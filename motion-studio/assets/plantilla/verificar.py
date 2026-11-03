"""Verificación de la exportación: lo que debe cumplir el archivo antes de entregarlo (references/rubricas.md, §13).

    python verificar.py                  revisa exportaciones/<nombre>.mp4 de motion.config.json
    python verificar.py video.mp4        revisa otro archivo; fuera del proyecto solo comprueba lo que no depende de la config
En un proyecto del modo edición (sin motion.config.json) toma resolución, fps y duración de montaje.json.

FALLA (código 1, bloqueante): códec distinto de H.264 o píxeles distintos de yuv420p; resolución, fps o duración distintos
de motion.config.json; fps variable; número de fotogramas incorrecto; negro casi puro durante 1 s o más fuera del primer y último medio segundo; falta el audio o no está a −14 ±1 LUFS cuando el
proyecto tiene audio/final.wav; audio y video con más de 0,1 s de diferencia. Un fundido a negro breve entre escenas no cuenta, y un fondo oscuro tampoco.
AVISO: color sin etiquetas BT.709, true peak por encima de −1 dBTP, imagen congelada 4 s o más fuera de las pausas
declaradas. Los negros intencionados se declaran en motion.config.json -> "verificacion" -> "negros": [[inicio, fin]].
Deja el informe en review/verificacion.json. Necesita ffmpeg y ffprobe.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def probe(ruta):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-show_entries",
                        "stream=codec_type,codec_name,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_read_packets,"
                        "duration,color_space,color_primaries,color_transfer:format=duration", "-of", "json", ruta],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"No puedo leer {ruta}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def fraccion(s):
    a, _, b = (s or "0/1").partition("/")
    return float(a) / float(b or 1) if float(b or 1) else 0.0


def filtros(ruta, tiene_audio):
    """Una sola decodificación: negros y congelados en la imagen; sonoridad y true peak en el audio."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", ruta, "-map", "0:v:0", "-vf", "blackdetect=d=1:pix_th=0.02,freezedetect=n=0.001:d=4"]
    if tiene_audio:
        cmd += ["-map", "0:a:0", "-af", "ebur128=peak=true"]
    r = subprocess.run(cmd + ["-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    t = r.stderr
    negros = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", t)]
    ini = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", t)]
    fin = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", t)]
    congelados = [(a, fin[i] if i < len(fin) else None) for i, a in enumerate(ini)]
    resumen = t[t.rfind("Summary:"):] if "Summary:" in t else ""
    lufs = re.search(r"I:\s+(-?[\d.]+) LUFS", resumen)
    pico = re.search(r"True peak:\s+Peak:\s+(-?[\d.]+|-inf) dBFS", resumen)
    return negros, congelados, (float(lufs.group(1)) if lufs else None), (float(pico.group(1)) if pico and pico.group(1) != "-inf" else None)


def solapa(a, b, tramos):
    return any(min(b, y) - max(a, x) > 0 for x, y, *_ in tramos)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        cfg = json.load(open(os.path.join(ROOT, "motion.config.json"), encoding="utf-8"))
    except OSError:
        cfg = {}
    if not cfg and os.path.exists(os.path.join(ROOT, "montaje.json")):
        # proyecto del modo edición: resolución, fps y duración salen de montaje.json; siempre lleva la voz
        sys.path.insert(0, ROOT)
        import montaje as mt
        m = mt.cargar()
        s = m["salida"]
        cfg = {"video": {"ancho": s["ancho"], "alto": s["alto"], "fps": s["fps"], "duracion": round(mt.duracion(m), 4)},
               "salida": {"carpeta": "exportaciones", "nombre": s.get("nombre", "video")}, "curva": m.get("curva", {}),
               "_voz": True}
    salida = cfg.get("salida", {})
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, salida.get("carpeta", "exportaciones"), salida.get("nombre", "video") + ".mp4")
    if not os.path.exists(ruta):
        sys.exit(f"No existe {ruta}: ejecuta antes `node render.mjs --final` o pasa la ruta de un video.")
    # la configuración del proyecto solo se aplica a sus propios archivos
    propio = bool(cfg) and os.path.abspath(ruta).startswith(ROOT + os.sep)
    info = probe(ruta)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        sys.exit(f"{ruta} no tiene pista de video.")
    dur = float(info["format"].get("duration", 0))
    fps = fraccion(v.get("r_frame_rate"))
    fallos, avisos, ok = [], [], []

    def check(cond, texto_ok, texto_falla, bloqueante=True):
        (ok.append(texto_ok) if cond else (fallos if bloqueante else avisos).append(texto_falla))

    check(v.get("codec_name") == "h264", "códec H.264", f"códec {v.get('codec_name')} (se espera h264)")
    check(v.get("pix_fmt") == "yuv420p", "píxeles yuv420p", f"píxeles {v.get('pix_fmt')} (se espera yuv420p para compatibilidad)")
    check(abs(fps - fraccion(v.get("avg_frame_rate"))) < 0.01, f"fps constante ({fps:g})", f"fps variable (r={v.get('r_frame_rate')}, media={v.get('avg_frame_rate')})")
    if propio:
        cv = cfg.get("video", {})
        check((v.get("width"), v.get("height")) == (cv.get("ancho"), cv.get("alto")), f"resolución {v.get('width')}×{v.get('height')}",
              f"resolución {v.get('width')}×{v.get('height')}; la config dice {cv.get('ancho')}×{cv.get('alto')}")
        check(abs(fps - cv.get("fps", fps)) < 0.01, f"{fps:g} fps como la config", f"{fps:g} fps; la config dice {cv.get('fps')}")
        check(abs(dur - cv.get("duracion", dur)) <= 1.5 / max(fps, 1), f"duración {dur:.2f} s", f"duración {dur:.2f} s; la config dice {cv.get('duracion')} s")
        esperados = round(cv.get("fps", fps) * cv.get("duracion", dur))
        leidos = int(v.get("nb_read_packets", 0))
        check(abs(leidos - esperados) <= 1, f"{leidos} fotogramas", f"{leidos} fotogramas; se esperaban {esperados} (¿faltan o sobran segmentos?)")

    etiquetas = (v.get("color_space"), v.get("color_primaries"), v.get("color_transfer"))
    check(all(e == "bt709" for e in etiquetas), "color etiquetado BT.709",
          f"color sin etiquetar ({'/'.join(str(e) for e in etiquetas)}): algunos reproductores lo interpretan como BT.601 y cambian el tono", bloqueante=False)

    negros, congelados, lufs, pico = filtros(ruta, a is not None)
    declarados = cfg.get("verificacion", {}).get("negros", []) if propio else []
    pausas = cfg.get("curva", {}).get("pausas", []) if propio else []
    # medio segundo de negro al principio o al final es un fundido, no un fallo
    malos = [(x, y) for x, y in negros if not (y <= 0.5 or x >= dur - 0.5) and not solapa(x, y, declarados)]
    check(not malos, "sin tramos negros", "tramos negros: " + ", ".join(f"{x:.2f}–{y:.2f} s" for x, y in malos)
          + " (si son intencionados, decláralos en verificacion.negros)")
    quietos = [(x, y) for x, y in congelados if not solapa(x, y if y is not None else dur, pausas)]
    check(not quietos, "sin imagen congelada 4 s o más", "imagen congelada: " + ", ".join(f"{x:.1f}–{(y if y is not None else dur):.1f} s" for x, y in quietos), bloqueante=False)

    espera_audio = propio and (cfg.get("_voz") or os.path.exists(os.path.join(ROOT, "audio", "final.wav")))
    if a is None:
        check(not espera_audio, "sin audio (no hay audio/final.wav)", "falta la pista de audio (hay audio/final.wav o es un montaje con voz)")
    else:
        da = float(a.get("duration") or dur)
        check(abs(da - dur) <= 0.1, "audio y video con la misma duración", f"audio {da:.2f} s frente a video {dur:.2f} s")
        check(lufs is not None and abs(lufs + 14) <= 1, f"sonoridad {lufs} LUFS", f"sonoridad {lufs} LUFS (se espera −14 ±1)")
        check(pico is not None and pico <= -1, f"true peak {pico} dBTP", f"true peak {pico} dBTP, por encima de −1: puede saturar al recodificarse en la plataforma", bloqueante=False)

    print(f"{os.path.basename(ruta)} · {v.get('width')}×{v.get('height')} · {fps:g} fps · {dur:.2f} s" + ("" if propio else " · fuera del proyecto: sin comparar con motion.config.json"))
    for x in ok:
        print("  OK   ", x)
    for x in avisos:
        print("  AVISO", x)
    for x in fallos:
        print("  FALLA", x)
    os.makedirs(os.path.join(ROOT, "review"), exist_ok=True)
    json.dump({"archivo": os.path.abspath(ruta), "ok": ok, "avisos": avisos, "fallos": fallos},
              open(os.path.join(ROOT, "review", "verificacion.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("Resultado:", "FALLA" if fallos else "OK", "(informe en review/verificacion.json)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
