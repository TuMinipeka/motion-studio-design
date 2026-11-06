"""Regresión real y pequeña del adaptador. Requiere Blender 5.2/EEVEE y NVIDIA.

python tests/animacion/recursos25d.py [--blender RUTA]
Comprueba rango parcial, caché estable tras diagnóstico y rechazo de GPU/tamaño incorrectos.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--blender', default='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
args = ap.parse_args()


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


with tempfile.TemporaryDirectory(prefix='motion-recursos25d-') as tmp:
    root = Path(tmp).resolve()
    assert root.is_relative_to(Path(tempfile.gettempdir()).resolve())
    (root / 'motion.config.json').write_text(json.dumps({'video': {'ancho': 128, 'alto': 224, 'fps': 30, 'duracion': 1}}), encoding='utf-8')
    gen = root / 'escena.py'
    shutil.copy2(repo / 'motion-studio/assets/ejemplos/25d/escena.py', gen)
    base = [sys.executable, str(repo / 'motion-studio/scripts/recursos25d.py'), '--proyecto', str(root),
            '--generador', str(gen), '--blender', args.blender, '--gpu', 'NVIDIA', '--fps', '12', '--inicio', '0', '--fin', '3']

    def run(cmd, expect=0):
        r = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace', timeout=90)
        assert r.returncode == expect, r.stdout + r.stderr
        return r.stdout + r.stderr

    run(base)
    manifest_file = root / 'escena.recurso.json'
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    out = root / Path(manifest['ruta']).parent
    hashes = {f.name: sha(f) for f in out.glob('f*.png')}
    manifest_sha = sha(manifest_file)
    signature = lambda: subprocess.run(['node', '--input-type=module', '-e',
        'import {huellaProyecto} from ' + json.dumps((repo / 'motion-studio/assets/plantilla/cache.mjs').as_uri()) +
        '; console.log(huellaProyecto(' + json.dumps(str(root)) + '));'], capture_output=True, text=True, check=True).stdout.strip()
    before = signature()
    log = run(base + ['--solo=1,2', '--forzar', '--comprobar'])
    assert '3 recursos, 1 generados' in log
    assert sha(manifest_file) == manifest_sha
    assert all(sha(out / name) == value for name, value in hashes.items())
    assert signature() == before, 'El diagnóstico o metadatos volátiles invalidaron la imagen'
    reports = list((root / 'review/recursos25d').glob('*.resultado.json'))
    assert reports and json.loads(reports[0].read_text(encoding='utf-8'))['diferencias'] == []
    bad_gpu = base.copy(); bad_gpu[bad_gpu.index('NVIDIA')] = 'GPU_INEXISTENTE'
    assert 'GPU inesperada' in run(bad_gpu, 1)
    assert sha(manifest_file) == manifest_sha
    # El generador cambia dimensiones durante seek: debe rechazarse después del render.
    gen.write_text(gen.read_text(encoding='utf-8') + '\n_original_seek = seek\ndef seek(t):\n    _original_seek(t)\n    sc.render.resolution_x = 16\n', encoding='utf-8')
    bad_size = base.copy(); bad_size[-1] = '1'
    assert 'dimensiones de salida incorrectas' in run(bad_size, 1)
    assert sha(manifest_file) == manifest_sha
    print('OK: --solo conserva alcance/PNG, comprobación no invalida caché, GPU y dimensiones incorrectas rechazadas')
