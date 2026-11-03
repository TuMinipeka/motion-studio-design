#!/usr/bin/env python3
"""Instala y verifica las herramientas con las que trabaja Motion Studio. Ejecútalo una vez tras instalar la skill
(los instaladores lo hacen solos) y el agente lo vuelve a comprobar antes de cada video.

    python scripts/preparar.py              instala lo que falte a nivel de usuario y verifica todo
    python scripts/preparar.py --comprobar  solo verifica (rápido); código 1 si falta algo
    python scripts/preparar.py --sistema    además instala Node.js y FFmpeg con el gestor del sistema (winget, brew)
    python scripts/preparar.py --perfil     perfil del equipo para el modo edición (GPU, codificadores, RAM, disco, nivel)
    python scripts/preparar.py --edicion [--modelo large-v3-turbo] [--whisper-gpu]
                                            nivel "completo" del modo edición: faster-whisper y un modelo de Whisper
                                            (--whisper-gpu añade las bibliotecas CUDA para transcribir en una GPU NVIDIA)

Qué prepara:
- En una carpeta compartida por todos los videos (MOTION_STUDIO_HOME, por defecto ~/.motion-studio):
  Playwright, Chromium y una colección de fuentes (@fontsource). render.mjs la usa si el proyecto no trae las suyas,
  y sirve sus fuentes en /node_modules/... Así no se instala nada por proyecto.
- En Python: numpy (audio/musica.py, ritmo.py) y Pillow (sheet.py), con `pip install --user`.
- Comprueba Node.js >= 18, FFmpeg con libx264 y el filtro ebur128 (sonoridad), y que Chrome sin interfaz obtiene la
  GPU (WebGL) en lugar de SwiftShader.
Node.js y FFmpeg son programas del sistema: sin --sistema solo se indica el comando para instalarlos.
Modo edición de video real (references/edicion.md): el perfil decide el codificador de revisión, el modelo de Whisper
y el paralelismo según el hardware; nada se impone. Niveles: "núcleo" (solo FFmpeg), "completo" (+ faster-whisper),
"avanzado" (+ PyTorch, opcional y aún sin uso).
Deja el resultado en MOTION_STUDIO_HOME/estado.json.
"""
import argparse
import datetime
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path(os.environ.get("MOTION_STUDIO_HOME", Path.home() / ".motion-studio"))
# Fuentes elegidas para cubrir estilos distintos: titulares, interfaz, editorial, rotulador, píxel y monoespaciada.
FUENTES = ["inter", "space-grotesk", "montserrat", "bebas-neue", "anton", "archivo-black", "dm-serif-display",
           "playfair-display", "permanent-marker", "press-start-2p", "silkscreen", "jetbrains-mono"]
PIP = ["numpy", "pillow"]
SISTEMA = {
    "Windows": {"node": ["winget", "install", "--id", "OpenJS.NodeJS.LTS", "-e"], "ffmpeg": ["winget", "install", "--id", "Gyan.FFmpeg", "-e"]},
    "Darwin": {"node": ["brew", "install", "node"], "ffmpeg": ["brew", "install", "ffmpeg"]},
    "Linux": {"node": ["sudo", "apt-get", "install", "-y", "nodejs", "npm"], "ffmpeg": ["sudo", "apt-get", "install", "-y", "ffmpeg"]},
}

resultados = []


def informe(nombre, ok, detalle=""):
    resultados.append((nombre, ok, detalle))
    print(f"  {'OK   ' if ok else 'FALTA'} {nombre:22} {detalle}")


def correr(cmd, **kw):
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    return subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def instalar_sistema(que):
    cmd = SISTEMA.get(platform.system(), {}).get(que)
    if not cmd or not shutil.which(cmd[0]):
        print(f"  No sé instalar {que} en este sistema: instálalo a mano y repite.")
        return
    print(f"  Instalando {que}: {' '.join(cmd)}")
    subprocess.run(cmd)
    print("  Si el comando sigue sin encontrarse, abre una terminal nueva (el PATH se actualiza al reiniciarla).")


