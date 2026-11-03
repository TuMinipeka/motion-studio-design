"""Línea de tiempo del modo edición: montaje.json es la fuente de verdad y la IA la cambia con operaciones, no
reescribiendo el archivo ni tocando el video.

    python montaje.py validar                       esquema, solapes, fuentes existentes y tiempos; código 1 si falla
    python montaje.py info                          clips con su posición en el video final
    python montaje.py cortar --en 83.4              parte el clip que contiene ese instante del video final
    python montaje.py quitar --desde 83.4 --hasta 85.0   quita ese tramo del video final (ajustado a pausas entre palabras)
    python montaje.py quitar --palabras 412-419     quita esas palabras de palabras.json (índices de `info --palabras`)
    python montaje.py layout --desde 120 --hasta 148 pantalla+pip --pantalla pant1   (sincronizada; o pant1@12.0)
    python montaje.py zoom --clip 7 --escala 1.15 [--foco 0.5,0.35]
    python montaje.py transicion --clip 7 fundido|corte
    python montaje.py diff [vN]                     qué cambió frente a la versión anterior (o la vN)
    python montaje.py deshacer                      vuelve a la versión anterior

Modelo de tiempo. Todos los clips se anclan al reloj de su "fuente" (la cámara que habla): `de` y `a` son segundos de
esa fuente. El video final es la concatenación de los clips; su posición se calcula, no se guarda. Lo que se ve en un
clip lo decide `layout`:
  completo       la fuente a pantalla completa, con `zoom` y `foco` (centro del recorte, 0–1)
  pantalla       una grabación de pantalla (`pantalla`: {"fuente", "de"}) con la voz de la fuente
  pantalla+pip   la pantalla y la cámara en una esquina
Cada operación guarda antes la versión anterior en versiones/ para poder comparar o deshacer.
"""
import argparse
import copy
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(ROOT, "montaje.json")
VERSIONES = os.path.join(ROOT, "versiones")
LAYOUTS = {"completo", "pantalla", "pantalla+pip"}
TRANSICIONES = {"corte", "fundido"}
MIN_CLIP = 0.2          # un clip más corto que esto es un parpadeo, no un plano


def cargar(ruta=RUTA):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar(m, motivo):
    """Guarda montaje.json conservando la versión anterior en versiones/vNNN.json."""
    os.makedirs(VERSIONES, exist_ok=True)
    if os.path.exists(RUTA):
        n = len(glob.glob(os.path.join(VERSIONES, "v*.json"))) + 1
        previo = cargar()
        previo.setdefault("_meta", {})["guardado"] = motivo
        with open(os.path.join(VERSIONES, f"v{n:03d}.json"), "w", encoding="utf-8") as f:
            json.dump(previo, f, ensure_ascii=False, indent=1)
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)


def fps(m):
    return m["salida"]["fps"]


def cuadros(m, segundos):
    """Duración de un clip en fotogramas del video final: todo se redondea a fotograma para que audio e imagen cuadren."""
    return max(0, round(segundos * fps(m)))


def posiciones(m):
    """[(clip, inicio, fin)] en segundos del video final, alineados a fotograma."""
    out, t = [], 0
    for c in m["clips"]:
        n = cuadros(m, c["a"] - c["de"])
        out.append((c, t / fps(m), (t + n) / fps(m)))
        t += n
    return out


def duracion(m):
    return sum(cuadros(m, c["a"] - c["de"]) for c in m["clips"]) / fps(m)


def palabras(m, fuente=None):
    ruta = os.path.join(ROOT, "analisis", "palabras.json")
    if not os.path.exists(ruta):
        return []
    datos = json.load(open(ruta, encoding="utf-8"))
    fuente = fuente or m.get("voz")
    return datos.get(fuente, {}).get("palabras", []) if isinstance(datos, dict) else []


