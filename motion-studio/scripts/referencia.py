"""Mide y reúne imágenes de una referencia local; no descarga ni publica material.

python referencia.py clip.mp4 --url https://fuente-original --salida review/referencias
Salidas: procedencia/huella, FFprobe, estadísticas Y/SAT a 1 fps y hojas temporizadas.
Los números describen el archivo; no califican actuación, montaje ni derechos de uso.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def ejecutar(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)


def analizar(archivo, destino, url=None):
    archivo = Path(archivo).resolve()
    h = hashlib.sha256()
    with archivo.open('rb') as fuente:
        for bloque in iter(lambda: fuente.read(1024 * 1024), b''):
            h.update(bloque)
    huella = h.hexdigest()
    out = Path(destino).resolve() / f'{archivo.stem}-{huella[:12]}'
    out.mkdir(parents=True, exist_ok=True)
    probe = json.loads(ejecutar(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(archivo)]).stdout)
    stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    frames = out / 'frames'
    frames.mkdir(exist_ok=True)
    # Una decodificación para estadísticas y capturas; no se escala el origen para medir.
    r = ejecutar(['ffmpeg', '-hide_banner', '-loglevel', 'info', '-y', '-i', str(archivo),
                  '-vf', 'fps=1:start_time=0,signalstats,metadata=print,scale=240:-1',
                  '-fps_mode', 'passthrough', str(frames / '%05d.jpg')])
    stats = []
    for block in re.split(r'frame:\d+\s+pts:', r.stderr)[1:]:
        tm = re.search(r'pts_time:([\d.]+)', block)
        vals = {k: float(v) for k, v in re.findall(r'lavfi.signalstats\.(YAVG|YLOW|YHIGH|SATAVG)=([\d.]+)', block)}
        if tm and len(vals) == 4:
            stats.append({'t': float(tm.group(1)), **vals})
    files = sorted(frames.glob('*.jpg'))
    if not files or len(stats) != len(files):
        raise ValueError('No se pudieron asociar estadísticas y fotogramas')
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 18)
    except OSError:
        font = ImageFont.load_default(size=18)
    # Hojas de 20 imágenes; mantienen orden, tiempo y relación de aspecto.
    sheets = []
    for start in range(0, len(files), 20):
        chunk = files[start:start + 20]
        with Image.open(chunk[0]) as first:
            w, h = first.size
        sheet = Image.new('RGB', (w * 5, (h + 28) * 4), '#141414')
        draw = ImageDraw.Draw(sheet)
        for i, file in enumerate(chunk):
            x, y = (i % 5) * w, (i // 5) * (h + 28)
            with Image.open(file) as im:
                sheet.paste(im, (x, y))
            draw.text((x + 6, y + h + 2), f'{stats[start + i]["t"]:.1f} s', font=font, fill='white')
        name = f'hoja-{start // 20 + 1:02d}.jpg'
        sheet.save(out / name, quality=90)
        sheets.append(name)
    data = {'version': 1, 'archivo': str(archivo), 'url_original_declarada': url, 'sha256': huella,
            'ancho': stream['width'], 'alto': stream['height'], 'fps': stream['avg_frame_rate'],
            'duracion': float(probe['format']['duration']), 'muestreo_fps': 1,
            'nota': 'Y/SAT de signalstats antes de escalar. La URL es procedencia declarada, no verificación de autoría/licencia.',
            'estadisticas': stats, 'hojas': sheets, 'ffprobe': probe}
    (out / 'referencia.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return out, data


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('video', type=Path)
    ap.add_argument('--url')
    ap.add_argument('--salida', type=Path, default=Path('review/referencias'))
    args = ap.parse_args()
    try:
        out, data = analizar(args.video, args.salida, args.url)
        print(f'OK: {data["duracion"]:.3f} s, {len(data["estadisticas"])} muestras, {len(data["hojas"])} hojas: {out}')
        return 0
    except (OSError, ValueError, StopIteration, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
