"""Auxiliar ejecutado por Blender. Entrada: JSON de recursos25d.py."""
import json
import os
import runpy
import sys
import time
from pathlib import Path

import bpy
import gpu

job = json.loads(Path(sys.argv[sys.argv.index('--') + 1]).read_text(encoding='utf-8'))
out = Path(job['salida'])
gpu.init()
device = gpu.platform.renderer_get()
print('MOTION_DEVICE:', device, flush=True)
if job['gpu'].lower() not in device.lower():
    raise RuntimeError(f'GPU inesperada: {device}; se exige {job["gpu"]}')
t0 = time.perf_counter()
bpy.ops.wm.read_factory_settings(use_empty=True)
sys.path.insert(0, str(Path(job['generador']).parent))
module = runpy.run_path(job['generador'], init_globals={'MOTION_CONFIG': job})
seek = module.get('seek')
if not callable(seek):
    raise RuntimeError('El generador debe exponer seek(t)')
sc = bpy.context.scene
if sc.render.engine != 'BLENDER_EEVEE':
    raise RuntimeError('Este adaptador comprueba EEVEE/OpenGL; otro motor requiere su propia verificación')
sc.render.resolution_x, sc.render.resolution_y = job['ancho'], job['alto']
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.film_transparent = bool(module.get('TRANSPARENTE', False))
# Blender escribe estos campos en PNG aunque no estén estampados sobre la imagen.
# La hora real/coste no forman parte del recurso visual ni deben romper su caché.
for prop in ('use_stamp_date', 'use_stamp_render_time', 'use_stamp_memory', 'use_stamp_hostname'):
    if hasattr(sc.render, prop):
        setattr(sc.render, prop, False)


def render(f, file):
    seek(f / job['fps'])
    bpy.context.view_layer.update()
    sc.render.filepath = str(file)
    bpy.ops.render.render(write_still=True)


for f in job['frames']:
    file = out / f'f{f:04d}.png'
    partial = out / f'f{f:04d}.part.png'
    render(f, partial)
    os.replace(partial, file)

# Solo genera repeticiones; Python/Pillow compara bytes fuera de Blender sin tuplas de floats.
for f in job['comprobar']:
    repeat = Path(job['comprobar_salida']) / f'check-{f:04d}.png'
    render(f, repeat)
result = {'dispositivo': device, 'version_blender': job['version_blender'],
          'segundos_ultima_ejecucion': time.perf_counter() - t0, 'generados_ultima_ejecucion': len(job['frames']),
          'comprobados_orden_inverso': job['comprobar']}
Path(job['informe']).write_text(json.dumps(result, indent=2), encoding='utf-8')
print('MOTION_RESULT:', json.dumps(result), flush=True)