def validar(m):
    """Lista de errores (vacía si todo está bien). Lo que rompe el render o la sincronía es error."""
    e = []
    s = m.get("salida", {})
    for k in ("ancho", "alto", "fps"):
        if not isinstance(s.get(k), (int, float)) or s[k] <= 0:
            e.append(f"salida.{k} falta o no es válido (lo propone analizar.py a partir de las fuentes)")
    if s.get("ancho", 1) % 2 or s.get("alto", 1) % 2:
        e.append("salida.ancho y salida.alto deben ser pares (yuv420p)")
    fuentes = m.get("fuentes", {})
    for k, f in fuentes.items():
        if not os.path.exists(os.path.join(ROOT, f.get("normalizado") or f.get("archivo", ""))):
            e.append(f"fuente {k}: no existe {f.get('normalizado') or f.get('archivo')} (¿falta `python analizar.py`?)")
    if m.get("voz") not in fuentes:
        e.append(f"voz = {m.get('voz')!r} no es una fuente")
    if not m.get("clips"):
        e.append("no hay clips (¿falta `python planificar.py`?)")
    ids = set()
    for i, c in enumerate(m.get("clips", [])):
        nombre = f"clip {c.get('id', i)}"
        if c.get("id") in ids:
            e.append(f"{nombre}: id repetido")
        ids.add(c.get("id"))
        if c.get("fuente") not in fuentes:
            e.append(f"{nombre}: fuente {c.get('fuente')!r} desconocida")
            continue
        dur = fuentes[c["fuente"]].get("duracion")
        if not (0 <= c.get("de", -1) < c.get("a", -1)):
            e.append(f"{nombre}: de={c.get('de')} a={c.get('a')} no es un tramo válido")
        elif c["a"] - c["de"] < MIN_CLIP:
            e.append(f"{nombre}: dura {c['a'] - c['de']:.2f} s (mínimo {MIN_CLIP} s)")
        if dur and c.get("a", 0) > dur + 1e-3:
            e.append(f"{nombre}: termina en {c['a']:.2f} s pero la fuente dura {dur:.2f} s")
        if c.get("layout", "completo") not in LAYOUTS:
            e.append(f"{nombre}: layout {c.get('layout')!r} desconocido ({', '.join(sorted(LAYOUTS))})")
        if c.get("layout", "completo") != "completo":
            p = c.get("pantalla") or {}
            if p.get("fuente") not in fuentes:
                e.append(f"{nombre}: layout {c['layout']} sin pantalla.fuente válida")
            else:
                fin = p.get("de", 0) + (c["a"] - c["de"])
                dp = fuentes[p["fuente"]].get("duracion")
                if p.get("de", -1) < 0 or (dp and fin > dp + 1e-3):
                    e.append(f"{nombre}: la pantalla {p['fuente']} no cubre {p.get('de')}–{fin:.2f} s (dura {dp})")
        if not 1 <= c.get("zoom", 1) <= 3:
            e.append(f"{nombre}: zoom {c.get('zoom')} fuera de 1–3")
        fx, fy = c.get("foco", [0.5, 0.4])
        if not (0 <= fx <= 1 and 0 <= fy <= 1):
            e.append(f"{nombre}: foco fuera de 0–1")
        if c.get("transicion", "corte") not in TRANSICIONES:
            e.append(f"{nombre}: transición {c.get('transicion')!r} desconocida ({', '.join(sorted(TRANSICIONES))})")
    # dos clips que muestran el mismo tramo de la fuente repetirían frases
    por_fuente = {}
    for c in m.get("clips", []):
        por_fuente.setdefault(c.get("fuente"), []).append(c)
    for f, cs in por_fuente.items():
        cs = sorted(cs, key=lambda c: c.get("de", 0))
        for x, y in zip(cs, cs[1:]):
            if y.get("de", 0) < x.get("a", 0) - 1e-3:
                e.append(f"clips {x.get('id')} y {y.get('id')} repiten {y['de']:.2f}–{min(x['a'], y['a']):.2f} s de {f}")
    return e


