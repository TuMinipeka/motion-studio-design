// Motion Studio · render determinista de un video que es una función pura de t.
//
//   node render.mjs --frames=0,1.5,3      fotogramas sueltos        -> review/frames/
//   node render.mjs --prueba=2,6          muestra con calidad final y mezcla si existe (max. 10 s) -> review/pruebas/
//   node render.mjs --sheet               un fotograma por pulso    -> review/beats/ (luego: python sheet.py)
//   node render.mjs --determinismo        comprueba que un fotograma depende solo de t (ver abajo)  [--t=0,1.5,3]
//   node render.mjs --ritmo               vista a 10 fps del video entero -> review/ritmo/vista.mp4 y `python ritmo.py`
//   node render.mjs --borrador            video completo, calidad de borrador (crf 16)
//   node render.mjs --final               video completo, calidad final (crf 12, preset slow)
//
// Opciones: --workers=N  --gpu=alto-rendimiento|bajo-consumo|auto|cpu  --swiftshader (= --gpu=cpu)
//           --pagina=kit/ejemplo.html   renderiza otra página del proyecto en lugar de index.html
//           --sin-audio               prueba visual explícitamente muda
// La configuración vive en motion.config.json (resolución, fps, GPU, calidad, salida).
import http from 'node:http';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { createRequire } from 'node:module';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const arg = k => { const a = process.argv.find(x => x === '--' + k || x.startsWith('--' + k + '=')); return a ? (a.split('=')[1] ?? true) : null; };

// ── configuración ────────────────────────────────────────────────────────────
const DEFECTO = {
  video: { ancho: 1920, alto: 1080, fps: 60, duracion: 10 },
  gpu: { modo: 'alto-rendimiento', angle: 'd3d11', coincidir: '', nombre: '' },
  codificacion: { borrador: { crf: 16, preset: 'medium' }, final: { crf: 12, preset: 'slow' } },
  salida: { carpeta: 'exportaciones', nombre: 'video' },
  workers: 6,
  revision: { desfase: 0.2 },
};
function cargarConfig() {
  const u = JSON.parse(fs.readFileSync(path.join(root, 'motion.config.json'), 'utf8'));
  const c = {};
  for (const k of Object.keys(DEFECTO)) {
    c[k] = typeof DEFECTO[k] === 'object' ? { ...DEFECTO[k], ...(u[k] || {}) } : (u[k] ?? DEFECTO[k]);
  }
  c.codificacion = { borrador: { ...DEFECTO.codificacion.borrador, ...(u.codificacion?.borrador || {}) },
                     final: { ...DEFECTO.codificacion.final, ...(u.codificacion?.final || {}) } };
  return c;
}
const cfg = cargarConfig();
const { ancho: W, alto: H, fps: FPS, duracion: DUR } = cfg.video;

// Validar el intervalo antes de abrir navegadores. Es una prueba corta, no una exportación completa.
const prueba = arg('prueba');
let rangoPrueba;
if (prueba !== null) {
  const partes = typeof prueba === 'string' ? prueba.split(',') : [];
  const [inicio, fin] = partes.map(Number);
  if (partes.length !== 2 || partes.some(s => !s.trim()) || !Number.isFinite(inicio) || !Number.isFinite(fin)
    || inicio < 0 || fin <= inicio || fin > DUR || fin - inicio > 10) {
    console.error('Usa --prueba=inicio,fin: 0 <= inicio < fin <= duracion; intervalo maximo de 10 s.');
    process.exit(1);
  }
  if (['frames', 'sheet', 'determinismo', 'ritmo', 'borrador', 'final'].some(k => arg(k) !== null)) {
    console.error('--prueba se ejecuta sin otros modos de render.'); process.exit(1);
  }
  rangoPrueba = [Math.ceil(inicio * FPS), Math.ceil(fin * FPS)];
  if (rangoPrueba[1] <= rangoPrueba[0]) { console.error('El intervalo no contiene fotogramas.'); process.exit(1); }
}

// ── Playwright: primero el del proyecto (o una carpeta superior); si no, el de las herramientas compartidas
// que instala `python scripts/preparar.py` de la skill (MOTION_STUDIO_HOME, por defecto ~/.motion-studio) ──
const HERRAMIENTAS = process.env.MOTION_STUDIO_HOME || path.join(os.homedir(), '.motion-studio');
let chromium;
try { ({ chromium } = await import('playwright')); }
catch {
  try { ({ chromium } = createRequire(path.join(HERRAMIENTAS, 'package.json'))('playwright')); }
  catch { console.error(`Falta Playwright. Desde la carpeta de la skill ejecuta:\n  python scripts/preparar.py\n(instala Playwright, Chromium y las fuentes en ${HERRAMIENTAS})`); process.exit(1); }
}

