"""Regresión real del render SDR. Requiere Node, Playwright, FFmpeg y numpy de la skill.

Uso: python tests/animacion/color_sdr.py
Genera una carta sintética de 1 s; no renderiza un proyecto del usuario.
"""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import numpy as np

REPO = Path(__file__).resolve().parents[2]
COLORES = [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0),
           (0, 0, 255), (64, 64, 64), (128, 128, 128), (192, 192, 192)]


def ejecutar(*args, cwd=None):
    r = subprocess.run(list(map(str, args)), cwd=cwd, capture_output=True, timeout=120)
    if r.returncode:
        raise RuntimeError((r.stdout + r.stderr).decode('utf-8', errors='replace'))
    return r.stdout


with tempfile.TemporaryDirectory(prefix='motion-color-sdr-') as carpeta:
    proyecto = Path(carpeta)
    shutil.copy2(REPO / 'motion-studio/assets/plantilla/render.mjs', proyecto / 'render.mjs')
    config = dict(video=dict(ancho=256, alto=64, fps=4, duracion=1), workers=1,
                  salida=dict(carpeta='exportaciones', nombre='carta'))
    (proyecto / 'motion.config.json').write_text(json.dumps(config), encoding='utf-8')
    (proyecto / 'index.html').write_text('''<!doctype html><style>
html,body{margin:0;overflow:hidden}canvas{display:block}</style><canvas width="256" height="64"></canvas>
<script>const c=document.querySelector('canvas'),x=c.getContext('2d');
const colores=''' + json.dumps(COLORES) + ''';
window.seek=t=>{x.reset();colores.forEach((v,i)=>{x.fillStyle=`rgb(${v.join(',')})`;x.fillRect(i*32,0,32,64);});};
window.seek(0);window.ready=true;</script>''', encoding='utf-8')
    for modo, nombre in [('--prueba=0,1', 'review/pruebas/movimiento-0-4.mp4'),
                         ('--borrador', 'exportaciones/carta_borrador.mp4'),
                         ('--final', 'exportaciones/carta.mp4')]:
        ejecutar('node', proyecto / 'render.mjs', modo, '--workers=1', cwd=proyecto)
        video = proyecto / nombre
        datos = json.loads(ejecutar('ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                                   '-show_streams', '-of', 'json', video))['streams'][0]
        assert all(datos.get(k) == 'bt709' for k in ('color_space', 'color_transfer', 'color_primaries')), datos
        assert datos.get('color_range') == 'tv' and datos['pix_fmt'] == 'yuv420p', datos
        assert datos['nb_read_frames'] == '4' and datos['r_frame_rate'] == '4/1', datos
        raw = ejecutar('ffmpeg', '-v', 'error', '-i', video, '-frames:v', '1', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-')
        imagen = np.frombuffer(raw, np.uint8).reshape(64, 256, 3)
        errores = [float(np.max(np.abs(imagen[24:40, i*32+8:i*32+24].mean(axis=(0, 1)) - color)))
                   for i, color in enumerate(COLORES)]
        assert max(errores) <= 5, (modo, errores)
        yuv = ejecutar('ffmpeg', '-v', 'error', '-i', video, '-frames:v', '1', '-pix_fmt', 'yuv420p', '-f', 'rawvideo', '-')
        luma = np.frombuffer(yuv, np.uint8)[:256*64].reshape(64, 256)
        # Negro/blanco limitados y verde con matriz 709: no basta etiquetar una conversión 601.
        assert abs(int(luma[32, 16]) - 16) <= 2
        assert abs(int(luma[32, 48]) - 235) <= 2
        assert abs(int(luma[32, 112]) - 173) <= 2
        print(f'OK {modo}: BT.709/tv, 4 fotogramas, error RGB máximo {max(errores):.1f}/255')