def nuevo_id(m):
    return max((c["id"] for c in m["clips"]), default=0) + 1


def ajustar(m, fuente, t, ventana=0.3):
    """Mueve un instante de la fuente al centro de la pausa entre palabras más cercana, para no cortar dentro de una
    palabra. Sin transcripción (nivel núcleo) lo deja igual."""
    ps = palabras(m, fuente)
    dentro = next((p for p in ps if p["de"] < t < p["a"]), None)
    if not dentro:
        return t
    huecos = [(a["a"] + b["de"]) / 2 for a, b in zip(ps, ps[1:]) if b["de"] >= a["a"]]
    cerca = min(huecos, key=lambda h: abs(h - t), default=t)
    return cerca if abs(cerca - t) <= ventana + (dentro["a"] - dentro["de"]) else t


def a_fuente(m, t):
    """Instante del video final -> (índice del clip, segundo de su fuente)."""
    for i, (c, ini, fin) in enumerate(posiciones(m)):
        if ini <= t < fin or (i == len(m["clips"]) - 1 and abs(t - fin) < 1e-6):
            return i, c["de"] + (t - ini)
    raise SystemExit(f"{t} s está fuera del video ({duracion(m):.2f} s)")


def partir(m, i, ts):
    """Parte el clip i en el segundo ts de su fuente; devuelve el índice del segundo trozo."""
    c = m["clips"][i]
    # el punto de corte cae en un fotograma del clip: así el trozo siguiente empieza justo donde acaba el anterior
    ts = c["de"] + round((ts - c["de"]) * fps(m)) / fps(m)
    # un corte a menos de MIN_CLIP de un borde se lleva a ese borde: no se crean parpadeos
    if ts - c["de"] < MIN_CLIP:
        return i
    if c["a"] - ts < MIN_CLIP:
        return i + 1
    b = copy.deepcopy(c)
    c["a"], b["de"], b["id"] = ts, ts, nuevo_id(m)
    if b.get("pantalla"):
        b["pantalla"]["de"] = round(c["pantalla"]["de"] + (ts - c["de"]), 4)
    b["transicion"] = "corte"
    m["clips"].insert(i + 1, b)
    return i + 1


