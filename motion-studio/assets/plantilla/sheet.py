"""Hoja de contacto: un fotograma por pulso (review/beats/*.jpg) -> review/sheets/sheet_XX.jpg.

Primero: node render.mjs --sheet      Después: python sheet.py     (necesita Pillow: pip install pillow)
Cada fila es un compás; cada hoja reúne 8 compases. El pulso y su tiempo van escritos sobre cada cuadro.
"""
import glob
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "review", "beats")
OUT = os.path.join(ROOT, "review", "sheets")
CFG = json.load(open(os.path.join(ROOT, "motion.config.json"), encoding="utf-8"))
BJ = json.load(open(os.path.join(ROOT, "beats.json"), encoding="utf-8"))
beats = BJ["beats"]
cols = BJ.get("beatsPerBar", 4)
BARS_PER_SHEET = 8
desfase = CFG.get("revision", {}).get("desfase", 0.2)

files = sorted(glob.glob(os.path.join(SRC, "*.jpg")))
if not files:
    raise SystemExit("No hay fotogramas en review/beats. Ejecuta antes: node render.mjs --sheet")


def fuente(tam):
    for nombre in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(nombre, tam)
        except OSError:
            continue
    return ImageFont.load_default()


TW = 480
ancho, alto = Image.open(files[0]).size
TH = round(TW * alto / ancho)
LAB = 30
font = fuente(22)
os.makedirs(OUT, exist_ok=True)
por_hoja = cols * BARS_PER_SHEET
for s in range((len(files) + por_hoja - 1) // por_hoja):
    grupo = files[s * por_hoja:(s + 1) * por_hoja]
    filas = (len(grupo) + cols - 1) // cols
    img = Image.new("RGB", (cols * TW + 90, filas * (TH + LAB)), (20, 20, 20))
    d = ImageDraw.Draw(img)
    for k, f in enumerate(grupo):
        i = s * por_hoja + k
        r, c = divmod(k, cols)
        img.paste(Image.open(f).resize((TW, TH), Image.LANCZOS), (90 + c * TW, r * (TH + LAB) + LAB))
        d.text((90 + c * TW + 6, r * (TH + LAB) + 4), f"pulso {i + 1}  t={beats[i] + desfase:.2f}s", fill=(230, 230, 230), font=font)
        if c == 0:
            d.text((8, r * (TH + LAB) + LAB + TH // 2 - 12), f"c{i // cols + 1}", fill=(230, 230, 230), font=font)
    destino = os.path.join(OUT, f"sheet_{s + 1:02d}.jpg")
    img.save(destino, quality=88)
    print(destino)
