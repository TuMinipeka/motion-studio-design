#!/usr/bin/env python3
"""Crea la carpeta de un video nuevo desde la plantilla de Motion Studio y configura la GPU.

    python nuevo.py <carpeta> [--nombre NOMBRE] [--gpu "texto del nombre"] [--duracion S] [--fps N] [--vertical]
                    [--sin-preparar] [--listar-gpus]

- Copia assets/plantilla/ a <carpeta> (no pisa nada: si <carpeta> ya existe y no esta vacia, se detiene).
- Detecta las GPU del equipo (Windows) y escribe la elegida en <carpeta>/motion.config.json.
  Si hay varias y no usas --gpu, elige la dedicada (NVIDIA > Radeon RX/Arc) y te lo dice: confirmalo con el usuario.
- Escribe la duracion, los fps y la orientacion del brief (--vertical = 1080x1920) en motion.config.json.
- Ejecuta preparar.py: instala lo que falte a nivel de usuario (Playwright, Chromium, fuentes, numpy, Pillow) en las
  herramientas compartidas y comprueba Node, FFmpeg y la GPU. Con --sin-preparar solo comprueba, sin instalar.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLANTILLA = Path(__file__).resolve().parent.parent / "assets" / "plantilla"
# (patron del nombre, texto para `gpu.coincidir`, prioridad: menor = mas probable que sea la dedicada)
MARCAS = [(r"NVIDIA|GeForce|RTX|GTX", "NVIDIA", 0), (r"Radeon RX|Radeon Pro|\bRX \d", "Radeon", 1), (r"Intel.*Arc|\bArc\b", "Arc", 2),
          (r"AMD|Radeon", "AMD|Radeon", 3), (r"Intel", "Intel", 4)]


def listar_gpus():
    if sys.platform != "win32":
        return []
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [n.strip() for n in r.stdout.splitlines() if n.strip() and "Basic Render" not in n]


def clasificar(nombre):
    for patron, coincidir, prio in MARCAS:
        if re.search(patron, nombre, re.I):
            return coincidir, prio
    return "", 9


def elegir(gpus, preferida):
    """Devuelve (nombre, coincidir, modo)."""
    if preferida:
        for n in gpus:
            if preferida.lower() in n.lower():
                return n, clasificar(n)[0], "alto-rendimiento"
        # nombre dado por el usuario que no esta en la lista detectada: se respeta tal cual
        return preferida, clasificar(preferida)[0], "alto-rendimiento"
    if not gpus:
        return "", "", "auto"
    if len(gpus) == 1:
        return gpus[0], clasificar(gpus[0])[0], "auto"
    mejor = min(gpus, key=lambda n: clasificar(n)[1])
    return mejor, clasificar(mejor)[0], "alto-rendimiento"


def preparar(instalar):
    """Herramientas compartidas (Playwright, Chromium, fuentes, numpy, Pillow) y comprobación de Node, FFmpeg y GPU.
    Delegado en preparar.py para que haya una sola definición de lo que necesita la skill."""
    cmd = [sys.executable, str(Path(__file__).resolve().parent / "preparar.py")] + ([] if instalar else ["--comprobar"])
    sys.stdout.flush()   # que el resumen del proyecto salga antes que el informe de herramientas
    return subprocess.run(cmd).returncode == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta", nargs="?")
    ap.add_argument("--nombre", help="nombre del archivo de salida (por defecto, el de la carpeta)")
    ap.add_argument("--gpu", help="parte del nombre de la GPU a usar, p. ej. \"RTX 3050\"")
    ap.add_argument("--duracion", type=float, help="segundos del video (la plantilla trae un ejemplo)")
    ap.add_argument("--fps", type=int, help="fotogramas por segundo, p. ej. 30 o 60")
    ap.add_argument("--vertical", action="store_true", help="1080x1920 (shorts, reels) en lugar de 1920x1080")
    ap.add_argument("--sin-preparar", action="store_true", help="no instalar herramientas que falten; solo comprobarlas")
    ap.add_argument("--listar-gpus", action="store_true")
    a = ap.parse_args()

    gpus = listar_gpus()
    if a.listar_gpus or not a.carpeta:
        print("\n".join(gpus) if gpus else "No se detectaron GPU (o el sistema no es Windows): configura gpu.* a mano.")
        return 0

    destino = Path(a.carpeta).resolve()
    if destino.exists() and any(destino.iterdir()):
        print(f"ERROR: {destino} ya existe y no esta vacia; no se sobrescribe nada.", file=sys.stderr)
        return 1
    shutil.copytree(PLANTILLA, destino, dirs_exist_ok=True)

    nombre_gpu, coincidir, modo = elegir(gpus, a.gpu)
    ruta = destino / "motion.config.json"
    cfg = json.loads(ruta.read_text(encoding="utf-8"))
    cfg["gpu"].update({"modo": modo, "coincidir": coincidir, "nombre": nombre_gpu})
    cfg["salida"]["nombre"] = a.nombre or re.sub(r"[^A-Za-z0-9_-]+", "-", destino.name).strip("-") or "video"
    if a.duracion:
        cfg["video"]["duracion"] = a.duracion
    if a.fps:
        cfg["video"]["fps"] = a.fps
    if a.vertical:
        cfg["video"]["ancho"], cfg["video"]["alto"] = 1080, 1920
    ruta.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Proyecto creado: {destino}")
    print(f"GPU detectadas: {', '.join(gpus) if gpus else 'ninguna'}")
    print(f"GPU configurada: {nombre_gpu or '(automatica)'}  modo={modo}")
    v = cfg["video"]
    print(f"Video: {v['ancho']}x{v['alto']} · {v['fps']} fps · {v['duracion']} s"
          + ("" if a.duracion else "  (duracion de ejemplo: ajustala al brief con --duracion o en motion.config.json)"))
    if len(gpus) > 1 and not a.gpu:
        print("AVISO: hay varias GPU; se eligio la dedicada. Confirma con el usuario y cambia motion.config.json si no es la que quiere.")
    print()
    if not preparar(instalar=not a.sin_preparar):
        print("AVISO: faltan herramientas (ver arriba). El proyecto está creado, pero no se podrá renderizar hasta resolverlo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
