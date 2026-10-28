// Motion Studio · render determinista de un video que es una función pura de t.
//
//   node render.mjs --frames=0,1.5,3      fotogramas sueltos        -> review/frames/
//   node render.mjs --sheet               un fotograma por pulso    -> review/beats/ (luego: python sheet.py)
//   node render.mjs --determinismo        comprueba que un fotograma depende solo de t (ver abajo)  [--t=0,1.5,3]
//   node render.mjs --borrador            video completo, calidad de borrador (crf 16)
//   node render.mjs --final               video completo, calidad final (crf 12, preset slow)
//
// Opciones: --workers=N  --gpu=alto-rendimiento|bajo-consumo|auto|cpu  --swiftshader (= --gpu=cpu)
// La configuración vive en motion.config.json (resolución, fps, GPU, calidad, salida).
import http from 'node:http';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
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

// ── Playwright (se resuelve hacia arriba desde esta carpeta; ver README de la skill) ──
let chromium;
try { ({ chromium } = await import('playwright')); }
catch { console.error('Falta Playwright. En la carpeta del proyecto o en una superior:\n  npm i playwright\n  npx playwright install chromium'); process.exit(1); }

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
// /node_modules/... se sirve desde el node_modules más cercano hacia arriba (p. ej. three.js)
function raizNodeModules() {
  for (let d = root; ; d = path.dirname(d)) { if (fs.existsSync(path.join(d, 'node_modules'))) return d; if (d === path.dirname(d)) return root; }
}
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const base = rel.startsWith('/node_modules/') ? raizNodeModules() : root;
  const file = path.resolve(base, '.' + (rel === '/' ? '/index.html' : rel));
  if (!file.startsWith(base + path.sep)) { res.writeHead(403).end(); return; }
  fs.readFile(file, (err, b) => {
    if (err) { res.writeHead(404).end(); return; }
    res.setHeader('Content-Type', MIME[path.extname(file)] || 'application/octet-stream'); res.end(b);
  });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}/`;

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
  if (!arg('frames') && !arg('sheet') && !arg('determinismo') && !arg('borrador') && !arg('final')) {
    console.log('Uso: node render.mjs --frames=t1,t2 | --sheet | --determinismo | --borrador | --final   [--workers=N] [--gpu=modo]');
  } else {
    await comprobarGpu();
    if (arg('frames')) {
      const page = await abrirPagina();
      const out = path.join(root, 'review', 'frames'); fs.mkdirSync(out, { recursive: true });
      for (const s of String(arg('frames')).split(',')) { const t = +s; await foto(page, t, path.join(out, `t${t.toFixed(2).padStart(6, '0')}.png`)); }
      console.log('frames ->', out);
    } else if (arg('determinismo')) {
      // Un fotograma debe depender solo de t. Se comprueba con el hash de cada captura:
      //  1) el mismo t dos veces seguidas en una página (detecta estado que se arrastra entre fotogramas);
      //  2) los mismos t en orden inverso en otro navegador (detecta dependencia del historial o del reloj).
      const lista = arg('t') ? String(arg('t')).split(',').map(Number)
        : Array.from({ length: 10 }, (_, i) => +Math.min(DUR - 1 / FPS, i * DUR / 9).toFixed(3));
      const hash = b => crypto.createHash('sha256').update(b).digest('hex');
      const A = await abrirPagina(), B = await abrirPagina();
      const adelante = {}, repetido = {}, inverso = {};
      for (const t of lista) { adelante[t] = hash(await foto(A, t)); repetido[t] = hash(await foto(A, t)); }
      for (const t of [...lista].reverse()) inverso[t] = hash(await foto(B, t));
      let fallos = 0;
      for (const t of lista) {
        const ok1 = adelante[t] === repetido[t], ok2 = adelante[t] === inverso[t];
        if (!ok1 || !ok2) fallos++;
        console.log(`t=${t.toFixed(3).padStart(8)}  ${ok1 ? 'igual   ' : 'DISTINTO'} (repetido)   ${ok2 ? 'igual   ' : 'DISTINTO'} (orden inverso)`);
      }
      console.log(fallos ? `FALLA: ${fallos} de ${lista.length} instantes no son deterministas` : `OK: ${lista.length} instantes idénticos`);
      if (fallos) process.exitCode = 1;
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
