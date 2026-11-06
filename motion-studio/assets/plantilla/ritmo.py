"""Ritmo: ¿se mueve el video lo suficiente, y se sostiene hasta el final? Mide movimiento, tramos muertos, cortes y la
curva de energía por tramos; una hoja de contacto no lo muestra.

    python ritmo.py                          revisa review/ritmo/vista.mp4 (node render.mjs --ritmo) o el borrador
    python ritmo.py video.mp4                revisa cualquier video
    python ritmo.py --referencia a.mp4 b.mp4 [--calibrar]
                                             mide videos de referencia; con --calibrar escribe sus umbrales en motion.config.json

Método: 10 fps, 48 px de ancho y escala de grises (así el grano o el ruido fino no cuentan como movimiento).
Movimiento de un segundo = diferencia media entre fotogramas consecutivos, de 0 a 255. Por debajo de `umbralMicro` solo
hay micromovimiento (respiración, deriva lenta de cámara): para quien mira, la imagen está quieta.

Falla (código 1) si, según motion.config.json -> "ritmo":
- la racha muerta más larga o el porcentaje de micromovimiento superan los umbrales;
- la curva de energía decae: un tramo (15 s, o una cuarta parte en piezas de menos de 60 s) cae por debajo de
  `caidaMin` veces el movimiento de la apertura y pasa al menos `caidaQuieto` % de su tiempo quieto, o dos tramos seguidos pasan de `tramoQuietoMax` % de tiempo quieto.
  Una media global esconde esa caída: un gancho fuerte compensa en el promedio un centro muerto.
Las pausas declaradas en motion.config.json -> "curva" -> "pausas" no cuentan como tramo muerto ni como caída.
Avisa (sin fallar) si la duración media de plano es larga, si un re-gancho planificado en "curva" -> "reganches" no se
ve en el video, si hay demasiado tiempo entre re-ganchos y, cuando el video tiene sonido, si la densidad de golpes
sonoros o el nivel caen respecto a la apertura o si el estéreo es estrecho y no cambia.
Mide también la saturación y la luminancia por tramo (el guion de color real). Si el proyecto declara un guion de color
en motion.config.json -> "curva" -> "color" = [[t0, t1, satMin, satMax, "motivo"], ...] (saturación en %), avisa de los
tramos que se salen; no falla por color.
Necesita numpy y ffmpeg.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
FPS, ANCHO = 10, 48
DEFECTO = {"umbralMicro": 1.5, "rachaMuertaMax": 4, "microMax": 40, "planoMedioMax": 5,
           "tramo": None, "caidaMin": 0.5, "caidaQuieto": 30, "tramoQuietoMax": 50, "reganchoMax": None}


def config():
    try:
        cfg = json.load(open(os.path.join(ROOT, "motion.config.json"), encoding="utf-8"))
    except OSError:
        cfg = {}
    return cfg, {**DEFECTO, **cfg.get("ritmo", {})}


def medir(ruta, umbral):
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", ruta],
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"No puedo leer {ruta}: {p.stderr.strip()}")
    w, h = map(int, p.stdout.strip().split(",")[:2])
    alto = max(2, int(round(ANCHO * h / w / 2) * 2))
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-vf", f"fps={FPS},scale={ANCHO}:{alto}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True)
    f = np.frombuffer(r.stdout, np.uint8).reshape(-1, alto, ANCHO).astype(np.float32)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    seg = d[: len(d) // FPS * FPS].reshape(-1, FPS).mean(1)
    lento = seg < umbral
    tramos, ini = [], None
    for i, v in enumerate(list(lento) + [False]):
        if v and ini is None:
            ini = i
        elif not v and ini is not None:
            tramos.append((ini, i)); ini = None
    corte = max(18.0, 6 * float(np.median(d)))
    es_corte = (d > corte) & np.r_[True, d[:-1] <= corte]
    cortes = int(np.sum(es_corte))
    dur = len(f) / FPS
    return {"nombre": os.path.basename(ruta), "dur": dur, "seg": seg, "mediana": float(np.median(seg)) if len(seg) else 0.0,
            "micro": float(lento.mean() * 100) if len(seg) else 0.0, "racha": max((b - a for a, b in tramos), default=0),
            "tramos": tramos, "cortesMin": cortes / dur * 60 if dur else 0.0, "plano": dur / (cortes + 1),
            "tCortes": (np.nonzero(es_corte)[0] + 1) / FPS}


def medir_audio(ruta):
    """Golpes sonoros (ataques de energía cada 10 ms), nivel y ancho estéreo. None si el video no tiene sonido."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-vn", "-f", "f32le", "-ac", "2", "-ar", "16000", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, "<f4")
    if r.returncode or len(x) < 32000:
        return None
    x = x[: len(x) // 2 * 2].reshape(-1, 2)
    sr, hop = 16000, 160
    m = x.mean(1)
    e = (m[: len(m) // hop * hop].reshape(-1, hop) ** 2).sum(1)
    flujo = np.maximum(0, np.diff(np.log(e + 1e-9)))
    golpe = (flujo > 2.0) & np.r_[True, flujo[:-1] <= 2.0]
    return {"x": x, "sr": sr, "golpes": (np.nonzero(golpe)[0] + 1) * hop / sr}


def medir_color(ruta):
    """Saturación (0–100 %) y luminancia (0–255) medias cada 0,5 s: el guion de color medido, no supuesto."""
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", ruta],
                       capture_output=True, text=True)
    w, h = map(int, p.stdout.strip().split(",")[:2])
    alto = max(2, int(round(ANCHO * h / w / 2) * 2))
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-vf", f"fps=2,scale={ANCHO}:{alto}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True)
    f = np.frombuffer(r.stdout, np.uint8).reshape(-1, alto, ANCHO, 3).astype(np.float32)
    mx, mn = f.max(axis=3), f.min(axis=3)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0).mean(axis=(1, 2)) * 100
    lum = (f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114).mean(axis=(1, 2))
    return {"t": np.arange(len(f)) / 2.0, "sat": sat, "lum": lum}


