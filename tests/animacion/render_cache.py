"""Regresión real: reanudar, invalidar fuentes y abortar un encoder fallido sin EPIPE/hang."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='motion-cache-render-') as tmp:
    root = Path(tmp)
    for name in ('render.mjs', 'cache.mjs'):
        shutil.copy2(repo / 'motion-studio/assets/plantilla' / name, root / name)
    cfg = {'video': {'ancho': 128, 'alto': 64, 'fps': 8, 'duracion': 1}, 'workers': 1,
           'salida': {'carpeta': 'exportaciones', 'nombre': 'prueba'}}
    config = root / 'motion.config.json'
    config.write_text(json.dumps(cfg), encoding='utf-8')
    index = root / 'index.html'
    html = '''<!doctype html><style>html,body{margin:0;overflow:hidden}</style><canvas width="128" height="64"></canvas>
<script>const ctx=document.querySelector('canvas').getContext('2d');window.seek=t=>{ctx.reset();ctx.fillStyle='COLOR';ctx.fillRect(0,0,128,64);};window.seek(0);window.ready=true;</script>'''
    index.write_text(html.replace('COLOR', '#ff0000'), encoding='utf-8')

    def run(expect=0):
        r = subprocess.run(['node', 'render.mjs', '--final'], cwd=root, capture_output=True, text=True, timeout=30)
        out = r.stdout + r.stderr
        assert r.returncode == expect, out
        return out

    assert 'segmentos 0/1' in run()
    before = (root / 'exportaciones/prueba.mp4').read_bytes()
    assert 'segmentos 1/1' in run()
    index.write_text(html.replace('COLOR', '#0000ff'), encoding='utf-8')
    assert 'segmentos 0/1' in run()
    assert before != (root / 'exportaciones/prueba.mp4').read_bytes()
    cfg['codificacion'] = {'final': {'preset': 'preset_inexistente', 'crf': 12}}
    config.write_text(json.dumps(cfg), encoding='utf-8')
    failed = run(1)
    assert 'FFmpeg falló en el segmento' in failed, failed
    assert 'Unhandled' not in failed and 'throw er;' not in failed, failed
    del cfg['codificacion']
    config.write_text(json.dumps(cfg), encoding='utf-8')
    assert 'segmentos 1/1' in run()
    print('OK: caché reutilizada, fuente modificada invalidada, encoder fallido abortado y caché anterior conservada')