def python_mods(comprobar):
    faltan = []
    for m in PIP:
        try:
            __import__("PIL" if m == "pillow" else m)
        except ImportError:
            faltan.append(m)
    if faltan and not comprobar:
        print(f"  pip install --user {' '.join(faltan)}")
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--quiet", *faltan])
        faltan = [m for m in faltan if subprocess.run([sys.executable, "-c", f"import {'PIL' if m == 'pillow' else m}"]).returncode]
    informe("Python " + platform.python_version(), sys.version_info >= (3, 9), "" if sys.version_info >= (3, 9) else "se necesita 3.9+")
    informe("numpy, Pillow", not faltan, f"faltan: {', '.join(faltan)} -> {sys.executable} -m pip install --user {' '.join(faltan)}" if faltan else "")


def node(comprobar, sistema):
    r = correr(["node", "--version"])
    if r is None and sistema and not comprobar:
        instalar_sistema("node"); r = correr(["node", "--version"])
    v = r.stdout.strip() if r else ""
    mayor = int(re.match(r"v(\d+)", v).group(1)) if re.match(r"v(\d+)", v) else 0
    pista = " ".join(SISTEMA.get(platform.system(), {}).get("node", ["(instálalo desde nodejs.org)"]))
    informe("Node.js " + (v or ""), mayor >= 18, "" if mayor >= 18 else f"se necesita 18+ -> {pista} (o --sistema)")
    return mayor >= 18


def ffmpeg(comprobar, sistema):
    if not shutil.which("ffmpeg") and sistema and not comprobar:
        instalar_sistema("ffmpeg")
    r = correr(["ffmpeg", "-hide_banner", "-encoders"])
    pista = " ".join(SISTEMA.get(platform.system(), {}).get("ffmpeg", ["(instálalo desde ffmpeg.org)"]))
    if r is None or not shutil.which("ffprobe"):
        informe("FFmpeg + FFprobe", False, f"no están en el PATH -> {pista} (o --sistema)")
        return
    x264 = "libx264" in r.stdout
    filtros = correr(["ffmpeg", "-hide_banner", "-filters"])
    ebur = filtros is not None and "ebur128" in filtros.stdout
    informe("FFmpeg + FFprobe", x264 and ebur, "" if x264 and ebur else "falta libx264 o ebur128: instala una compilación completa")
    if x264:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.mp4"
            r = correr(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=30:duration=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(p)])
            informe("codificación H.264", r is not None and r.returncode == 0 and p.exists(), "" if p.exists() else (r.stderr[-200:] if r else ""))


def npm_compartido(comprobar):
    HOME.mkdir(parents=True, exist_ok=True)
    pkg = HOME / "package.json"
    if not pkg.exists():
        pkg.write_text(json.dumps({"name": "motion-studio-herramientas", "private": True, "description": "Herramientas compartidas de Motion Studio"}, indent=2), encoding="utf-8")
    nm = HOME / "node_modules"
    faltan = [p for p in ["playwright", *[f"@fontsource/{f}" for f in FUENTES]] if not (nm / p).exists()]
    if faltan and not comprobar and shutil.which("npm"):
        print(f"  npm install en {HOME}: {len(faltan)} paquetes")
        r = correr(["npm", "install", "--no-audit", "--no-fund", *faltan], cwd=HOME)
        if r and r.returncode:
            print(r.stderr[-800:])
        faltan = [p for p in faltan if not (nm / p).exists()]
    sin_pw = ("no instalado -> python scripts/preparar.py" if comprobar
              else "npm no está en el PATH" if not shutil.which("npm") else "falló `npm install` (ver arriba)")
    informe("Playwright", "playwright" not in faltan, str(HOME) if "playwright" not in faltan else sin_pw)
    fuentes = [f for f in faltan if f.startswith("@fontsource/")]
    informe(f"fuentes ({len(FUENTES)})", not fuentes, "en /node_modules/@fontsource/..." if not fuentes else "faltan: " + ", ".join(fuentes))
    if "playwright" in faltan:
        return False
    # Chromium: `playwright install` es idempotente y rápido si ya está
    if not comprobar:
        r = correr(["npx", "playwright", "install", "chromium"], cwd=HOME)
        if r and r.returncode:
            print(r.stderr[-800:])
    return True