def quitar_fuente(m, fuente, de, a, motivo):
    """Quita [de, a] (segundos de la fuente) de todos los clips de esa fuente."""
    # lo quitado puede ser corto (una palabra); lo que queda a cada lado, no: un resto menor que MIN_CLIP se va también
    for i in reversed(range(len(m["clips"]))):
        c = m["clips"][i]
        if c["fuente"] != fuente or c["a"] <= de or c["de"] >= a:
            continue
        piezas = []
        if de - c["de"] >= MIN_CLIP:
            antes = copy.deepcopy(c)
            antes["a"] = round(c["de"] + round((de - c["de"]) * fps(m)) / fps(m), 4)
            piezas.append(antes)
        if c["a"] - a >= MIN_CLIP:
            despues = copy.deepcopy(c)
            despues["de"], despues["transicion"] = round(a, 4), "corte"
            if despues.get("pantalla"):
                despues["pantalla"]["de"] = round(c["pantalla"]["de"] + (a - c["de"]), 4)
            if piezas:
                despues["id"] = nuevo_id(m)
            piezas.append(despues)
        m["clips"][i:i + 1] = piezas
    m.setdefault("registro", []).append({"op": "quitar", "fuente": fuente, "de": round(de, 3), "a": round(a, 3), "motivo": motivo})


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="op", required=True)
    sub.add_parser("validar")
    i = sub.add_parser("info"); i.add_argument("--palabras", action="store_true", help="lista las palabras con su índice y si se conservan")
    c = sub.add_parser("cortar"); c.add_argument("--en", type=float, required=True); c.add_argument("--exacto", action="store_true")
    q = sub.add_parser("quitar"); q.add_argument("--desde", type=float); q.add_argument("--hasta", type=float)
    q.add_argument("--palabras", help="rango de índices, p. ej. 412-419"); q.add_argument("--motivo", default="indicado por el agente")
    q.add_argument("--exacto", action="store_true", help="no ajustar a la pausa entre palabras")
    lay = sub.add_parser("layout"); lay.add_argument("tipo", choices=sorted(LAYOUTS)); lay.add_argument("--desde", type=float, required=True)
    lay.add_argument("--hasta", type=float, required=True); lay.add_argument("--pantalla", help="fuente[@segundo], p. ej. pant1 o pant1@12.0")
    lay.add_argument("--exacto", action="store_true", help="no llevar los bordes a la pausa entre palabras más cercana")
    z = sub.add_parser("zoom"); z.add_argument("--clip", type=int, required=True); z.add_argument("--escala", type=float, required=True)
    z.add_argument("--foco", help="x,y entre 0 y 1")
    tr = sub.add_parser("transicion"); tr.add_argument("tipo", choices=sorted(TRANSICIONES)); tr.add_argument("--clip", type=int, required=True)
    d = sub.add_parser("diff"); d.add_argument("version", nargs="?")
    sub.add_parser("deshacer")
    a = ap.parse_args()
    m = cargar()

    if a.op == "validar":
        errores = validar(m)
        for x in errores:
            print("ERROR:", x)
        print("OK: montaje válido" if not errores else f"{len(errores)} errores")
        print(f"{len(m.get('clips', []))} clips · {duracion(m) if m.get('clips') and m.get('salida', {}).get('fps') else 0:.2f} s")
        return 1 if errores else 0

    if a.op == "info":
        for c, ini, fin in posiciones(m):
            extra = f" pantalla={c['pantalla']['fuente']}@{c['pantalla']['de']:.2f}" if c.get("pantalla") else ""
            print(f"clip {c['id']:3d}  {ini:7.2f}–{fin:7.2f} s  ← {c['fuente']} {c['de']:7.2f}–{c['a']:7.2f}  {c.get('layout', 'completo'):12} "
                  f"zoom {c.get('zoom', 1):.2f}{extra}")
        if a.palabras:
            dentro = lambda p: any(c["fuente"] == m["voz"] and c["de"] <= p["de"] and p["a"] <= c["a"] for c in m["clips"])
            for k, p in enumerate(palabras(m)):
                print(f"{k:5d} {p['de']:8.2f} {'  ' if dentro(p) else '✗ '}{p['t']}")
        print(f"total {duracion(m):.2f} s")
        return 0

    if a.op == "diff":
        vs = sorted(glob.glob(os.path.join(VERSIONES, "v*.json")))
        if not vs:
            print("No hay versiones anteriores."); return 0
        previo = cargar(os.path.join(VERSIONES, a.version + ".json") if a.version else vs[-1])
        antes = {c["id"]: c for c in previo["clips"]}
        ahora = {c["id"]: c for c in m["clips"]}
        for k in sorted(set(antes) | set(ahora)):
            x, y = antes.get(k), ahora.get(k)
            if x != y:
                print(("+ " if not x else "- " if not y else "~ ") + f"clip {k}: "
                      + (json.dumps(y, ensure_ascii=False) if y else json.dumps(x, ensure_ascii=False)))
        print(f"duración {duracion(previo):.2f} s -> {duracion(m):.2f} s")
        return 0

    if a.op == "deshacer":
        vs = sorted(glob.glob(os.path.join(VERSIONES, "v*.json")))
        if not vs:
            print("No hay nada que deshacer."); return 1
        previo = cargar(vs[-1]); previo.pop("_meta", None)
        with open(RUTA, "w", encoding="utf-8") as f:
            json.dump(previo, f, ensure_ascii=False, indent=1)
        os.remove(vs[-1])
        print(f"Restaurada {os.path.basename(vs[-1])}"); return 0

    if a.op == "cortar":
        i, ts = a_fuente(m, a.en)
        ts = ts if a.exacto else ajustar(m, m["clips"][i]["fuente"], ts)
        partir(m, i, ts)
    elif a.op == "quitar":
        if a.palabras:
            ps = palabras(m)
            x, _, y = a.palabras.partition("-")
            x, y = int(x), int(y or x)
            if not 0 <= x <= y < len(ps):
                raise SystemExit(f"rango de palabras fuera de 0–{len(ps) - 1}")
            # del final de la palabra anterior al principio de la siguiente: no queda media respiración
            de = (ps[x - 1]["a"] + ps[x]["de"]) / 2 if x > 0 else ps[x]["de"] - 0.05
            hasta = (ps[y]["a"] + ps[y + 1]["de"]) / 2 if y + 1 < len(ps) else ps[y]["a"] + 0.1
            quitar_fuente(m, m["voz"], de, hasta, a.motivo + f" (palabras {x}-{y})")
        else:
            if a.desde is None or a.hasta is None or a.hasta <= a.desde:
                raise SystemExit("indica --desde y --hasta (segundos del video final) o --palabras")
            i, de = a_fuente(m, a.desde)
            j, hasta = a_fuente(m, min(a.hasta, duracion(m) - 1e-6))
            if i != j:
                raise SystemExit("el tramo cruza clips: quítalo por partes o con --palabras")
            f = m["clips"][i]["fuente"]
            if not a.exacto:
                de, hasta = ajustar(m, f, de), ajustar(m, f, hasta)
            quitar_fuente(m, f, de, hasta, a.motivo)
    elif a.op == "layout":
        # el cambio de imagen cae entre dos palabras salvo --exacto: cambiar de plano a mitad de palabra se nota
        i, de = a_fuente(m, a.desde)
        ini_i = partir(m, i, de if a.exacto else ajustar(m, m["clips"][i]["fuente"], de))   # primer clip afectado
        j, hasta = a_fuente(m, min(a.hasta, duracion(m) - 1e-6))
        fin_j = partir(m, j, hasta if a.exacto else ajustar(m, m["clips"][j]["fuente"], hasta)) - 1   # último clip afectado
        fuente_p, _, t0 = (a.pantalla or "").partition("@")
        t = float(t0) if t0 else None
        F = m["fuentes"]
        for c in m["clips"][ini_i:fin_j + 1]:
            c["layout"] = a.tipo
            if a.tipo == "completo":
                c.pop("pantalla", None)
            else:
                if fuente_p not in F:
                    raise SystemExit("layout con pantalla necesita --pantalla fuente[@segundo]")
                # sin @segundo: lo que se grabó en la pantalla en ese mismo momento (por el desfase medido)
                de = t if t is not None else c["de"] - F[c["fuente"]].get("desfase", 0) + F[fuente_p].get("desfase", 0)
                c["pantalla"] = {"fuente": fuente_p, "de": round(de, 4)}
                if t is not None:
                    t += c["a"] - c["de"]
    elif a.op == "zoom":
        c = next((c for c in m["clips"] if c["id"] == a.clip), None) or sys.exit(f"no hay clip {a.clip}")
        c["zoom"] = a.escala
        if a.foco:
            c["foco"] = [float(v) for v in a.foco.split(",")]
    elif a.op == "transicion":
        c = next((c for c in m["clips"] if c["id"] == a.clip), None) or sys.exit(f"no hay clip {a.clip}")
        c["transicion"] = a.tipo

    errores = validar(m)
    if errores:
        for x in errores:
            print("ERROR:", x)
        print("No se guardó: la operación deja el montaje inválido.")
        return 1
    guardar(m, " ".join(sys.argv[1:]))
    print(f"OK ({a.op}) · {len(m['clips'])} clips · {duracion(m):.2f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
