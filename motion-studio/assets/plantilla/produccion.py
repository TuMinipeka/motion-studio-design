"""Plan de planos/impactos y voz real -> sincro.json, SRT y muestra por plano.

python produccion.py [--plan produccion.json] [--voz tiempos.json] [--capturar]
python produccion.py --transcribir audio/voz.wav [--idioma es] [--modelo small]

La captura es opcional y requiere el alcance de render autorizado de la skill.
Los fotogramas son enteros absolutos, base cero, intervalos [inicio, fin).
"""
import argparse
import json
import math
import subprocess
from pathlib import Path


def numero(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def entero(x):
    return isinstance(x, int) and not isinstance(x, bool)


def leer_palabras(datos):
    """Whisper/faster-whisper, make-short o words; conserva tiempos y orden originales."""
    if 'segments' in datos:
        entradas = [w for s in datos['segments'] for w in s.get('words', [])]
    elif 'lines' in datos:
        entradas = [w for s in datos['lines'] for w in s.get('words', [])]
    else:
        entradas = datos.get('words', [])
    if not entradas:
        raise ValueError('La voz no contiene marcas por palabra; no se estiman desde el texto')
    salida = []
    for w in entradas:
        texto = w.get('word', w.get('w', '')).strip()
        a, b = w.get('start'), w.get('end')
        if not texto or not numero(a) or not numero(b) or a < 0 or b <= a:
            raise ValueError(f'Palabra o tiempos inválidos: {w}')
        if salida and a < salida[-1]['start']:
            raise ValueError('Marcas de voz fuera de orden')
        salida.append({'word': texto, 'start': a, 'end': b})
    return salida


def preparar(plan, cfg, palabras=None):
    fps, dur = cfg['video']['fps'], cfg['video']['duracion']
    if not numero(fps) or fps <= 0 or not numero(dur) or dur <= 0:
        raise ValueError('FPS y duración deben ser positivos')
    n = round(fps * dur)
    if abs(n - fps * dur) > 1e-6:
        raise ValueError('La duración debe contener un número entero de fotogramas')
    planos = plan.get('planos', [])
    if plan.get('version') != 1 or not planos:
        raise ValueError('Se requiere version: 1 y planos no vacíos')
    palabras = palabras or []
    if any(w['end'] > dur + 1e-6 for w in palabras):
        raise ValueError('La voz supera la duración del proyecto; ajusta el brief antes de animar')
    previo, ids, eventos, muestras = 0, set(), [], set()
    for p in planos:
        pid, a, b = p.get('id'), p.get('inicio'), p.get('fin')
        if not isinstance(pid, str) or not pid or pid in ids:
            raise ValueError('Identificador de plano vacío o duplicado')
        ids.add(pid)
        if not entero(a) or not entero(b) or a != previo or b <= a or b > n:
            raise ValueError(f'{pid}: hueco, solape o intervalo inválido [{a}, {b})')
        previo = b
        muestras.update((a, (a + b - 1) // 2, b - 1))
        for f in p.get('muestras', []):
            if not entero(f) or not a <= f < b:
                raise ValueError(f'{pid}: muestra fuera del plano')
            muestras.add(f)
        for e in p.get('impactos', []):
            eid = e.get('id')
            if not isinstance(eid, str) or not eid or any(x['id'] == eid for x in eventos):
                raise ValueError(f'{pid}: impacto vacío o duplicado')
            if ('fotograma' in e) == ('palabra' in e):
                raise ValueError(f'{eid}: usa fotograma O índice de palabra')
            if 'palabra' in e:
                i, desfase = e['palabra'], e.get('desfase', 0)
                if not entero(i) or not 0 <= i < len(palabras) or not numero(desfase):
                    raise ValueError(f'{eid}: palabra o desfase inválido')
                f = math.floor((palabras[i]['start'] + desfase) * fps + 0.5)
            else:
                f = e['fotograma']
            if not entero(f) or not a <= f < b:
                raise ValueError(f'{eid}: impacto fuera del plano {pid}')
            efecto, ganancia = e.get('efecto'), e.get('ganancia', 0.5)
            if efecto not in (None, 'tic', 'impacto') or not numero(ganancia) or not 0 <= ganancia <= 1:
                raise ValueError(f'{eid}: efecto/ganancia inválidos')
            eventos.append({'id': eid, 'plano': pid, 'fotograma': f, 't': f / fps,
                            'efecto': efecto, 'ganancia': ganancia})
            muestras.add(f)
    if previo != n:
        raise ValueError(f'Los planos terminan en {previo}; el proyecto requiere {n}')
    # No cruza cortes ni mantiene una palabra más allá de la siguiente o de 0,9 s.
    caps = []
    for i, w in enumerate(palabras):
        corte = next(p['fin'] / fps for p in planos if p['inicio'] / fps <= w['start'] < p['fin'] / fps)
        fin = min(w['end'] + 0.12, w['start'] + 0.9, corte,
                  palabras[i + 1]['start'] if i + 1 < len(palabras) else dur)
        if fin > w['start']:
            caps.append({'texto': w['word'], 'inicio': w['start'], 'fin': fin})
    return {'version': 1, 'fps': fps, 'fotogramas': n, 'planos': planos,
            'impactos': sorted(eventos, key=lambda x: x['fotograma']), 'subtitulos': caps,
            'muestras': sorted(muestras)}


def srt(caps):
    def tiempo(t):
        ms = round(t * 1000)
        return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'
    return '\n\n'.join(f'{i}\n{tiempo(c["inicio"])} --> {tiempo(c["fin"])}\n{c["texto"]}'
                       for i, c in enumerate(caps, 1)) + '\n'


def hoja_revision(root, datos):
    from PIL import Image, ImageDraw, ImageFont
    out = root / 'review' / 'produccion'
    out.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 18)
    except OSError:
        font = ImageFont.load_default(size=18)
    items, fallos = [], []
    for f in datos['muestras']:
        t = f / datos['fps']
        file = root / 'review' / 'frames' / f't{t:06.2f}.png'
        p = next(p for p in datos['planos'] if p['inicio'] <= f < p['fin'])
        r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(file), '-vf', 'signalstats,metadata=print',
                            '-frames:v', '1', '-f', 'null', '-'], capture_output=True, text=True, check=True)
        import re
        stats = {k: float(v) for k, v in re.findall(r'lavfi.signalstats\.(YAVG|SATAVG)=([\d.]+)', r.stderr)}
        fuera = []
        for nombre, limites in p.get('bandas', {}).items():
            if nombre not in stats or not isinstance(limites, list) or len(limites) != 2:
                raise ValueError(f'{p["id"]}: banda desconocida o inválida')
            if not all(numero(x) for x in limites) or limites[0] > limites[1]:
                raise ValueError(f'{p["id"]}: límites de banda inválidos')
            if not limites[0] <= stats[nombre] <= limites[1]:
                fuera.append(nombre)
        items.append({'plano': p['id'], 'fotograma': f, 'archivo': str(file), **stats, 'fuera_de_banda': fuera})
        fallos.extend(f'{p["id"]} f{f}: {v}' for v in fuera)
    for start in range(0, len(items), 20):
        chunk = items[start:start + 20]
        with Image.open(chunk[0]['archivo']) as im:
            w, h = 216, round(im.height * 216 / im.width)
        sheet = Image.new('RGB', (w * 5, (h + 28) * 4), '#141414')
        draw = ImageDraw.Draw(sheet)
        for i, it in enumerate(chunk):
            x, y = i % 5 * w, i // 5 * (h + 28)
            with Image.open(it['archivo']) as im:
                sheet.paste(im.convert('RGB').resize((w, h)), (x, y))
            draw.text((x + 4, y + h + 2), f'{it["plano"]} f{it["fotograma"]}', font=font, fill='white')
        sheet.save(out / f'hoja-{start // 20 + 1:02d}.jpg', quality=92)
    informe = {'nota': 'Muestras declaradas, no inspección continua. Bandas opcionales de signalstats no juzgan calidad.',
               'muestras': items, 'avisos': fallos}
    (out / 'revision.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for aviso in fallos:
        print('AVISO de color:', aviso)
    print(f'Hoja y mediciones: {out}; lectura visual y reproducción pendientes')


def transcribir(ruta, modelo, idioma):
    # FFmpeg -> ndarray evita diferencias entre versiones de PyAV y conserva 16 kHz.
    import numpy as np
    from faster_whisper import WhisperModel
    audio = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(ruta), '-ac', '1', '-ar', '16000',
                            '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    m = WhisperModel(modelo, device='cpu', compute_type='int8')
    segments, _ = m.transcribe(np.frombuffer(audio, dtype='<f4'), language=idioma,
                              word_timestamps=True, vad_filter=True)
    words = [{'word': w.word.strip(), 'start': w.start, 'end': w.end}
             for seg in segments for w in (seg.words or []) if w.word.strip()]
    if not words:
        raise ValueError('No se reconocieron palabras; revisar el audio')
    return {'fuente': str(ruta), 'modelo': modelo, 'words': words}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan', default='produccion.json')
    ap.add_argument('--voz', help='JSON con marcas por palabra ya revisadas')
    ap.add_argument('--capturar', action='store_true', help='captura inicios, extremos e impactos autorizados')
    ap.add_argument('--transcribir', type=Path)
    ap.add_argument('--modelo', default='small')
    ap.add_argument('--idioma', default='es')
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    try:
        if args.transcribir:
            ruta = args.transcribir.resolve()
            salida = ruta.with_suffix('.palabras.json')
            salida.write_text(json.dumps(transcribir(ruta, args.modelo, args.idioma), ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'Marcas estimadas por ASR, revisar contra el guion: {salida}')
            return 0
        cfg = json.loads((root / 'motion.config.json').read_text(encoding='utf-8-sig'))
        plan = json.loads(Path(args.plan).read_text(encoding='utf-8-sig'))
        palabras = leer_palabras(json.loads(Path(args.voz).read_text(encoding='utf-8-sig'))) if args.voz else []
        datos = preparar(plan, cfg, palabras)
        (root / 'sincro.json').write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (root / 'subtitulos.srt').write_text(srt(datos['subtitulos']), encoding='utf-8')
        print(f'OK: {len(datos["planos"])} planos, {len(datos["impactos"])} impactos, {len(datos["muestras"])} muestras; sincro.json y subtitulos.srt')
        if args.capturar:
            # Renderiza con el motor existente; no crea un exportador paralelo.
            for i in range(0, len(datos['muestras']), 30):
                tiempos = ','.join(f'{f / datos["fps"]:.9f}' for f in datos['muestras'][i:i + 30])
                subprocess.run(['node', 'render.mjs', '--frames=' + tiempos], cwd=root, check=True)
            hoja_revision(root, datos)
        return 0
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