PRUEBA_GPU = r"""
const { chromium } = require('playwright');
(async () => {
  for (const [modo, extra] of [['alto-rendimiento', ['--force_high_performance_gpu']], ['auto', []]]) {
    const angle = process.platform === 'win32' ? ['--use-angle=d3d11'] : [];
    try {
      const b = await chromium.launch({ headless: true, args: [...angle, ...extra, '--enable-gpu', '--ignore-gpu-blocklist'] });
      const p = await b.newPage();
      const r = await p.evaluate(() => { const g = document.createElement('canvas').getContext('webgl2');
        const e = g && g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'sin WebGL2'; });
      await b.close(); console.log(JSON.stringify({ modo, r })); return;
    } catch (e) { console.log(JSON.stringify({ modo, error: String(e.message).split('\n')[0] })); }
  }
})();
"""


def gpu():
    archivo = HOME / "_prueba_gpu.cjs"
    archivo.write_text(PRUEBA_GPU, encoding="utf-8")
    r = correr(["node", str(archivo)], cwd=HOME, timeout=120)
    archivo.unlink(missing_ok=True)
    datos = [json.loads(x) for x in (r.stdout.splitlines() if r else []) if x.startswith("{")]
    ok = next((d for d in datos if "r" in d), None)
    if not ok:
        err = datos[-1].get("error", "") if datos else (r.stderr[-300:] if r else "node no disponible")
        informe("Chromium sin interfaz", False, err + " -> ejecuta sin --comprobar para instalar Chromium")
        return ""
    cpu = re.search(r"SwiftShader|sin WebGL", ok["r"], re.I)
    informe("GPU en Chromium", not cpu, ok["r"][:90] + ("  (render por CPU: muy lento, ver references/gpu.md)" if cpu else ""))
    return ok["r"]


# ── modo edición: perfil del equipo y nivel "completo" ─────────────────────────
# Codificadores H.264 por hardware en orden de preferencia por fabricante; libx264 siempre como respaldo.
CODIFICADORES = ["h264_nvenc", "h264_amf", "h264_qsv", "h264_videotoolbox", "libx264"]
MODELOS = HOME / "modelos" / "whisper"


def ram_gb():
    try:
        if platform.system() == "Windows":
            import ctypes

            class M(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("c", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("libre", ctypes.c_ulonglong),
                            *[(f"x{i}", ctypes.c_ulonglong) for i in range(5)]]
            m = M(); m.l = ctypes.sizeof(M)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.total / 2**30, 1)
        if platform.system() == "Darwin":
            return round(int(correr(["sysctl", "-n", "hw.memsize"]).stdout) / 2**30, 1)
        return round(int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1)) / 2**20, 1)
    except Exception:
        return None


def gpus():
    """[(nombre, vram_gb o None)]. nvidia-smi da la VRAM real; el resto de GPU solo el nombre."""
    lista = []
    r = correr(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    if r and r.returncode == 0:
        for l in r.stdout.strip().splitlines():
            n, _, mb = l.rpartition(",")
            lista.append((n.strip(), round(float(mb) / 1024, 1)))
    if platform.system() == "Windows":
        r = correr(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_VideoController).Name"])
        for n in (r.stdout.splitlines() if r else []):
            if n.strip() and not any(n.strip() in x[0] or x[0] in n.strip() for x in lista):
                lista.append((n.strip(), None))
    elif platform.system() == "Darwin" and platform.machine() == "arm64":
        lista.append(("Apple Silicon (memoria unificada)", ram_gb()))
    return lista


def codificadores():
    """Prueba de verdad cada codificador con 1 s de video: que exista en la lista de FFmpeg no basta."""
    ok = []
    with tempfile.TemporaryDirectory() as d:
        for c in CODIFICADORES:
            p = Path(d) / f"{c}.mp4"
            r = correr(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=1", "-c:v", c,
                        "-pix_fmt", "yuv420p", str(p)], timeout=60)
            if r and r.returncode == 0 and p.exists() and p.stat().st_size > 1000:
                ok.append(c)
    return ok


