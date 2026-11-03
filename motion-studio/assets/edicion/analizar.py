"""Etapa 1 del modo edición: analiza el material grabado y deja todo lo que la planificación necesita en analisis/.

    python analizar.py [--idioma es] [--sin-transcribir] [--forzar]

Fuentes (originales: nunca se modifican):
  fuentes/camara/*     tú hablando (la primera con audio es la voz, salvo que montaje.json diga otra cosa)
  fuentes/pantalla/*   grabaciones de pantalla (OBS)
  fuentes/broll/*      tomas de recurso
  fuentes/audio/*      micrófono aparte, si lo hay (pasa a ser la voz)
Pasos y salida:
  ingesta      analisis/ingesta.json        formato, fps, VFR, rotación y audio de cada archivo
  salida       montaje.json -> salida       si falta, propone resolución, orientación y fps a partir de la cámara
  normalizar   analisis/normalizados/*.mp4  copias a fps constante (las grabaciones de móvil son VFR) con el
                                            codificador del perfil del equipo; analisis/audio/*.wav a 48 kHz
  sincronizar  montaje.json -> fuentes.*.desfase   por correlación de los ataques de audio con la voz
  transcribir  analisis/palabras.json       palabras con tiempo y confianza (faster-whisper; nivel completo)
  frases       analisis/frases.json         frases, silencios, sonidos sin palabra (muletillas probables) y tomas
                                            repetidas agrupadas con la elegida y el porqué
  calidad      analisis/calidad.json        luz por segundo y nivel de voz por frase
  escenas      analisis/escenas.json        cambios de contenido en las grabaciones de pantalla
Lee el perfil de `python scripts/preparar.py --perfil` (~/.motion-studio/estado.json) para elegir codificador, modelo
de Whisper y dispositivo. Sin faster-whisper (nivel núcleo) trabaja solo con la energía del audio.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import wave
from difflib import SequenceMatcher

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
AN = os.path.join(ROOT, "analisis")
HOME = os.environ.get("MOTION_STUDIO_HOME", os.path.join(os.path.expanduser("~"), ".motion-studio"))
VIDEO = {".mp4", ".mov", ".mkv", ".m4v", ".webm", ".avi", ".mts"}
AUDIO = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
FPS_NOMINALES = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]
SR = 48000
PAUSA_FRASE = 0.45        # una pausa así separa frases
PAUSA_LARGA = 1.0         # un silencio así se recorta en el montaje
# calidad de cada codificador para las copias normalizadas: casi sin pérdida, porque de ellas sale el video final
CALIDAD_NORM = {"h264_nvenc": ["-preset", "p5", "-rc", "vbr", "-cq", "16", "-b:v", "0"],
                "h264_amf": ["-quality", "quality", "-rc", "cqp", "-qp_i", "16", "-qp_p", "18"],
                "h264_qsv": ["-global_quality", "16"], "h264_videotoolbox": ["-q:v", "75"],
                "libx264": ["-preset", "veryfast", "-crf", "16"]}


def log(*a):
    print(*a, flush=True)


def ff(args, **kw):
    return subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *args], capture_output=True, **kw)


def perfil():
    try:
        return json.load(open(os.path.join(HOME, "estado.json"), encoding="utf-8")).get("perfil", {})
    except OSError:
        return {}


def cargar_montaje():
    ruta = os.path.join(ROOT, "montaje.json")
    return json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}


def guardar_json(nombre, datos):
    with open(os.path.join(AN, nombre), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)


def fraccion(s):
    a, _, b = (s or "0/1").partition("/")
    return float(a) / float(b) if float(b or 0) else 0.0


# ── ingesta ────────────────────────────────────────────────────────────────
def ingesta():
    fuentes, n = {}, {}
    for tipo, prefijo in (("camara", "cam"), ("audio", "mic"), ("pantalla", "pant"), ("broll", "broll")):
        carpeta = os.path.join(ROOT, "fuentes", tipo)
        for nombre in sorted(os.listdir(carpeta)) if os.path.isdir(carpeta) else []:
            ext = os.path.splitext(nombre)[1].lower()
            if ext not in VIDEO | AUDIO:
                continue
            n[prefijo] = n.get(prefijo, 0) + 1
            ruta = os.path.join("fuentes", tipo, nombre).replace("\\", "/")
            p = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", os.path.join(ROOT, ruta)],
                               capture_output=True, text=True)
            info = json.loads(p.stdout or "{}")
            v = next((s for s in info.get("streams", []) if s["codec_type"] == "video" and not s.get("disposition", {}).get("attached_pic")), None)
            a = next((s for s in info.get("streams", []) if s["codec_type"] == "audio"), None)
            f = {"tipo": tipo, "archivo": ruta, "duracion": round(float(info.get("format", {}).get("duration", 0)), 3), "audio": bool(a)}
            if v:
                rot = next((int(sd.get("rotation", 0)) for sd in v.get("side_data_list", []) if "rotation" in sd), 0)
                w, h = v["width"], v["height"]
                if abs(rot) % 180 == 90:
                    w, h = h, w
                r, avg = fraccion(v.get("r_frame_rate")), fraccion(v.get("avg_frame_rate"))
                f.update({"ancho": w, "alto": h, "rotacion": rot, "fps": round(r, 3), "fpsMedio": round(avg, 3),
                          "vfr": abs(r - avg) > 0.01, "color": v.get("color_space") or "sin etiqueta"})
            fuentes[f"{prefijo}{n[prefijo]}"] = f
    return fuentes


def proponer_salida(fuentes):
    cam = next((f for f in fuentes.values() if f["tipo"] == "camara" and "ancho" in f), None) or \
          next((f for f in fuentes.values() if "ancho" in f), None)
    if not cam:
        sys.exit("No hay ningún video en fuentes/camara, fuentes/pantalla ni fuentes/broll.")
    fps = min(FPS_NOMINALES, key=lambda x: abs(x - (cam["fps"] or 30)))
    return {"ancho": cam["ancho"] // 2 * 2, "alto": cam["alto"] // 2 * 2, "fps": fps, "nombre": "video", "propuesta": True}


# ── normalización ──────────────────────────────────────────────────────────
def normalizar(fuentes, salida, prf, forzar):
    os.makedirs(os.path.join(AN, "normalizados"), exist_ok=True)
    os.makedirs(os.path.join(AN, "audio"), exist_ok=True)
    cod = prf.get("codificadorRevision") or "libx264"
    for k, f in fuentes.items():
        orig = os.path.join(ROOT, f["archivo"])
        if f["audio"]:
            wav = f"analisis/audio/{k}.wav"
            if forzar or not os.path.exists(os.path.join(ROOT, wav)) or os.path.getmtime(os.path.join(ROOT, wav)) < os.path.getmtime(orig):
                # first_pts=0 + async: el audio empieza en 0 y rellena los huecos que deja un móvil, igual que el video CFR
                ff(["-i", orig, "-vn", "-af", "aresample=async=1:first_pts=0", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le",
                    os.path.join(ROOT, wav)], check=True)
            f["wav"] = wav
        if "ancho" not in f:
            continue
        dest = f"analisis/normalizados/{k}.mp4"
        f["normalizado"] = dest
        destino = os.path.join(ROOT, dest)
        if not forzar and os.path.exists(destino) and os.path.getmtime(destino) > os.path.getmtime(orig):
            continue
        t = time.time()
        # GOP de 1 s: cortar en cualquier punto obliga a decodificar como mucho un segundo
        args = lambda c: ["-i", orig, "-an", "-vf", f"fps={salida['fps']},format=yuv420p", "-c:v", c, *CALIDAD_NORM.get(c, []),
                          "-g", str(round(salida["fps"])), "-pix_fmt", "yuv420p", "-movflags", "+faststart", destino]
        r = ff(args(cod))
        if r.returncode and cod != "libx264":
            log(f"  {cod} falló con {k}; repito con libx264")
            r = ff(args("libx264"))
        if r.returncode:
            sys.exit(f"No pude normalizar {f['archivo']}: {r.stderr.decode(errors='replace')[-400:]}")
        log(f"  {k}: {f['archivo']} -> {dest} ({salida['fps']} fps constantes, {cod}, {time.time() - t:.0f} s)")


def leer_wav(ruta, sr=None):
    with wave.open(os.path.join(ROOT, ruta)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
        tasa = w.getframerate()
    if sr and sr != tasa:
        n = int(len(x) * sr / tasa)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
    return x


# ── sincronía ──────────────────────────────────────────────────────────────
def ataques(x, sr, hop):
    e = np.log((x[: len(x) // hop * hop].reshape(-1, hop) ** 2).sum(1) + 1e-6)
    d = np.maximum(0, np.diff(e, prepend=e[0]))
    return (d - d.mean()) / (d.std() + 1e-9)


def desfase(voz, otra, sr=8000, hop=16, maximo=180):
    """Segundos tales que t_otra = t_voz + desfase. Correlación de los ataques (2 ms de resolución), afinada con una
    parábola. Devuelve también la confianza: el pico frente al segundo mejor fuera de ±50 ms."""
    a, b = ataques(leer_wav(voz, sr), sr, hop), ataques(leer_wav(otra, sr), sr, hop)
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(b, n) * np.conj(np.fft.rfft(a, n)), n)
    tasa = sr / hop
    lags = np.r_[np.arange(0, len(b)), np.arange(-len(a) + 1, 0)]
    c = np.r_[c[: len(b)], c[n - len(a) + 1:]]
    valido = np.abs(lags) <= maximo * tasa
    c, lags = c[valido], lags[valido]
    k = int(np.argmax(c))
    fino = lags[k] + (0.5 * (c[k - 1] - c[k + 1]) / (c[k - 1] - 2 * c[k] + c[k + 1]) if 0 < k < len(c) - 1 else 0)
    lejos = np.abs(lags - lags[k]) > 0.05 * tasa
    conf = float(c[k] / (c[lejos].max() + 1e-9)) if lejos.any() else 1.0
    return round(float(fino / tasa), 4), round(conf, 2)


# ── transcripción ──────────────────────────────────────────────────────────
def transcribir(wav, idioma, prf, vocabulario):
    w = prf.get("whisper", {})
    if not w.get("modelo"):
        return None
    for p in w.get("bibliotecasCuda", []):
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(p)
        os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
    from faster_whisper import WhisperModel
    ruta = os.path.join(HOME, "modelos", "whisper", w["modelo"])
    # el audio se pasa ya decodificado (16 kHz): así no depende de la versión de PyAV que faster-whisper usa para abrir archivos
    audio = leer_wav(wav, 16000)
    for disp, tipo in ([(w["dispositivo"], w["tipo"])] + ([("cpu", "int8")] if w["dispositivo"] != "cpu" else [])):
        try:
            t = time.time()
            modelo = WhisperModel(ruta, device=disp, compute_type=tipo, cpu_threads=max(1, (os.cpu_count() or 4) - 2))
            segs, info = modelo.transcribe(audio, language=idioma, word_timestamps=True, vad_filter=True,
                                           initial_prompt=vocabulario or None, condition_on_previous_text=False)
            palabras, segmentos = [], []
            for s in segs:
                segmentos.append({"de": round(s.start, 3), "a": round(s.end, 3), "texto": s.text.strip()})
                for x in s.words or []:
                    if x.word.strip():
                        palabras.append({"t": x.word.strip(), "de": round(x.start, 3), "a": round(x.end, 3), "p": round(x.probability, 3)})
            log(f"  transcripción: {len(palabras)} palabras con {w['modelo']} en {disp} ({time.time() - t:.0f} s)")
            return {"modelo": w["modelo"], "dispositivo": disp, "idioma": info.language, "palabras": palabras, "segmentos": segmentos}
        except Exception as e:  # sin cuBLAS/cuDNN, memoria de video llena...: se repite en CPU
            log(f"  Whisper en {disp} falló ({str(e)[:120]}); {'repito en CPU' if disp != 'cpu' else 'sigo sin transcripción'}")
    return None


# ── frases, silencios, muletillas y tomas ──────────────────────────────────
def energia(x, hop=480):
    """Nivel en dB cada 10 ms."""
    return 10 * np.log10((x[: len(x) // hop * hop].reshape(-1, hop) ** 2).mean(1) + 1e-10)


SILENCIO_MIN = 8      # 80 ms bajo el umbral = la voz terminó; menos es una oclusiva o una sílaba suave


def voz_real(de, a, db, umbral):
    """Dónde empieza y termina de verdad la voz que Whisper situó en [de, a]. Sus tiempos suelen ir adelantados (el
    final llega antes que la última sílaba y el inicio antes que el primer sonido), así que se buscan los silencios
    de verdad a cada lado."""
    n, i, j = len(db), int(de * 100), int(a * 100)
    if i < n and db[i] < umbral:                      # empezó antes de la voz: avanza al primer sonido (máx. 0,6 s)
        k = next((k for k in range(i, min(n, i + 60)) if db[k] >= umbral), i)
    else:                                             # retrocede hasta un silencio de verdad (máx. 0,3 s)
        k = i
        while k > max(0, i - 30) and not np.all(db[max(0, k - SILENCIO_MIN):k] < umbral):
            k -= 1
    j = min(j, n - 1)
    while j < min(n, int(a * 100) + 80) and not np.all(db[j:j + SILENCIO_MIN] < umbral):   # avanza hasta el silencio (máx. 0,8 s)
        j += 1
    return k / 100, max(j / 100, k / 100 + 0.05)


def norm(texto):
    return re.sub(r"[^\wáéíóúüñ ]", " ", texto.lower()).split()


def frases_de(palabras, voz_db, umbral):
    frases, actual = [], []
    for i, p in enumerate(palabras):
        if actual and (p["de"] - palabras[actual[-1]]["a"] >= PAUSA_FRASE):
            frases.append(actual); actual = []
        actual.append(i)
        if re.search(r"[.?!…]$", p["t"]):
            frases.append(actual); actual = []
    if actual:
        frases.append(actual)
    out = []
    for k, idx in enumerate(frases):
        de, a = palabras[idx[0]]["de"], palabras[idx[-1]]["a"]
        seg = voz_db[int(de * 100): int(a * 100) + 1]
        out.append({"i": k, "palabras": [idx[0], idx[-1]], "de": de, "a": a, "texto": " ".join(palabras[j]["t"] for j in idx),
                    "confianza": round(float(np.mean([palabras[j]["p"] for j in idx])), 3),
                    "nivelDb": round(float(np.percentile(seg, 90)), 1) if len(seg) else None})
    return out


def sin_palabra(palabras, voz_db, umbral, dur):
    """Tramos con voz (energía sobre el umbral) que no cubre ninguna palabra: Whisper suele omitir "eh", "em" y
    arranques fallidos, así que se buscan por energía. Son muletillas probables; el agente decide."""
    con_voz = voz_db > umbral
    cubierto = np.zeros_like(con_voz)
    for p in palabras:
        cubierto[int(p["de"] * 100): int(p["a"] * 100) + 1] = True
    libre = con_voz & ~cubierto
    tramos, ini = [], None
    for i, v in enumerate(list(libre) + [False]):
        if v and ini is None:
            ini = i
        elif not v and ini is not None:
            if i - ini >= 12:          # 120 ms: más corto es una consonante desbordada o un clic
                tramos.append({"de": ini / 100, "a": min(dur, i / 100)})
            ini = None
    return tramos


def tomas(frases, palabras):
    """Agrupa frases repetidas (el mismo arranque o casi el mismo texto, cerca en el tiempo) y elige una por grupo."""
    padre = list(range(len(frases)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]; i = padre[i]
        return i

    for i, f in enumerate(frases):
        a = norm(f["texto"])
        for g in frases[i + 1: i + 5]:
            if g["de"] - f["a"] > 45:
                break
            b = norm(g["texto"])
            k = min(len(a), len(b), 4)
            prefijo = SequenceMatcher(None, a[:k], b[:k]).ratio() if k >= 3 else 0
            if prefijo >= 0.75 or SequenceMatcher(None, a, b).ratio() >= 0.6:
                padre[raiz(g["i"])] = raiz(i)
    grupos = {}
    for f in frases:
        grupos.setdefault(raiz(f["i"]), []).append(f)
    salida = []
    for miembros in grupos.values():
        if len(miembros) < 2:
            continue
        largo = max(len(norm(m["texto"])) for m in miembros)
        for m in miembros:
            completa = 1.0 if re.search(r"[.?!…]$", m["texto"].strip()) else 0.0
            m["puntaje"] = round(0.45 * len(norm(m["texto"])) / largo + 0.25 * m["confianza"] + 0.15 * completa
                                 + 0.15 * (m is miembros[-1]), 3)
        mejor = max(m["puntaje"] for m in miembros)
        # empate técnico (±0,05) -> la última: quien repite una frase suele quedarse con la última versión
        elegida = [m for m in miembros if m["puntaje"] >= mejor - 0.05][-1]
        salida.append({"frases": [m["i"] for m in miembros], "elegida": elegida["i"],
                       "porque": "más completa" if len(norm(elegida["texto"])) == largo else "mejor puntaje (confianza y final completo)",
                       "puntajes": {m["i"]: m["puntaje"] for m in miembros}})
    return salida


# ── calidad y escenas ──────────────────────────────────────────────────────
def luz(ruta):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", os.path.join(ROOT, ruta), "-vf",
                        "fps=2,scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"],
                       capture_output=True, text=True)
    y = [float(v) for v in re.findall(r"YAVG=([\d.]+)", r.stdout)]
    return [round(float(np.mean(y[i:i + 2])), 1) for i in range(0, len(y), 2)]


def escenas(ruta):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "info", "-i", os.path.join(ROOT, ruta), "-vf", "scale=320:-2,scdet=threshold=8",
                        "-f", "null", "-"], capture_output=True, text=True)
    return [round(float(t), 2) for t in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", r.stderr)]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--idioma", default="es")
    ap.add_argument("--sin-transcribir", action="store_true", help="nivel núcleo aunque haya Whisper")
    ap.add_argument("--forzar", action="store_true", help="rehacer normalizados y transcripción aunque existan")
    a = ap.parse_args()
    os.makedirs(AN, exist_ok=True)
    prf = perfil()
    if not prf:
        log("AVISO: no hay perfil del equipo; ejecuta `python scripts/preparar.py --perfil` (uso libx264 y nivel núcleo)")
    m = cargar_montaje()

    log("1/7 ingesta")
    fuentes = ingesta()
    if not fuentes:
        sys.exit("No hay archivos en fuentes/camara, fuentes/pantalla, fuentes/broll ni fuentes/audio.")
    for k, f in fuentes.items():
        log(f"  {k}: {f['archivo']} · {f.get('ancho', '-')}×{f.get('alto', '-')} · {f.get('fps', '-')} fps"
            + (" (VFR)" if f.get("vfr") else "") + f" · {f['duracion']} s · audio {'sí' if f['audio'] else 'no'}")
    guardar_json("ingesta.json", fuentes)
    salida = m.get("salida") if all(m.get("salida", {}).get(k) for k in ("ancho", "alto", "fps")) else {**proponer_salida(fuentes), **m.get("salida", {})}
    if salida.get("propuesta"):
        log(f"2/7 salida propuesta desde la cámara: {salida['ancho']}×{salida['alto']} a {salida['fps']} fps (confírmala con el usuario)")
    else:
        log(f"2/7 salida de montaje.json: {salida['ancho']}×{salida['alto']} a {salida['fps']} fps")

    log("3/7 normalizar")
    normalizar(fuentes, salida, prf, a.forzar)
    previas = m.get("fuentes", {})
    voz = m.get("voz") if m.get("voz") in fuentes else next((k for k in fuentes if k.startswith("mic")), None) or \
        next((k for k, f in fuentes.items() if f["tipo"] == "camara" and f["audio"]), None)
    if not voz:
        sys.exit("No hay ninguna fuente con voz (cámara con audio o fuentes/audio).")

    log("4/7 sincronizar")
    for k, f in fuentes.items():
        f["desfase"], f["confianzaSincronia"] = (0.0, None) if k == voz else (previas.get(k, {}).get("desfase"), None)
        if k != voz and f["audio"] and (a.forzar or f["desfase"] is None):
            f["desfase"], f["confianzaSincronia"] = desfase(fuentes[voz]["wav"], f["wav"])
            log(f"  {k}: desfase {f['desfase']:+.3f} s respecto a {voz} (confianza {f['confianzaSincronia']})"
                + ("  <- baja: revisa a mano" if f["confianzaSincronia"] < 1.5 else ""))
        elif k != voz and not f["audio"]:
            f["desfase"] = f["desfase"] or 0.0
            log(f"  {k}: sin audio, no se puede sincronizar; desfase {f['desfase']} (ajústalo en montaje.json si hace falta)")

    log("5/7 transcribir")
    ruta_pal = os.path.join(AN, "palabras.json")
    pal = json.load(open(ruta_pal, encoding="utf-8")) if os.path.exists(ruta_pal) and not a.forzar else {}
    if voz not in pal and not a.sin_transcribir:
        voc = os.path.join(ROOT, "vocabulario.txt")
        t = transcribir(fuentes[voz]["wav"], a.idioma, prf, open(voc, encoding="utf-8").read().strip() if os.path.exists(voc) else "")
        if t:
            pal[voz] = t
            guardar_json("palabras.json", pal)
    palabras = pal.get(voz, {}).get("palabras", [])
    nivel = "completo" if palabras else "núcleo"
    if not palabras:
        log("  sin transcripción: nivel núcleo (cortes solo por silencios)")

    log("6/7 frases, silencios y tomas")
    x = leer_wav(fuentes[voz]["wav"])
    db = energia(x)
    piso = float(np.percentile(db, 10))
    umbral = max(piso + 12, float(np.percentile(db, 60)) - 25)
    dur = len(x) / SR
    if palabras:
        fr = frases_de(palabras, db, umbral)
    else:   # núcleo: frases = tramos con voz separados por pausas
        con_voz = np.convolve(db > umbral, np.ones(int(PAUSA_FRASE * 100)), "same") > 0
        cambios = np.flatnonzero(np.diff(np.r_[0, con_voz.astype(int), 0]))
        fr = [{"i": k, "palabras": None, "de": round(s / 100, 2), "a": round(e / 100, 2), "texto": "", "confianza": None,
               "nivelDb": round(float(np.percentile(db[s:e], 90)), 1)} for k, (s, e) in enumerate(zip(cambios[::2], cambios[1::2]))]
    silencios = [{"de": round(f["a"], 3), "a": round(g["de"], 3)} for f, g in zip(fr, fr[1:]) if g["de"] - f["a"] >= PAUSA_LARGA]
    sp = sin_palabra(palabras, db, umbral, dur) if palabras else []
    # pegado a una palabra es la cola o el ataque que Whisper no incluyó (sus finales suelen llegar antes de tiempo);
    # suelto, entre frases, es una muletilla o un arranque fallido probable
    for s in sp:
        s["tipo"] = "cola" if any(abs(s["de"] - p["a"]) < 0.06 or abs(s["a"] - p["de"]) < 0.06 for p in palabras) else "muletilla probable"
    for p in palabras:   # palabras sin voz debajo: alucinaciones típicas de Whisper ("Gracias." al final de un silencio)
        seg = db[int(p["de"] * 100): int(p["a"] * 100) + 1]
        p["sinVoz"] = bool(len(seg) == 0 or (p["p"] < 0.6 and float(np.mean(seg)) < umbral))
    # los bordes de cada frase pasan a ser los de la voz real; el tiempo de Whisper se conserva en deWhisper/aWhisper
    for f in fr if palabras else []:
        x0, x1 = f["palabras"]
        if all(palabras[k]["sinVoz"] for k in range(x0, x1 + 1)):
            continue
        ini, fin = voz_real(f["de"], f["a"], db, umbral)
        p0, p1 = palabras[x0], palabras[x1]
        p0.setdefault("deWhisper", p0["de"]); p1.setdefault("aWhisper", p1["a"])
        p0["de"], p1["a"] = round(min(ini, p0["a"] - 0.02), 3), round(max(fin, p1["de"] + 0.02), 3)
        f["de"], f["a"] = p0["de"], p1["a"]
    silencios = [{"de": round(f["a"], 3), "a": round(g["de"], 3)} for f, g in zip(fr, fr[1:]) if g["de"] - f["a"] >= PAUSA_LARGA]
    if palabras:
        guardar_json("palabras.json", pal)
    tm = tomas(fr, palabras) if palabras else []
    guardar_json("frases.json", {"fuente": voz, "nivel": nivel, "umbralDb": round(umbral, 1), "frases": fr, "silencios": silencios,
                                 "sinPalabra": sp, "tomas": tm})
    log(f"  {len(fr)} frases · {len(silencios)} silencios ≥ {PAUSA_LARGA} s · {len(sp)} sonidos sin palabra · {len(tm)} grupos de tomas")
    for g in tm:
        log(f"  tomas {g['frases']} -> se queda la {g['elegida']} ({g['porque']})")

    log("7/7 calidad y escenas")
    cal = {k: {"luzPorSegundo": luz(f["normalizado"])} for k, f in fuentes.items() if f.get("normalizado") and f["tipo"] == "camara"}
    guardar_json("calidad.json", cal)
    guardar_json("escenas.json", {k: escenas(f["normalizado"]) for k, f in fuentes.items() if f.get("normalizado") and f["tipo"] == "pantalla"})

    m.setdefault("version", 1)
    m["salida"] = salida
    m["fuentes"] = {k: {kk: f[kk] for kk in ("tipo", "archivo", "normalizado", "wav", "duracion", "desfase", "ancho", "alto") if kk in f}
                    for k, f in fuentes.items()}
    m["voz"] = voz
    m.setdefault("clips", [])
    m["nivel"] = nivel
    with open(os.path.join(ROOT, "montaje.json"), "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)
    log(f"Análisis listo (nivel {nivel}). Siguiente: python planificar.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
