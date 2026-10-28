#!/usr/bin/env python3
"""Crea la carpeta de un video nuevo desde la plantilla de Motion Studio y configura la GPU.

    python nuevo.py <carpeta> [--nombre NOMBRE] [--gpu "texto del nombre"] [--listar-gpus]

- Copia assets/plantilla/ a <carpeta> (no pisa nada: si <carpeta> ya existe y no esta vacia, se detiene).
- Detecta las GPU del equipo (Windows) y escribe la elegida en <carpeta>/motion.config.json.
  Si hay varias y no usas --gpu, elige la dedicada (NVIDIA > Radeon RX/Arc) y te lo dice: confirmalo con el usuario.
- Comprueba que Playwright, FFmpeg y Pillow estan disponibles y avisa de lo que falte.
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


def comprobar_entorno(destino):
    avisos = []
    for exe in ("node", "ffmpeg", "ffprobe"):
        if not shutil.which(exe):
            avisos.append(f"falta `{exe}` en el PATH")
    if not any((d / "node_modules" / "playwright").exists() for d in [destino, *destino.parents]):
        avisos.append("falta Playwright: en la carpeta del proyecto o en una superior ejecuta `npm i playwright` y `npx playwright install chromium`")
    try:
        import PIL  # noqa: F401
    except ImportError:
        avisos.append("falta Pillow para sheet.py: `pip install pillow`")
    return avisos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta", nargs="?")
    ap.add_argument("--nombre", help="nombre del archivo de salida (por defecto, el de la carpeta)")
    ap.add_argument("--gpu", help="parte del nombre de la GPU a usar, p. ej. \"RTX 3050\"")
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
    ruta.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Proyecto creado: {destino}")
    print(f"GPU detectadas: {', '.join(gpus) if gpus else 'ninguna'}")
    print(f"GPU configurada: {nombre_gpu or '(automatica)'}  modo={modo}")
    if len(gpus) > 1 and not a.gpu:
        print("AVISO: hay varias GPU; se eligio la dedicada. Confirma con el usuario y cambia motion.config.json si no es la que quiere.")
    for av in comprobar_entorno(destino):
        print("AVISO:", av)
    return 0


if __name__ == "__main__":
    sys.exit(main())