def whisper_cuda():
    """Rutas de las bibliotecas CUDA instaladas por pip (nvidia-cublas-cu12, nvidia-cudnn-cu12) para que CTranslate2 las cargue."""
    import site
    rutas = []
    for base in [*site.getsitepackages(), site.getusersitepackages()]:
        for sub in ("cublas", "cudnn"):
            for carpeta in ("bin", "lib"):
                p = Path(base) / "nvidia" / sub / carpeta
                if p.exists():
                    rutas.append(str(p))
    return rutas


def perfil_whisper(vram):
    """Modelo y dispositivo según lo instalado y la VRAM. Devuelve lo que se puede usar ya, no lo deseable."""
    try:
        import ctranslate2  # noqa: F401  (lo instala faster-whisper)
        import faster_whisper  # noqa: F401
    except ImportError:
        return {"instalado": False}
    modelos = sorted(p.name for p in MODELOS.glob("*") if (p / "model.bin").exists()) if MODELOS.exists() else []
    disp = "cpu"
    if ctranslate2.get_cuda_device_count() > 0 and modelos:
        rutas = whisper_cuda()
        prueba = ("import os,sys\nfor p in sys.argv[1:]:\n  os.add_dll_directory(p) if hasattr(os,'add_dll_directory') else None\n"
                  "  os.environ['PATH']=p+os.pathsep+os.environ['PATH']\n"
                  "import numpy as np\n")
        # ver una GPU no basta: CTranslate2 necesita cuBLAS y cuDNN, que solo se cargan al transcribir de verdad
        prueba += (f"from faster_whisper import WhisperModel\nm = WhisperModel(r'{MODELOS / modelos[0]}', device='cuda', compute_type='int8_float16')\n"
                   "list(m.transcribe(np.zeros(16000, np.float32))[0])\n")   # transcribe es perezoso: hay que consumirlo
        r = subprocess.run([sys.executable, "-c", prueba, *rutas], capture_output=True, text=True, timeout=300)
        disp = "cuda" if r.returncode == 0 else "cpu"
    preferido = "large-v3-turbo" if (disp == "cuda" and (vram or 0) >= 5) or (disp == "cpu" and "large-v3-turbo" in modelos) else "small"
    return {"instalado": True, "dispositivo": disp, "tipo": "int8_float16" if disp == "cuda" else "int8",
            "modelos": modelos, "modelo": preferido if preferido in modelos else (modelos[-1] if modelos else None),
            "bibliotecasCuda": whisper_cuda()}