// ── GPU ──────────────────────────────────────────────────────────────────────
// Chrome sin interfaz elige la GPU por su cuenta; sin la bandera de alto rendimiento suele quedarse con la integrada.
const modoGpu = arg('swiftshader') ? 'cpu' : (typeof arg('gpu') === 'string' ? arg('gpu') : cfg.gpu.modo);
const CPU_ARGS = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
function argsGpu(modo) {
  if (modo === 'cpu') return CPU_ARGS;
  const base = [`--use-angle=${cfg.gpu.angle}`, '--enable-gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization'];
  if (modo === 'alto-rendimiento') base.splice(1, 0, '--force_high_performance_gpu');
  else if (modo === 'bajo-consumo') base.splice(1, 0, '--force_low_power_gpu');
  else if (modo !== 'auto') throw new Error(`gpu.modo desconocido: ${modo}`);
  return base;
}
const LAUNCH = { headless: true, args: argsGpu(modoGpu) };

// ── servidor estático ───────────────────────────────────────────────────────
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.glb': 'model/gltf-binary', '.wav': 'audio/wav', '.mp3': 'audio/mpeg' };
// /node_modules/... se sirve desde el primer node_modules hacia arriba que tenga ese archivo (p. ej. three.js) y,
// si ninguno lo tiene, desde las herramientas compartidas (fuentes @fontsource instaladas por preparar.py)
function raizNodeModules(rel) {
  for (let d = root; ; d = path.dirname(d)) {
    if (fs.existsSync(path.join(d, '.' + rel))) return d;
    if (d === path.dirname(d)) return fs.existsSync(path.join(HERRAMIENTAS, '.' + rel)) ? HERRAMIENTAS : root;
  }
}
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const base = rel.startsWith('/node_modules/') ? raizNodeModules(rel) : root;
  const file = path.resolve(base, '.' + (rel === '/' ? '/index.html' : rel));
  if (!file.startsWith(base + path.sep)) { res.writeHead(403).end(); return; }
  fs.readFile(file, (err, b) => {
    if (err) { res.writeHead(404).end(); return; }
    res.setHeader('Content-Type', MIME[path.extname(file)] || 'application/octet-stream'); res.end(b);
  });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}/` + (typeof arg('pagina') === 'string' ? arg('pagina').replace(/^\/+/, '') : '');

// ── navegadores: uno por proceso de render, cada uno con su propio proceso de GPU ──
const browsers = [];
async function lanzar() { const b = await chromium.launch(LAUNCH); browsers.push(b); return b; }
async function comprobarGpu() {
  const b = await lanzar(), p = await b.newPage();
  const r = await p.evaluate(() => { const g = document.createElement('canvas').getContext('webgl2'); const e = g && g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'sin WebGL'; });
  await p.close();
  console.log(`WebGL: ${r}  (modo ${modoGpu})`);
  if (modoGpu === 'cpu') return;
  if (/SwiftShader|sin WebGL/i.test(r)) console.warn('AVISO: no se obtuvo la GPU; el render usará la CPU (mucho más lento). Revisa references/gpu.md.');
  else if (cfg.gpu.coincidir && !new RegExp(cfg.gpu.coincidir, 'i').test(r)) console.warn(`AVISO: se esperaba una GPU que coincida con «${cfg.gpu.coincidir}»${cfg.gpu.nombre ? ` (${cfg.gpu.nombre})` : ''} y se usa otra.`);
}

async function abrirPagina() {
  const b = await lanzar();
  const page = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('PAGEERROR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
  await page.goto(url);
  await page.waitForFunction(() => window.ready || window.loadError, null, { timeout: 60000 });
  const err = await page.evaluate(() => window.loadError);
  if (err) throw new Error(err);
  return page;
}
async function foto(page, t, dest, type = 'png') {
  await page.evaluate(t => window.seek(t), t);
  return page.screenshot({ path: dest, type, quality: type === 'jpeg' ? 92 : undefined, animations: 'disabled', caret: 'hide' });
}
const trabajadores = () => +(arg('workers') || cfg.workers);

// ── sonoridad: la regla es -14 LUFS ────────────────────────────────────────
function lufs(archivo) {
  const r = spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', archivo, '-af', 'ebur128', '-f', 'null', '-'], { encoding: 'utf8' });
  const m = [...r.stderr.matchAll(/I:\s+(-?\d+(?:\.\d+)?)\s+LUFS/g)];
  return m.length ? +m[m.length - 1][1] : null;
}

try {
  if (!arg('frames') && !rangoPrueba && !arg('sheet') && !arg('determinismo') && !arg('ritmo') && !arg('borrador') && !arg('final')) {
    console.log('Uso: node render.mjs --frames=t1,t2 | --prueba=inicio,fin | --sheet | --determinismo | --ritmo | --borrador | --final   [--workers=N] [--gpu=modo]');
  } else {
    await comprobarGpu();
    if (arg('frames')) {
      const page = await abrirPagina();
      const out = path.join(root, 'review', 'frames'); fs.mkdirSync(out, { recursive: true });
      for (const s of String(arg('frames')).split(',')) { const t = +s; await foto(page, t, path.join(out, `t${t.toFixed(2).padStart(6, '0')}.png`)); }
      console.log('frames ->', out);
    } else if (rangoPrueba) {
      const [desde, hasta] = rangoPrueba;
      const out = path.join(root, 'review', 'pruebas'); fs.mkdirSync(out, { recursive: true });
      const salida = path.join(out, `movimiento-${desde}-${hasta}.mp4`), parcial = salida + '.part.mp4';
      const videoParcial = salida + '.video.part.mp4';
      const audio = path.join(root, 'audio', 'final.wav');
      const hayAudio = !arg('sin-audio') && fs.existsSync(audio);
      const segundos = (hasta - desde) / FPS;
      if (!hayAudio) console.warn('AVISO: prueba visual sin audio; la sincronización y la mezcla quedan pendientes.');
      const page = await abrirPagina();
      const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png',
        '-framerate', String(FPS), '-i', '-', '-an',
        '-c:v', 'libx264', '-preset', cfg.codificacion.final.preset, '-crf', String(cfg.codificacion.final.crf),
        '-pix_fmt', 'yuv420p', '-t', String(segundos), '-movflags', '+faststart', videoParcial], { stdio: ['pipe', 'inherit', 'inherit'] });
      const terminado = new Promise((resolve, reject) => {
        ff.once('error', reject);
        ff.once('close', code => code === 0 ? resolve() : reject(new Error(`FFmpeg fallo en la prueba (${code})`)));
      });
      terminado.catch(() => {});
      ff.stdin.on('error', () => {});
      try {
        for (let i = desde; i < hasta; i++) {
          const buf = await foto(page, i / FPS);
          await new Promise((resolve, reject) => ff.stdin.write(buf, err => err ? reject(err) : resolve()));
        }
        ff.stdin.end(); await terminado;
        // La captura entrega solo imagen. Con el archivo cerrado se une la mezcla;
        // el video ya codificado se copia sin una segunda compresión.
        if (hayAudio) {
          const mux = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', videoParcial, '-i', audio,
            '-filter_complex', `[1:a]atrim=start=${desde / FPS}:duration=${segundos},asetpts=PTS-STARTPTS,apad=whole_dur=${segundos}[a]`,
            '-map', '0:v:0', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k',
            '-t', String(segundos), '-movflags', '+faststart', parcial], { stdio: 'inherit' });
          if (mux.error || mux.status !== 0) throw new Error('FFmpeg fallo al unir la mezcla de la prueba');
          fs.renameSync(parcial, salida); fs.unlinkSync(videoParcial);
        } else fs.renameSync(videoParcial, salida);
        console.log(`OK prueba ${hayAudio ? 'con mezcla' : 'sin audio'}: ${salida} · ${segundos} s · ${hasta - desde} fotogramas · CRF ${cfg.codificacion.final.crf} / ${cfg.codificacion.final.preset}`);
      } finally {
        if (ff.exitCode === null) { ff.stdin.destroy(); ff.kill(); }
        await terminado.catch(() => {});
        await page.close();
      }
    } else if (arg('determinismo')) {
      // Un fotograma debe depender solo de t. Se comprueba con el hash de cada captura:
      //  1) el mismo t dos veces seguidas en una página (detecta estado que se arrastra entre fotogramas);
      //  2) los mismos t en orden inverso en otro navegador (detecta dependencia del historial o del reloj).
      const lista = arg('t') ? String(arg('t')).split(',').map(Number)
        : Array.from({ length: 10 }, (_, i) => +Math.min(DUR - 1 / FPS, i * DUR / 9).toFixed(3));
      const hash = b => crypto.createHash('sha256').update(b).digest('hex');
      const A = await abrirPagina(), B = await abrirPagina();
      const adelante = {}, repetido = {}, inverso = {};
      for (const t of lista) { adelante[t] = await foto(A, t); repetido[t] = await foto(A, t); }
      for (const t of [...lista].reverse()) inverso[t] = await foto(B, t);
      // Si difieren, se guardan ambas capturas y se mide dónde y cuánto: un Δ de 1-2 niveles en bordes de texto suele ser
      // la caché de glifos (texto con fillText bajo escala: usa crearTexto); un Δ grande, estado o reloj en el código.
      const out = path.join(root, 'review', 'determinismo'); fs.rmSync(out, { recursive: true, force: true });
      const comparar = (a, b) => A.evaluate(async ([a, b]) => {
        const leer = async s => { const im = await createImageBitmap(await (await fetch('data:image/png;base64,' + s)).blob());
          const c = new OffscreenCanvas(im.width, im.height), x = c.getContext('2d'); x.drawImage(im, 0, 0); return x.getImageData(0, 0, im.width, im.height).data; };
        const [p, q] = await Promise.all([leer(a), leer(b)]), w = innerWidth;
        let n = 0, max = 0, x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
        for (let i = 0; i < p.length; i += 4) {
          const d = Math.max(Math.abs(p[i] - q[i]), Math.abs(p[i + 1] - q[i + 1]), Math.abs(p[i + 2] - q[i + 2]));
          if (d) { n++; max = Math.max(max, d); const k = i / 4, x = k % w, y = (k - x) / w; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
        }
        return { n, max, zona: `${x0},${y0}–${x1},${y1}` };
      }, [a.toString('base64'), b.toString('base64')]);
      let fallos = 0, soloBordes = true;
      for (const t of lista) {
        const ok1 = hash(adelante[t]) === hash(repetido[t]), ok2 = hash(adelante[t]) === hash(inverso[t]);
        console.log(`t=${t.toFixed(3).padStart(8)}  ${ok1 ? 'igual   ' : 'DISTINTO'} (repetido)   ${ok2 ? 'igual   ' : 'DISTINTO'} (orden inverso)`);
        if (ok1 && ok2) continue;
        fallos++; fs.mkdirSync(out, { recursive: true });
        const otra = ok1 ? inverso[t] : repetido[t], d = await comparar(adelante[t], otra), base = path.join(out, `t${t.toFixed(3)}`);
        fs.writeFileSync(base + '_a.png', adelante[t]); fs.writeFileSync(base + '_b.png', otra);
        if (d.max > 2) soloBordes = false;
        console.log(`           ${d.n} px distintos · Δ máx ${d.max} · zona ${d.zona} -> ${path.relative(root, base)}_a.png / _b.png`);
      }
      console.log(fallos ? `FALLA: ${fallos} de ${lista.length} instantes no son deterministas` : `OK: ${lista.length} instantes idénticos`);
      if (fallos) console.log(soloBordes
        ? 'Pista: diferencias de 1-2 niveles. Si la zona es texto, es la caché de glifos: dibuja el texto con crearTexto (lib.js).'
        : 'Pista: hay estado que se arrastra entre fotogramas (acumuladores, cachés, contexto 2D sin ctx.reset()) o un reloj real.');
      if (fallos) process.exitCode = 1;
    } else if (arg('ritmo')) {
      // El ritmo no se ve en una hoja de contacto: se mide sobre el video entero a 10 fps, sin esperar al borrador.
      const R = 10, n = Math.floor(DUR * R), capturas = new Array(n);
      const out = path.join(root, 'review', 'ritmo'); fs.mkdirSync(out, { recursive: true });
      const vista = path.join(out, 'vista.mp4');
      let next = 0;
      await Promise.all(Array.from({ length: Math.min(trabajadores(), n) }, async () => {
        const page = await abrirPagina();
        while (next < n) { const i = next++; capturas[i] = await foto(page, i / R, undefined, 'jpeg'); }
        await page.close();
      }));
      const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(R), '-i', '-',
        '-vf', 'scale=480:-2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p', vista], { stdio: ['pipe', 'inherit', 'inherit'] });
      for (const buf of capturas) if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      ff.stdin.end(); await new Promise(r => ff.on('close', r));
      console.log(`vista de ritmo: ${path.relative(root, vista)} · ${n} fotogramas a ${R} fps`);
      const py = spawnSync(process.platform === 'win32' ? 'python' : 'python3', ['ritmo.py', vista], { cwd: root, stdio: 'inherit' });
      if (py.error) console.error('No pude ejecutar ritmo.py (¿Python con numpy en el PATH?):', py.error.message);
      if (py.status) process.exitCode = py.status;
    } else if (arg('sheet')) {
      // un fotograma por pulso, unos instantes después del golpe para ver la reacción
      const beats = JSON.parse(fs.readFileSync(path.join(root, 'beats.json'), 'utf8')).beats;
      const out = path.join(root, 'review', 'beats'); fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(out, { recursive: true });
      const pages = await Promise.all(Array.from({ length: trabajadores() }, abrirPagina));
      let next = 0;
      await Promise.all(pages.map(async page => {
        while (next < beats.length) { const i = next++; await foto(page, Math.max(0, beats[i] + cfg.revision.desfase), path.join(out, `${String(i).padStart(3, '0')}.jpg`), 'jpeg'); }
      }));
      console.log('beats ->', out, beats.length);
    } else {
      const modo = arg('borrador') ? 'borrador' : 'final', enc = cfg.codificacion[modo];
      // segmentos de 5 s: si se interrumpe, al relanzar solo rehace los que faltan (cada modo tiene los suyos)
      const n = FPS * DUR, SEG = FPS * 5;
      const tmp = path.join(root, 'review', 'segments-' + modo); fs.mkdirSync(tmp, { recursive: true });
      const nSeg = Math.ceil(n / SEG), segPath = k => path.join(tmp, `s${String(k).padStart(3, '0')}.mp4`);
      const okSeg = k => {
        if (!fs.existsSync(segPath(k))) return false;
        const r = spawnSync('ffprobe', ['-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', segPath(k)], { encoding: 'utf8' });
        return +r.stdout.trim() === Math.min(SEG, n - k * SEG);
      };
      const todo = []; for (let k = 0; k < nSeg; k++) if (!okSeg(k)) todo.push(k);
      console.log(`${modo}: crf ${enc.crf} ${enc.preset} · segmentos ${nSeg - todo.length}/${nSeg} listos, faltan ${todo.length}`);
      const t0 = Date.now(); let hechos = 0, next = 0;
      await Promise.all(Array.from({ length: Math.min(trabajadores(), todo.length) }, async () => {
        const page = await abrirPagina();
        while (next < todo.length) {
          const k = todo[next++], a = k * SEG, b = Math.min(n, a + SEG), part = segPath(k) + '.part.mp4';
          const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(FPS), '-i', '-',
            '-c:v', 'libx264', '-preset', enc.preset, '-crf', String(enc.crf), '-pix_fmt', 'yuv420p', '-r', String(FPS), part], { stdio: ['pipe', 'inherit', 'inherit'] });
          for (let i = a; i < b; i++) {
            const buf = await foto(page, i / FPS, undefined, 'png');
            if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
            if (++hechos % (FPS * 5) === 0) console.log(`${hechos}/${todo.length * SEG}  ${((Date.now() - t0) / 1000).toFixed(0)} s`);
          }
          ff.stdin.end(); await new Promise(r => ff.on('close', r));
          fs.renameSync(part, segPath(k));
        }
        await page.close();
      }));
      fs.writeFileSync(path.join(tmp, 'list.txt'), Array.from({ length: nSeg }, (_, k) => `file '${path.basename(segPath(k))}'`).join('\n'));
      const exp = path.resolve(root, cfg.salida.carpeta); fs.mkdirSync(exp, { recursive: true });
      const salida = path.join(exp, `${cfg.salida.nombre}${modo === 'borrador' ? '_borrador' : ''}.mp4`);
      const audio = path.join(root, 'audio', 'final.wav'), hayAudio = fs.existsSync(audio);
      if (hayAudio) {
        const l = lufs(audio);
        if (l === null) console.warn('AVISO: no se pudo medir la sonoridad de audio/final.wav');
        else if (Math.abs(l + 14) > 1) console.warn(`AVISO: audio/final.wav mide ${l.toFixed(1)} LUFS y la regla es -14.`);
        else console.log(`Sonoridad: ${l.toFixed(1)} LUFS`);
      } else console.warn('AVISO: no hay audio/final.wav; el video saldrá sin sonido.');
      const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', path.join(tmp, 'list.txt'),
        ...(hayAudio ? ['-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-shortest'] : ['-c:v', 'copy']),
        '-movflags', '+faststart', salida], { stdio: 'inherit' });
      if (r.status !== 0) throw new Error('falló el ensamblado final (mux)');
      console.log('OK', salida, ((Date.now() - t0) / 1000).toFixed(0) + ' s');
    }
  }
} catch (e) {
  console.error(e.message || e); process.exitCode = 1;
} finally {
  await Promise.all(browsers.map(b => b.close())); server.close();
}
