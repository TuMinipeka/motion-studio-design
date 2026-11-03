"""Etapa 5 del modo edición: control de calidad del montaje y del último render (review/cortes.json).

    python qc.py                         montaje, cortes, palabras y el último render
    python qc.py --retranscribir         además transcribe el render y lo compara con el guion aprobado (WER)
    python qc.py --determinismo          además rehace un segmento y compara sus fotogramas con la caché

FALLA (código 1, bloqueante):
  montaje inválido · corte dentro de una palabra · corte con la voz sonando (se comería una sílaba) ·
  una palabra conservada del guion que no está en el montaje · render con otra duración que el montaje ·
  clic en un corte · WER > --wer-max (con --retranscribir) · segmento no determinista (con --determinismo) ·
  lo que falle en verificar.py (solo en el render final)
AVISO: una palabra quitada en el guion que vuelve a estar · silencio > 0,6 s en el render · dos clips seguidos de la
misma cámara con el mismo zoom y layout (el jump cut se notará)
Deja review/qc.json. Las medidas son del audio y de los tiempos; no juzgan si una toma es mejor ni si el ritmo engancha.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

import analizar
import editar
import montaje as mt

ROOT = os.path.dirname(os.path.abspath(__file__))
SILENCIO_MAX = 0.6


def palabras_norm(texto):
    return re.sub(r"[^\wáéíóúüñ ]", " ", texto.lower()).split()


def wer(ref, hip):
    d = np.arange(len(hip) + 1)
    for i, r in enumerate(ref, 1):
        prev, d[0] = d.copy(), i
        for j, h in enumerate(hip, 1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (r != h))
    return d[-1] / max(1, len(ref))


def audio_render(ruta, sr=48000):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", ruta, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, "<f4")


def clics(y, cortes, sr=48000):
    """Un clic es un salto entre muestras mucho mayor que los de alrededor justo en el corte."""
    malos = []
    d = np.abs(np.diff(y))
    for t in cortes:
        k = int(t * sr)
        cerca = d[max(0, k - int(0.02 * sr)): k + int(0.02 * sr)]
        contexto = np.r_[d[max(0, k - int(0.2 * sr)): max(0, k - int(0.03 * sr))], d[k + int(0.03 * sr): k + int(0.2 * sr)]]
        if len(cerca) and len(contexto) and cerca.max() > 0.05 and cerca.max() > 8 * (np.percentile(contexto, 99) + 1e-4):
            malos.append(round(t, 3))
    return malos


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--retranscribir", action="store_true")
    ap.add_argument("--determinismo", action="store_true")
    ap.add_argument("--wer-max", type=float, default=0.03)
    a = ap.parse_args()
    m = mt.cargar()
    fallos, avisos, ok = [], [], []
    check = lambda cond, bien, mal, bloq=True: ok.append(bien) if cond else (fallos if bloq else avisos).append(mal)

    errores = mt.validar(m)
    check(not errores, "montaje válido", "montaje inválido: " + "; ".join(errores))
    if errores:
        return informe(ok, avisos, fallos)
    voz = m["voz"]
    ps = mt.palabras(m, voz)
    fr_ruta = os.path.join(ROOT, "analisis", "frases.json")
    umbral = json.load(open(fr_ruta, encoding="utf-8"))["umbralDb"] if os.path.exists(fr_ruta) else None
    db = analizar.energia(analizar.leer_wav(m["fuentes"][voz]["wav"]))
    F = m["fuentes"]

    # bordes de cada clip en el reloj de la voz
    # (los cambios de layout sobre voz continua no son cortes de audio y no cuentan)
    bordes = []
    cs = m["clips"]
    for k, c in enumerate(cs):
        off = F[c["fuente"]].get("desfase", 0) - F[voz].get("desfase", 0)
        sigue_de = k > 0 and cs[k - 1]["fuente"] == c["fuente"] and abs(cs[k - 1]["a"] - c["de"]) < 0.002
        sigue_a = k + 1 < len(cs) and cs[k + 1]["fuente"] == c["fuente"] and abs(cs[k + 1]["de"] - c["a"]) < 0.002
        bordes += ([] if sigue_de else [(c["id"], "inicio", c["de"] - off)]) + ([] if sigue_a else [(c["id"], "fin", c["a"] - off)])
    dentro = [f"clip {i} ({lado} {t:.2f} s) corta «{p['t']}»" for i, lado, t in bordes for p in ps if p["de"] + 0.03 < t < p["a"] - 0.03]
    check(not dentro, "ningún corte dentro de una palabra", "cortes dentro de palabras: " + "; ".join(dentro[:8]))
    if umbral is not None:
        sonando = []
        for i, lado, t in bordes:
            k = int(t * 100)
            ventana = db[k - 2:k] if lado == "fin" else db[k:k + 2]
            if len(ventana) and ventana.mean() > umbral + 6:
                sonando.append(f"clip {i} ({lado} {t:.2f} s, {ventana.mean():.0f} dB)")
        check(not sonando, "ningún corte con la voz sonando", "cortes con la voz sonando (se come una sílaba o una respiración): " + "; ".join(sonando[:8]))

    g_ruta = os.path.join(ROOT, "analisis", "guion.json")
    if os.path.exists(g_ruta) and ps:
        g = json.load(open(g_ruta, encoding="utf-8"))
        # clips seguidos sin salto en la voz forman un tramo continuo: una palabra puede repartirse entre ellos
        tramos = []
        for c in m["clips"]:
            if c["fuente"] != voz:
                continue
            if tramos and abs(tramos[-1][1] - c["de"]) < 0.002:
                tramos[-1][1] = c["a"]
            else:
                tramos.append([c["de"], c["a"]])
        cubierta = lambda p: any(de - 0.02 <= p["de"] and p["a"] <= a_ + 0.02 for de, a_ in tramos)
        perdidas = [f"{k} «{ps[k]['t']}» ({ps[k]['de']:.2f} s)" for k in g["conservadas"] if not cubierta(ps[k])]
        check(not perdidas, f"las {len(g['conservadas'])} palabras del guion están en el montaje", "palabras del guion perdidas: " + "; ".join(perdidas[:10]))
        quitadas = {k for q in g["quitadas"] for k in range(*(lambda f: (f["palabras"][0], f["palabras"][1] + 1))(
            json.load(open(fr_ruta, encoding="utf-8"))["frases"][q["frase"]]))} if os.path.exists(fr_ruta) else set()
        vuelven = [f"«{ps[k]['t']}» ({ps[k]['de']:.2f} s)" for k in sorted(quitadas) if cubierta(ps[k]) and not ps[k].get("sinVoz")]
        check(not vuelven, "nada de lo quitado vuelve", "palabras quitadas en el guion que vuelven a estar: " + "; ".join(vuelven[:8]), bloq=False)

    iguales = [f"{x['id']}→{y['id']}" for x, y in zip(m["clips"], m["clips"][1:])
               if x["fuente"] == y["fuente"] and abs(x["a"] - y["de"]) > 0.05 and x.get("layout") == y.get("layout") == "completo"
               and x.get("zoom", 1) == y.get("zoom", 1)]
    check(not iguales, "los jump cuts cambian de zoom o de layout", "jump cuts sin cambio de zoom ni layout: " + ", ".join(iguales), bloq=False)

    # el último render
    cr = os.path.join(ROOT, "review", "cortes.json")
    if not os.path.exists(cr):
        avisos.append("no hay render que revisar (python editar.py)")
        return informe(ok, avisos, fallos)
    r = json.load(open(cr, encoding="utf-8"))
    ruta = os.path.join(ROOT, r["archivo"])
    if os.path.getmtime(ruta) < os.path.getmtime(mt.RUTA):
        avisos.append(f"{r['archivo']} es anterior al último cambio de montaje.json: vuelve a renderizar")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", ruta],
                               capture_output=True, text=True).stdout or 0)
    check(abs(dur - mt.duracion(m)) <= 1.5 / m["salida"]["fps"], f"render de {dur:.2f} s, como el montaje",
          f"el render dura {dur:.2f} s y el montaje {mt.duracion(m):.2f} s")
    y = audio_render(ruta)
    malos = clics(y, r["cortes"])
    check(not malos, f"sin clics en los {len(r['cortes'])} cortes", "clics en los cortes: " + ", ".join(f"{t} s" for t in malos))
    e = analizar.energia(y)
    umbral_r = max(float(np.percentile(e, 10)) + 12, float(np.percentile(e, 60)) - 25)
    quieto = np.r_[0, (e < umbral_r).astype(int), 0]
    cambios = np.flatnonzero(np.diff(quieto))
    largos = [(s / 100, t / 100) for s, t in zip(cambios[::2], cambios[1::2]) if (t - s) / 100 > SILENCIO_MAX and s > 0 and t < len(e)]
    pausas = m.get("curva", {}).get("pausas", [])
    largos = [x for x in largos if not any(p[0] <= x[0] and x[1] <= p[1] for p in pausas)]
    check(not largos, f"ningún silencio de más de {SILENCIO_MAX} s", "silencios largos en el render: " + ", ".join(f"{x:.1f}–{z:.1f} s" for x, z in largos), bloq=False)

    if a.retranscribir and os.path.exists(g_ruta) and ps:
        with tempfile.TemporaryDirectory() as d:
            wav = os.path.join(d, "render.wav")
            subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", ruta, "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", wav], check=True)
            analizar.ROOT = d   # transcribir() lee rutas relativas a ROOT
            t = analizar.transcribir("render.wav", m.get("idioma", "es"), analizar.perfil(), "")
            analizar.ROOT = ROOT
        ref = palabras_norm(" ".join(ps[k]["t"] for k in g["conservadas"]))
        hip = palabras_norm(" ".join(p["t"] for p in t["palabras"])) if t else []
        w = wer(ref, hip)
        check(t and w <= a.wer_max, f"retranscripción: WER {w:.1%}", f"retranscripción: WER {w:.1%} (máximo {a.wer_max:.0%}): falta o sobra texto")

    if a.determinismo and m["clips"]:
        c = m["clips"][0]
        final = r["modo"] == "final"
        s = m["salida"]
        W, H = (s["ancho"], s["alto"]) if final else editar.tam_revision(s)
        prf = editar.perfil()
        cod = s.get("codificador", "libx264") if final else (prf.get("codificadorRevision") or "libx264")
        args_cod = (s.get("parametros") or ["-preset", s.get("preset", "slow"), "-crf", str(s.get("crf", 18))]) if final and cod == "libx264" else editar.REVISION.get(cod, [])
        n = mt.cuadros(m, c["a"] - c["de"])
        cache = os.path.join(ROOT, "cache", r["modo"], editar.clave(m, c, W, H, n, cod, args_cod) + ".mp4")
        with tempfile.TemporaryDirectory() as d:
            otro = os.path.join(d, "s.mp4")
            subprocess.run(editar.segmento(m, c, W, H, n, cod, args_cod, otro), check=True, capture_output=True)
            md5 = lambda p: subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "framemd5", "-"], capture_output=True, text=True).stdout.split("\n")[-50:]
            check(os.path.exists(cache) and md5(cache) == md5(otro), "segmento determinista (fotogramas idénticos)",
                  "el segmento del clip 1 no es idéntico al rehacerlo (o no está en caché)")

    if r["modo"] == "final" and os.path.exists(os.path.join(ROOT, "verificar.py")):
        v = subprocess.run([sys.executable, os.path.join(ROOT, "verificar.py"), ruta], capture_output=True, text=True, encoding="utf-8")
        for linea in v.stdout.splitlines():
            if linea.strip().startswith("FALLA"):
                fallos.append("verificar: " + linea.strip()[5:].strip())
            elif linea.strip().startswith("AVISO"):
                avisos.append("verificar: " + linea.strip()[5:].strip())
        if v.returncode == 0:
            ok.append("verificar.py: exportación correcta")
    return informe(ok, avisos, fallos)


def informe(ok, avisos, fallos):
    for x in ok:
        print("  OK   ", x)
    for x in avisos:
        print("  AVISO", x)
    for x in fallos:
        print("  FALLA", x)
    os.makedirs(os.path.join(ROOT, "review"), exist_ok=True)
    json.dump({"ok": ok, "avisos": avisos, "fallos": fallos}, open(os.path.join(ROOT, "review", "qc.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("Resultado:", "FALLA" if fallos else "OK", "(review/qc.json)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
