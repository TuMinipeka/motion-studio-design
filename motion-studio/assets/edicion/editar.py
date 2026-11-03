"""Etapa 4 del modo edición: renderiza montaje.json con FFmpeg, por segmentos y con caché.

    python editar.py                 revisión: resolución reducida y codificador por hardware del perfil (rápido)
    python editar.py --final         calidad final: salida.ancho×alto, salida.codificador (libx264 por defecto)
    python editar.py --solo 4,7      rehace solo esos clips (el resto sale de la caché)

Cada clip es un segmento de video sin audio, codificado con los mismos parámetros; su nombre es el hash de lo que lo
define (fuente, tramo en fotogramas, layout, zoom, foco, transición, salida y archivos de origen). Cambiar un clip solo
rehace ese segmento. La voz se monta aparte con muestras exactas (cada clip dura sus fotogramas / fps), con un
microfundido de 12 ms en cada corte para que no suene un clic, y se normaliza a −14 LUFS / −1 dBTP en dos pasadas.
Salida: exportaciones/<nombre>_revision.mp4 o exportaciones/<nombre>.mp4 (H.264 yuv420p, etiquetado BT.709) y
review/cortes.json con los instantes de cada corte (para qc.py).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import montaje as mt

ROOT = os.path.dirname(os.path.abspath(__file__))
HOME = os.environ.get("MOTION_STUDIO_HOME", os.path.join(os.path.expanduser("~"), ".motion-studio"))
VERSION = "1"                 # súbela si cambia cómo se dibuja un segmento: invalida la caché
SR = 48000
FUNDIDO_AUDIO = 0.012
FONDO = "0x101014"
COLOR = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
REVISION = {"h264_nvenc": ["-preset", "p4", "-rc", "vbr", "-cq", "23", "-b:v", "0"],
            "h264_amf": ["-quality", "balanced", "-rc", "cqp", "-qp_i", "23", "-qp_p", "25"],
            "h264_qsv": ["-global_quality", "23"], "h264_videotoolbox": ["-q:v", "60"],
            "libx264": ["-preset", "veryfast", "-crf", "23"]}


def perfil():
    try:
        return json.load(open(os.path.join(HOME, "estado.json"), encoding="utf-8")).get("perfil", {})
    except OSError:
        return {}


def par(x):
    return int(round(x / 2)) * 2


def tam_revision(s):
    """Lado mayor de 960 px: suficiente para revisar ritmo, encuadre y subtítulos."""
    f = min(1.0, 960 / max(s["ancho"], s["alto"]))
    return par(s["ancho"] * f), par(s["alto"] * f)


def cubrir(w, h, W, H, zoom=1.0, foco=(0.5, 0.4)):
    """scale+crop que llena W×H con una fuente w×h, ampliada `zoom` veces y centrada en `foco` (0–1)."""
    s = max(W / w, H / h) * zoom
    sw, sh = par(w * s + 1), par(h * s + 1)
    x = min(max(0, round(foco[0] * sw - W / 2)), sw - W)
    y = min(max(0, round(foco[1] * sh - H / 2)), sh - H)
    return f"scale={sw}:{sh}:flags=lanczos,crop={W}:{H}:{x}:{y}"


def contener(W, H):
    return f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={FONDO}"


def segmento(m, c, W, H, n, cod, args_cod, destino):
    """Comando FFmpeg de un clip. Los -ss van antes de cada -i: con decodificación es exacto al fotograma y rápido
    porque las copias normalizadas tienen un fotograma clave por segundo."""
    F = m["fuentes"]
    fps = m["salida"]["fps"]
    f = F[c["fuente"]]
    entradas = ["-ss", f"{c['de']:.4f}", "-i", os.path.join(ROOT, f["normalizado"])]
    zoom, foco = c.get("zoom", 1.0), c.get("foco", [0.5, 0.4])
    lay = c.get("layout", "completo")
    if lay == "completo":
        grafo = f"[0:v]{cubrir(f['ancho'], f['alto'], W, H, zoom, foco)},setsar=1[v]"
    else:
        p = F[c["pantalla"]["fuente"]]
        entradas += ["-ss", f"{c['pantalla']['de']:.4f}", "-i", os.path.join(ROOT, p["normalizado"])]
        if lay == "pantalla":
            grafo = f"[1:v]{contener(W, H)},setsar=1[v]"
        elif H > W:   # vertical: la pantalla arriba y la cámara llenando la mitad de abajo
            hp = par(H * 0.42)
            grafo = (f"[1:v]{contener(W, hp)}[p];[0:v]{cubrir(f['ancho'], f['alto'], W, H - hp, zoom, foco)}[c];"
                     f"[p][c]vstack,setsar=1[v]")
        else:         # horizontal: la cámara en la esquina inferior derecha con un borde fino
            pw = par(W * 0.24); ph = par(pw * 0.75); margen = par(W * 0.025); borde = max(2, par(W / 480))
            grafo = (f"[1:v]{contener(W, H)}[p];[0:v]{cubrir(f['ancho'], f['alto'], pw, ph, zoom, foco)},"
                     f"pad={pw + 2 * borde}:{ph + 2 * borde}:{borde}:{borde}:color=0xf2f2f2[c];"
                     f"[p][c]overlay={W - pw - 2 * borde - margen}:{H - ph - 2 * borde - margen}:shortest=1,setsar=1[v]")
    if c.get("transicion") == "fundido":   # entrada desde negro de 6 fotogramas
        grafo = grafo[:-3] + f",fade=t=in:st=0:d={6 / fps:.4f}[v]"
    grafo = grafo[:-3] + f",scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]"
    return ["ffmpeg", "-hide_banner", "-v", "error", "-y", *entradas, "-filter_complex", grafo, "-map", "[v]", "-frames:v", str(n),
            "-r", str(fps), "-c:v", cod, *args_cod, "-g", str(round(fps)), "-pix_fmt", "yuv420p", *COLOR,
            "-video_track_timescale", "90000", "-an", destino]


def clave(m, c, W, H, n, cod, args_cod):
    F = m["fuentes"]
    usadas = [c["fuente"]] + ([c["pantalla"]["fuente"]] if c.get("pantalla") else [])
    origen = [(F[k]["normalizado"], os.path.getsize(os.path.join(ROOT, F[k]["normalizado"])),
               int(os.path.getmtime(os.path.join(ROOT, F[k]["normalizado"])))) for k in usadas]
    visual = {k: c.get(k) for k in ("fuente", "layout", "pantalla", "zoom", "foco", "transicion")}
    visual["de"] = round(c["de"], 4)
    datos = json.dumps([VERSION, visual, n, W, H, m["salida"]["fps"], cod, args_cod, origen], sort_keys=True)
    return hashlib.sha1(datos.encode()).hexdigest()[:16]


def leer_wav(ruta):
    with wave.open(ruta) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1, f"{ruta}: se espera mono a {SR} Hz (lo escribe analizar.py)"
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768


def voz(m, salida_wav):
    """Concatena la voz de cada clip con muestras exactas y microfundidos; devuelve los instantes de los cortes."""
    fps = m["salida"]["fps"]
    vz = m["voz"]
    x = leer_wav(os.path.join(ROOT, m["fuentes"][vz]["wav"]))
    partes, cortes, t, fin_previo = [], [], 0, None
    nf = int(FUNDIDO_AUDIO * SR)
    rampa = np.linspace(0, 1, nf, dtype=np.float32)
    for c in m["clips"]:
        n = mt.cuadros(m, c["a"] - c["de"])
        muestras = round(n * SR / fps)
        # el reloj del clip es el de su fuente; la voz va en el suyo: t_fuente = t_voz + desfase
        ini = round((c["de"] - m["fuentes"][c["fuente"]].get("desfase", 0.0) + m["fuentes"][vz].get("desfase", 0.0)) * SR)
        seg = np.zeros(muestras, np.float32)
        a, b = max(0, ini), min(len(x), ini + muestras)
        if b > a:
            seg[a - ini: b - ini] = x[a:b]
        # solo hay corte de audio si la voz salta; un cambio de layout sobre voz continua no lleva fundido (sería un hueco)
        salto = fin_previo is None or abs(ini - fin_previo) > 0.002 * SR
        if salto:
            seg[:nf] *= rampa
            if partes:
                partes[-1][-nf:] *= rampa[::-1]
                cortes.append(round(t / fps, 4))
        partes.append(seg)
        fin_previo = ini + muestras
        t += n
    if partes:
        partes[-1][-nf:] *= rampa[::-1]
    y = np.concatenate(partes) if partes else np.zeros(1, np.float32)
    with wave.open(salida_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
    return cortes


def normalizar_audio(entrada, salida, lufs=-14, pico=-1):
    """Paso alto + loudnorm en dos pasadas (la primera mide, la segunda aplica con esas medidas, en modo lineal)."""
    base = f"highpass=f=70,loudnorm=I={lufs}:TP={pico}:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", entrada, "-af", base + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr[r.stderr.rfind("{"): r.stderr.rfind("}") + 1]
    med = json.loads(txt) if txt else {}
    if med.get("input_i") and med["input_i"] != "-inf":
        base += (f":measured_I={med['input_i']}:measured_TP={med['input_tp']}:measured_LRA={med['input_lra']}"
                 f":measured_thresh={med['input_thresh']}:offset={med['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", entrada, "-af", base + f",aresample={SR}", "-ar", str(SR),
                    "-c:a", "pcm_s16le", salida], check=True)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--solo", help="ids de clips que se rehacen aunque estén en caché")
    ap.add_argument("--paralelo", type=int)
    a = ap.parse_args()
    m = mt.cargar()
    errores = mt.validar(m)
    if errores:
        for e in errores:
            print("ERROR:", e)
        sys.exit("montaje.json no es válido: corrige con montaje.py antes de renderizar.")
    prf = perfil()
    s = m["salida"]
    if a.final:
        W, H = s["ancho"], s["alto"]
        cod = s.get("codificador", "libx264")
        args_cod = s.get("parametros") or (["-preset", s.get("preset", "slow"), "-crf", str(s.get("crf", 18))] if cod == "libx264"
                                          else REVISION.get(cod, []))
    else:
        W, H = tam_revision(s)
        cod = prf.get("codificadorRevision") or "libx264"
        args_cod = REVISION.get(cod, [])
    modo = "final" if a.final else "revision"
    cache = os.path.join(ROOT, "cache", modo)
    os.makedirs(cache, exist_ok=True)
    rehacer = {int(x) for x in a.solo.split(",")} if a.solo else set()

    trabajos, lista = [], []
    for c in m["clips"]:
        n = mt.cuadros(m, c["a"] - c["de"])
        destino = os.path.join(cache, clave(m, c, W, H, n, cod, args_cod) + ".mp4")
        lista.append(destino)
        if c["id"] in rehacer or not os.path.exists(destino):
            trabajos.append((c, n, destino))
    print(f"{modo}: {W}×{H} · {s['fps']} fps · {cod} · {len(m['clips'])} clips, {len(trabajos)} por renderizar, "
          f"{len(m['clips']) - len(trabajos)} en caché")

    def hacer(t):
        c, n, destino = t
        tmp = destino + ".part.mp4"
        r = subprocess.run(segmento(m, c, W, H, n, cod, args_cod, tmp), capture_output=True, text=True)
        if r.returncode and cod != "libx264":    # el codificador por hardware puede rechazar un tamaño: x264 siempre sirve
            r = subprocess.run(segmento(m, c, W, H, n, "libx264", REVISION["libx264"], tmp), capture_output=True, text=True)
        if r.returncode:
            return f"clip {c['id']}: {r.stderr[-300:]}"
        os.replace(tmp, destino)
        return None

    t0 = time.time()
    paralelo = a.paralelo or prf.get("paralelo") or 2
    with ThreadPoolExecutor(paralelo) as ex:
        fallos = [e for e in ex.map(hacer, trabajos) if e]
    if fallos:
        for e in fallos:
            print("ERROR:", e)
        return 1
    print(f"  segmentos listos en {time.time() - t0:.1f} s (paralelo {paralelo})")

    os.makedirs(os.path.join(ROOT, "review"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "exportaciones"), exist_ok=True)
    bruto, limpio = os.path.join(cache, "voz_bruta.wav"), os.path.join(cache, "voz.wav")
    cortes = voz(m, bruto)
    normalizar_audio(bruto, limpio)
    with open(os.path.join(cache, "lista.txt"), "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.basename(p)}'\n" for p in lista)
    nombre = s.get("nombre", "video") + ("" if a.final else "_revision")
    salida = os.path.join(ROOT, "exportaciones", nombre + ".mp4")
    dur = mt.duracion(m)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(cache, "lista.txt"),
                        "-i", limpio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-t", f"{dur:.4f}",
                        *COLOR, "-movflags", "+faststart", salida], capture_output=True, text=True)
    if r.returncode:
        print("ERROR al unir:", r.stderr[-500:]); return 1
    json.dump({"modo": modo, "archivo": os.path.relpath(salida, ROOT), "duracion": round(dur, 4), "cortes": cortes,
               "clips": [{"id": c["id"], "ini": round(i, 4), "fin": round(f, 4)} for c, i, f in mt.posiciones(m)]},
              open(os.path.join(ROOT, "review", "cortes.json"), "w", encoding="utf-8"), indent=1)
    print(f"OK {os.path.relpath(salida, ROOT)} · {dur:.2f} s · {len(cortes)} cortes · {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
