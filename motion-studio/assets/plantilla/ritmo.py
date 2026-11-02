"""Ritmo: ¿se mueve el video lo suficiente? Mide movimiento, tramos muertos y cortes; una hoja de contacto no lo muestra.

    python ritmo.py                          revisa review/ritmo/vista.mp4 (node render.mjs --ritmo) o el borrador
    python ritmo.py video.mp4                revisa cualquier video
    python ritmo.py --referencia a.mp4 b.mp4 [--calibrar]
                                             mide videos de referencia; con --calibrar escribe sus umbrales en motion.config.json

Método: 10 fps, 48 px de ancho y escala de grises (así el grano o el ruido fino no cuentan como movimiento).
Movimiento de un segundo = diferencia media entre fotogramas consecutivos, de 0 a 255. Por debajo de `umbralMicro` solo
hay micromovimiento (respiración, deriva lenta de cámara): para quien mira, la imagen está quieta.
Falla (código 1) si la racha muerta más larga o el porcentaje de micromovimiento superan los umbrales de
motion.config.json -> "ritmo". La duración media de plano solo avisa: hay estilos de plano largo que funcionan.
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
DEFECTO = {"umbralMicro": 1.5, "rachaMuertaMax": 4, "microMax": 40, "planoMedioMax": 5}


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
    cortes = int(np.sum((d > corte) & np.r_[True, d[:-1] <= corte]))
    dur = len(f) / FPS
    return {"nombre": os.path.basename(ruta), "dur": dur, "seg": seg, "mediana": float(np.median(seg)) if len(seg) else 0.0,
            "micro": float(lento.mean() * 100) if len(seg) else 0.0, "racha": max((b - a for a, b in tramos), default=0),
            "tramos": tramos, "cortesMin": cortes / dur * 60 if dur else 0.0, "plano": dur / (cortes + 1)}


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

    if a.referencia:
        refs = [medir(r, u["umbralMicro"]) for r in a.referencia]
        print(CABECERA); [print(fila(m)) for m in refs]
        # umbrales = percentil 75 de las referencias con un pequeño margen: el estilo típico, sin que la referencia más
        # lenta (un caso aislado) abra la puerta a tramos muertos que el resto nunca tiene
        p75 = lambda k: float(np.percentile([m[k] for m in refs], 75))
        nuevo = {"umbralMicro": u["umbralMicro"], "rachaMuertaMax": int(np.ceil(p75("racha"))) + 1,
                 "microMax": int(round(p75("micro") + 5)), "planoMedioMax": round(p75("plano") + 0.5, 1)}
        print(f"\nUmbrales derivados de las referencias: {nuevo}")
        if a.calibrar:
            cfg["ritmo"] = nuevo
            json.dump(cfg, open(os.path.join(ROOT, "motion.config.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print("Guardados en motion.config.json -> ritmo")
        if not a.videos:
            return 0
        u = {**u, **(nuevo if a.calibrar else {})}

    videos = a.videos
    if not videos:
        nombre = cfg.get("salida", {}).get("nombre", "video")
        for c in [os.path.join(ROOT, "review", "ritmo", "vista.mp4"),
                  os.path.join(ROOT, cfg.get("salida", {}).get("carpeta", "exportaciones"), f"{nombre}_borrador.mp4")]:
            if os.path.exists(c):
                videos = [c]; break
        else:
            sys.exit("No hay video que revisar: ejecuta antes `node render.mjs --ritmo` o pasa la ruta de un video.")

    fallo = False
    for ruta in videos:
        m = medir(ruta, u["umbralMicro"])
        print(CABECERA); print(fila(m))
        marcas = "".join("·" if v < u["umbralMicro"] else ("▮" if v > 4 * u["umbralMicro"] else "▪") for v in m["seg"])
        print("\npor segundo (· quieto, ▪ algo de movimiento, ▮ mucho):")
        for i in range(0, len(marcas), 60):
            print(f"  {i:4d}s {marcas[i:i + 60]}")
        muertos = [(x, y) for x, y in m["tramos"] if y - x > u["rachaMuertaMax"]]
        problemas = []
        if muertos:
            problemas.append("tramos muertos de más de %d s: %s" % (u["rachaMuertaMax"], ", ".join(f"{x}–{y} s" for x, y in muertos)))
        if m["micro"] > u["microMax"]:
            problemas.append(f"{m['micro']:.0f} % del tiempo con solo micromovimiento (máximo {u['microMax']} %)")
        for p in problemas:
            print("FALLA:", p)
        if m["plano"] > u["planoMedioMax"]:
            print(f"AVISO: plano medio de {m['plano']:.1f} s (referencia: hasta {u['planoMedioMax']} s); ¿falta cambiar de escala o de ángulo?")
        if problemas:
            fallo = True
            print("Arreglo: en esos tramos, cambia de escala o ángulo cada 2–4 s, haz que el personaje actúe (no solo respire),"
                  " agranda la acción principal y muestra un indicador que cambie.")
        else:
            print("OK: ritmo dentro de los umbrales.")
    return 1 if fallo else 0


if __name__ == "__main__":
    sys.exit(main())