def tramos_de(n, tramo):
    """Ventanas de `tramo` segundos sobre n segundos; un resto corto se une al último tramo."""
    bordes = list(range(0, n, tramo)) + [n]
    if len(bordes) > 2 and bordes[-1] - bordes[-2] < tramo / 2:
        bordes.pop(-2)
    return list(zip(bordes[:-1], bordes[1:]))


def en_pausa(a, b, pausas):
    return sum(max(0, min(b, q1) - max(a, q0)) for q0, q1, *_ in pausas) >= 0.5 * (b - a)


def curva(m, u, pausas, audio=None):
    """Mide cada tramo y compara con la apertura (el primer tramo)."""
    n = len(m["seg"])
    tramo = int(u["tramo"] or (15 if m["dur"] >= 60 else max(5, round(m["dur"] / 4))))
    filas = []
    for a, b in tramos_de(n, tramo):
        s = m["seg"][a:b]
        f = {"a": a, "b": b, "mov": float(np.median(s)), "quieto": float((s < u["umbralMicro"]).mean() * 100),
             "pausa": en_pausa(a, b, pausas)}
        if audio:
            x, sr = audio["x"][int(a * audio["sr"]): int(b * audio["sr"])], audio["sr"]
            mid, side = x.mean(1), (x[:, 0] - x[:, 1]) / 2
            f["golpes"] = float(((audio["golpes"] >= a) & (audio["golpes"] < b)).sum() / (b - a))
            f["db"] = float(20 * np.log10(np.sqrt((mid ** 2).mean()) + 1e-9))
            f["ancho"] = float(np.sqrt((side ** 2).mean()) / (np.sqrt((mid ** 2).mean()) + 1e-9))
        filas.append(f)
    return tramo, filas


def caida_minima(filas):
    """Peor tramo frente a la apertura (sin contar pausas): la medida que se calibra con referencias."""
    if len(filas) < 2 or filas[0]["mov"] <= 0:
        return 1.0
    return min((f["mov"] / filas[0]["mov"] for f in filas[1:] if not f["pausa"]), default=1.0)


def fila(m):
    return (f"{m['nombre'][:34]:34} {m['dur']:6.1f}s {m['mediana']:7.2f} {m['micro']:7.0f}% {m['racha']:6d}s "
            f"{m['cortesMin']:9.1f} {m['plano']:6.1f}s")


