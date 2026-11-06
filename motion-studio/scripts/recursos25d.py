"""Genera recursos PNG de Blender para componer con seek(t); no exporta videos.

python recursos25d.py --proyecto P --generador P/escena.py --blender RUTA
    --gpu NVIDIA --fps 12 --inicio 0 --fin 72 [--fuente dependencia.py]

El generador construye una escena y expone seek(t), que fija la pose completa.
Lee MOTION_CONFIG (ancho, alto, fps) mediante runpy. Cada fuente declarada entra en la
huella. Caché por huella, revisión de tamaño y manifiesto de recursos, sin borrar renders.
Blender es opcional: Motion Studio sigue exportando con render.mjs.
"""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageChops


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--proyecto', type=Path, required=True)
    ap.add_argument('--generador', type=Path, required=True)
    ap.add_argument('--blender', type=Path, required=True)
    ap.add_argument('--gpu', required=True, help='texto exigido en el nombre real del dispositivo, p. ej. NVIDIA')
    ap.add_argument('--fps', type=float, default=12, help='cadencia del recurso; no cambia fps de entrega')
    ap.add_argument('--inicio', type=int, default=0)
    ap.add_argument('--fin', type=int, required=True, help='exclusivo, a la cadencia del recurso')
    ap.add_argument('--fuente', type=Path, action='append', default=[])
    ap.add_argument('--solo', help='rango de dibujos a generar, A,B; no cambia el alcance inicio/fin del recurso')
    ap.add_argument('--forzar', action='store_true', help='regenerar los dibujos seleccionados aunque estén válidos')
    ap.add_argument('--comprobar', action='store_true', help='repite primero/medio/último en orden inverso y compara píxeles')
    args = ap.parse_args()
    try:
        if not math.isfinite(args.fps) or args.fps <= 0 or args.inicio < 0 or args.fin <= args.inicio:
            raise ValueError('FPS o rango inválidos')
        seleccionados = set(range(args.inicio, args.fin))
        if args.solo:
            rango = [int(x) for x in args.solo.split(',')]
            if len(rango) != 2 or not args.inicio <= rango[0] < rango[1] <= args.fin:
                raise ValueError('--solo=A,B debe estar dentro del alcance inicio/fin')
            seleccionados = set(range(*rango))
        root, gen = args.proyecto.resolve(), args.generador.resolve()
        cfg = json.loads((root / 'motion.config.json').read_text(encoding='utf-8-sig'))
        h = hashlib.sha256()
        fuentes = [gen, Path(__file__).with_name('recursos25d_blender.py').resolve(), *[p.resolve() for p in args.fuente]]
        for f in fuentes:
            h.update(f.name.encode()); h.update(b'\0'); h.update(f.read_bytes())
        params = {'ancho': cfg['video']['ancho'], 'alto': cfg['video']['alto'], 'fps': args.fps,
                  'gpu': args.gpu, 'blender': str(args.blender.resolve())}
        version = subprocess.run([str(args.blender), '--version'], capture_output=True, text=True, check=True).stdout.splitlines()[0]
        h.update(json.dumps(params, sort_keys=True).encode()); h.update(version.encode())
        out = root / 'recursos' / (gen.stem + '-' + h.hexdigest()[:12])
        out.mkdir(parents=True, exist_ok=True)
        faltan = []
        for f in range(args.inicio, args.fin):
            file = out / f'f{f:04d}.png'
            try:
                with Image.open(file) as im:
                    if im.size != (params['ancho'], params['alto']):
                        raise ValueError('tamaño')
                    im.verify()
            except (OSError, ValueError):
                if f not in seleccionados:
                    raise ValueError(f'Falta f{f:04d} fuera de --solo; genera primero todo el recurso de esta huella')
                faltan.append(f)
        if args.forzar:
            faltan = sorted(set(faltan) | seleccionados)
        seleccion = sorted(set([args.inicio, (args.inicio + args.fin - 1) // 2, args.fin - 1]), reverse=True)
        job = {**params, 'generador': str(gen), 'salida': str(out), 'frames': faltan,
               'comprobar': seleccion if args.comprobar else [], 'version_blender': version}
        ruta_job = root / 'review' / 'recursos25d' / (out.name + '.json')
        ruta_job.parent.mkdir(parents=True, exist_ok=True)
        job['informe'] = str(ruta_job.with_suffix('.resultado.json'))
        job['comprobar_salida'] = str(ruta_job.parent / out.name)
        Path(job['comprobar_salida']).mkdir(exist_ok=True)
        ruta_job.write_text(json.dumps(job, indent=2), encoding='utf-8')
        runner = Path(__file__).with_name('recursos25d_blender.py')
        if faltan or args.comprobar:
            # EEVEE/OpenGL: se comprueba el dispositivo real en el proceso, antes de generar.
            subprocess.run([str(args.blender), '-b', '--factory-startup', '--gpu-backend', 'opengl',
                            '--python-exit-code', '1', '-P', str(runner), '--', str(ruta_job)], check=True)
        for f in range(args.inicio, args.fin):
            with Image.open(out / f'f{f:04d}.png') as im:
                if im.size != (params['ancho'], params['alto']):
                    raise ValueError(f'f{f:04d}: dimensiones de salida incorrectas {im.size}')
                im.verify()
        resultado = json.loads(Path(job['informe']).read_text(encoding='utf-8'))
        diferencias = []
        if args.comprobar:
            for f in seleccion:
                with Image.open(out / f'f{f:04d}.png') as a, Image.open(Path(job['comprobar_salida']) / f'check-{f:04d}.png') as b:
                    hist = ImageChops.difference(a.convert('RGBA'), b.convert('RGBA')).histogram()
                    count = sum(hist) - sum(hist[::256])
                    if count:
                        diferencias.append({'fotograma': f, 'canales_distintos': count})
            resultado['diferencias'] = diferencias
            Path(job['informe']).write_text(json.dumps(resultado, indent=2), encoding='utf-8')
        manifest = {**params, 'ruta': str(out.relative_to(root)).replace('\\', '/') + '/f',
                    'primero': args.inicio, 'cantidad': args.fin - args.inicio, 'digitos': 4,
                    'fuentes': [str(f) for f in fuentes], 'huella': h.hexdigest(),
                    'dispositivo': resultado['dispositivo'], 'version_blender': version}
        (out / 'recurso.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (root / (gen.stem + '.recurso.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'OK: {manifest["cantidad"]} recursos, {len(faltan)} generados; {out / "recurso.json"}')
        if diferencias:
            print(f'AVISO: generador con diferencias al repetir instantes; ver {job["informe"]}')
            return 1
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