def perfil():
    print("Perfil del equipo para el modo edición:")
    gs = gpus()
    vram = max((v for _, v in gs if v), default=None)
    cods = codificadores()
    revision = next((c for c in cods if c != "libx264"), "libx264" if "libx264" in cods else None)
    libre = round(shutil.disk_usage(HOME if HOME.exists() else Path.home()).free / 2**30, 1)
    w = perfil_whisper(vram)
    try:
        import torch  # noqa: F401
        avanzado = True
    except ImportError:
        avanzado = False
    nivel = "avanzado" if avanzado and w.get("modelo") else "completo" if w.get("modelo") else "núcleo"
    p = {"sistema": platform.system(), "arquitectura": platform.machine(), "nucleos": os.cpu_count(), "ramGB": ram_gb(),
         "gpus": [{"nombre": n, "vramGB": v} for n, v in gs], "codificadores": cods, "codificadorRevision": revision,
         "discoLibreGB": libre, "whisper": w, "nivel": nivel,
         # segmentos en paralelo: un codificador por hardware admite pocas sesiones a la vez; x264 ya usa todos los núcleos
         "paralelo": 2 if revision and revision != "libx264" else max(1, (os.cpu_count() or 2) // 4)}
    informe("GPU", bool(gs), ", ".join(f"{n}" + (f" ({v} GB)" if v else "") for n, v in gs) or "ninguna detectada")
    informe("codificadores H.264", bool(cods), ", ".join(cods) + f" -> revisión con {revision}")
    informe("RAM / disco libre", True, f"{p['ramGB']} GB / {libre} GB")
    informe("Whisper (nivel completo)", bool(w.get("modelo")),
            f"{w['modelo']} en {w['dispositivo']} ({w['tipo']})" if w.get("modelo") else
            "no instalado -> python scripts/preparar.py --edicion" if not w.get("instalado") else "sin modelo -> python scripts/preparar.py --edicion")
    print(f"  nivel efectivo: {nivel}")
    return p


def edicion(modelo, gpu_whisper):
    """Instala el nivel completo: faster-whisper (CTranslate2, sin PyTorch) y el modelo en MODELOS/<modelo>."""
    paquetes = ["faster-whisper"] + (["nvidia-cublas-cu12", "nvidia-cudnn-cu12"] if gpu_whisper else [])
    print(f"  pip install --user {' '.join(paquetes)}")
    subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--quiet", *paquetes])
    destino = MODELOS / modelo
    if not (destino / "model.bin").exists():
        print(f"  descargando el modelo {modelo} en {destino} (large-v3-turbo ~1,6 GB, small ~0,5 GB)")
        r = subprocess.run([sys.executable, "-c", "import sys\nfrom faster_whisper.utils import download_model\n"
                            "download_model(sys.argv[1], output_dir=sys.argv[2])", modelo, str(destino)])
        if r.returncode:
            informe(f"modelo {modelo}", False, "falló la descarga (¿sin conexión?)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--comprobar", action="store_true", help="solo verificar, sin instalar nada")
    ap.add_argument("--sistema", action="store_true", help="instalar también Node.js y FFmpeg con winget/brew/apt")
    ap.add_argument("--perfil", action="store_true", help="perfil del equipo para el modo edición")
    ap.add_argument("--edicion", action="store_true", help="instalar el nivel completo del modo edición (faster-whisper y un modelo)")
    ap.add_argument("--modelo", default="large-v3-turbo", help="con --edicion: modelo de Whisper (large-v3-turbo, medium, small...)")
    ap.add_argument("--whisper-gpu", action="store_true", help="con --edicion: bibliotecas CUDA para Whisper en GPU NVIDIA (~1,5 GB)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.edicion and not a.comprobar:
        print("Motion Studio · nivel completo del modo edición")
        edicion(a.modelo, a.whisper_gpu)
    if a.perfil or a.edicion:
        p = perfil()
        HOME.mkdir(parents=True, exist_ok=True)
        estado = json.loads((HOME / "estado.json").read_text(encoding="utf-8")) if (HOME / "estado.json").exists() else {}
        estado["perfil"] = {**p, "fecha": datetime.datetime.now().isoformat(timespec="seconds")}
        (HOME / "estado.json").write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
        faltan = [n for n, ok, _ in resultados if not ok and n != "Whisper (nivel completo)"]
        return 1 if faltan else 0
    print(f"Motion Studio · {'comprobando' if a.comprobar else 'preparando'} herramientas ({platform.system()})")
    python_mods(a.comprobar)
    hay_node = node(a.comprobar, a.sistema)
    ffmpeg(a.comprobar, a.sistema)
    renderer = ""
    if hay_node and npm_compartido(a.comprobar):
        renderer = gpu()
    faltan = [n for n, ok, _ in resultados if not ok]
    estado = {"fecha": datetime.datetime.now().isoformat(timespec="seconds"), "sistema": platform.platform(),
              "herramientas": HOME.as_posix(), "renderer": renderer, "faltan": faltan, "fuentes": FUENTES}
    if HOME.exists():
        (HOME / "estado.json").write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    if faltan:
        print(f"\nFaltan: {', '.join(faltan)}. Sigue las indicaciones de arriba y repite `python scripts/preparar.py`.")
        return 1
    print("\nTodo listo: Motion Studio puede estructurar, revisar y renderizar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