CABECERA = f"{'video':34} {'dur':>7} {'mediana':>7} {'micro':>8} {'racha':>7} {'cortes/min':>9} {'plano':>7}"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # consola de Windows: los símbolos de la línea de tiempo
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("videos", nargs="*")
    ap.add_argument("--referencia", nargs="+", help="videos de referencia del estilo buscado")
    ap.add_argument("--calibrar", action="store_true", help="con --referencia: guarda en motion.config.json umbrales derivados de ellos")
    a = ap.parse_args()
    cfg, u = config()
    plan = cfg.get("curva", {})
    pausas = [p for p in plan.get("pausas", []) if len(p) >= 2]
    reganches = sorted(float(t) for t in plan.get("reganches", []))

    if a.referencia:
        refs = [medir(r, u["umbralMicro"]) for r in a.referencia]
        print(CABECERA); [print(fila(m)) for m in refs]
        curvas = [curva(m, u, [])[1] for m in refs]
        # umbrales = percentil 75 de las referencias con un pequeño margen: el estilo típico, sin que la referencia más
        # lenta (un caso aislado) abra la puerta a tramos muertos que el resto nunca tiene. Para la caída, que es un
        # mínimo, el mismo criterio es el percentil 25 del peor tramo de cada referencia.
        p75 = lambda k: float(np.percentile([m[k] for m in refs], 75))
        nuevo = {"umbralMicro": u["umbralMicro"], "rachaMuertaMax": int(np.ceil(p75("racha"))) + 1,
                 "microMax": int(round(p75("micro") + 5)), "planoMedioMax": round(p75("plano") + 0.5, 1),
                 "caidaMin": round(float(np.clip(np.percentile([caida_minima(c) for c in curvas], 25) * 0.9, 0.3, 0.8)), 2),
                 "tramoQuietoMax": int(round(float(np.percentile([max(f["quieto"] for f in c) for c in curvas], 75)) + 5))}
        print(f"\nUmbrales derivados de las referencias: {nuevo}")
        if a.calibrar:
            cfg["ritmo"] = {**cfg.get("ritmo", {}), **nuevo}
            json.dump(cfg, open(os.path.join(ROOT, "motion.config.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print("Guardados en motion.config.json -> ritmo")
        if not a.videos:
            return 0
        u = {**u, **(nuevo if a.calibrar else {})}

    videos, propio = a.videos, not a.videos
    if not videos:
        nombre = cfg.get("salida", {}).get("nombre", "video")
        for c in [os.path.join(ROOT, "review", "ritmo", "vista.mp4"),
                  os.path.join(ROOT, cfg.get("salida", {}).get("carpeta", "exportaciones"), f"{nombre}_borrador.mp4")]:
            if os.path.exists(c):
                videos = [c]; break
        else:
            sys.exit("No hay video que revisar: ejecuta antes `node render.mjs --ritmo` o pasa la ruta de un video.")
    # la curva planificada es del proyecto: se aplica a sus propios videos, no a una referencia externa
    propio = propio or all(os.path.abspath(v).startswith(ROOT + os.sep) for v in videos)

    fallo = False
    for ruta in videos:
        m = medir(ruta, u["umbralMicro"])
        audio = medir_audio(ruta)
        pz = pausas if propio else []
        print(CABECERA); print(fila(m))
        marcas = "".join("·" if v < u["umbralMicro"] else ("▮" if v > 4 * u["umbralMicro"] else "▪") for v in m["seg"])
        print("\npor segundo (· quieto, ▪ algo de movimiento, ▮ mucho):")
        for i in range(0, len(marcas), 60):
            print(f"  {i:4d}s {marcas[i:i + 60]}")

        tramo, filas = curva(m, u, pz, audio)
        color = medir_color(ruta)
        for f in filas:
            sel = (color["t"] >= f["a"]) & (color["t"] < f["b"])
            f["sat"] = float(color["sat"][sel].mean()) if sel.any() else 0.0
            f["lum"] = float(color["lum"][sel].mean()) if sel.any() else 0.0
        base = filas[0]
        print(f"\ncurva de energía por tramos de {tramo} s (la apertura es la referencia):")
        print(f"  {'tramo':>9} {'mov':>6} {'vs ap.':>7} {'quieto':>7}" + (f" {'golpes/s':>9} {'dB':>6} {'ancho':>6}" if audio else "")
              + f" {'sat':>5} {'lum':>5}")
        for f in filas:
            rel = f["mov"] / base["mov"] if base["mov"] > 0 else 1.0
            linea = f"  {f['a']:4d}-{f['b']:<4d} {f['mov']:6.2f} {rel:6.0%} {f['quieto']:6.0f}%"
            if audio:
                linea += f" {f['golpes']:9.2f} {f['db']:6.1f} {f['ancho']:6.2f}"
            linea += f" {f['sat']:4.0f}% {f['lum']:5.0f}"
            print(linea + ("  pausa declarada" if f["pausa"] else ""))

        problemas, avisos = [], []
        muertos = [(x, y) for x, y in m["tramos"] if y - x > u["rachaMuertaMax"] and not en_pausa(x, y, pz)]
        if muertos:
            problemas.append("tramos muertos de más de %d s: %s" % (u["rachaMuertaMax"], ", ".join(f"{x}–{y} s" for x, y in muertos)))
        if m["micro"] > u["microMax"]:
            problemas.append(f"{m['micro']:.0f} % del tiempo con solo micromovimiento (máximo {u['microMax']} %)")
        # caer = moverse mucho menos que la apertura Y pasar parte del tramo quieto: un cierre más calmado que sigue
        # moviéndose no es una caída
        caen = [f for f in filas[1:] if not f["pausa"] and base["mov"] > 0 and f["mov"] < u["caidaMin"] * base["mov"]
                and f["quieto"] >= u["caidaQuieto"]]
        if caen:
            problemas.append(f"la energía decae por debajo del {u['caidaMin']:.0%} de la apertura, con al menos un {u['caidaQuieto']} % de tiempo quieto, en "
                             + ", ".join(f"{f['a']}–{f['b']} s ({f['mov'] / base['mov']:.0%})" for f in caen))
        quietos = [(x, y) for x, y in zip(filas, filas[1:])
                   if not x["pausa"] and not y["pausa"] and min(x["quieto"], y["quieto"]) > u["tramoQuietoMax"]]
        if quietos:
            problemas.append(f"tramos seguidos con más del {u['tramoQuietoMax']} % de tiempo quieto: "
                             + ", ".join(f"{x['a']}–{y['b']} s" for x, y in quietos))

        if m["plano"] > u["planoMedioMax"]:
            avisos.append(f"plano medio de {m['plano']:.1f} s (referencia: hasta {u['planoMedioMax']} s); ¿falta cambiar de escala o de ángulo?")
        if propio:
            maximo = u["reganchoMax"] or (25 if m["dur"] >= 60 else 12)
            if not reganches and m["dur"] > 20:
                avisos.append("no hay curva planificada (motion.config.json -> curva -> reganches): planifica los re-ganchos en el storyboard")
            for t in reganches:
                cerca = m["seg"][max(0, int(t) - 1): int(t) + 2]
                hay_corte = np.any((m["tCortes"] >= t - 1) & (m["tCortes"] <= t + 1.5))
                if t < m["dur"] and not hay_corte and (not len(cerca) or cerca.max() < 4 * u["umbralMicro"]):
                    avisos.append(f"el re-gancho planificado en {t:g} s no se ve: ni corte ni movimiento fuerte en ese momento")
            puntos = [0.0] + [t for t in reganches if t < m["dur"]] + [m["dur"]]
            huecos = [(x, y) for x, y in zip(puntos, puntos[1:]) if y - x > maximo and not en_pausa(x, y, pz)]
            if reganches and huecos:
                avisos.append(f"más de {maximo} s sin re-gancho: " + ", ".join(f"{x:g}–{y:g} s" for x, y in huecos))
            # guion de color declarado: [[t0, t1, satMin, satMax, motivo?], ...] en %. Solo avisa: el color es una decisión.
            for tramo_color in plan.get("color", []):
                if len(tramo_color) < 4:
                    continue
                c0, c1, smin, smax = (float(v) for v in tramo_color[:4])
                sel = (color["t"] >= c0) & (color["t"] < c1)
                if sel.any():
                    s = float(color["sat"][sel].mean())
                    if not smin <= s <= smax:
                        avisos.append(f"guion de color {c0:g}–{c1:g} s: saturación media {s:.0f} %, fuera de lo planeado ({smin:g}–{smax:g} %)")
        if audio:
            flojos = [f for f in filas[1:] if not f["pausa"] and base["golpes"] > 0 and f["golpes"] < 0.6 * base["golpes"]]
            if flojos:
                avisos.append("el sonido pierde densidad frente a la apertura (menos del 60 % de sus golpes/s) en "
                              + ", ".join(f"{f['a']}–{f['b']} s" for f in flojos))
            bajos = [f for f in filas[1:] if not f["pausa"] and f["db"] < base["db"] - 4]
            if bajos:
                avisos.append("el nivel cae más de 4 dB respecto a la apertura en " + ", ".join(f"{f['a']}–{f['b']} s" for f in bajos))
            anchos = [f["ancho"] for f in filas]
            if max(anchos) < 0.3:
                avisos.append(f"estéreo estrecho en toda la pieza (ancho máximo {max(anchos):.2f}): panea los efectos según la posición en pantalla"
                              " y abre la mezcla en los momentos clave")

        for p in problemas:
            print("FALLA:", p)
        for p in avisos:
            print("AVISO:", p)
        if problemas:
            fallo = True
            print("Arreglo: no lo tapes con efectos de relleno. En los tramos muertos, cambia de escala o ángulo cada 2–4 s,"
                  " haz que el personaje actúe (no solo respire), agranda la acción principal y muestra un indicador que cambie."
                  " Si la energía decae, vuelve al storyboard: pon un re-gancho ligado al contenido (giro, pregunta nueva,"
                  " cambio de lugar o de escala) y reutiliza los recursos de la apertura en el clímax de ese tramo."
                  " Una caída intencionada se declara en motion.config.json -> curva -> pausas con su motivo.")
        else:
            print("OK: ritmo y curva de energía dentro de los umbrales.")
    return 1 if fallo else 0


if __name__ == "__main__":
    sys.exit(main())
