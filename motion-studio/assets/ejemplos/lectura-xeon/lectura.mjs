// Medición de lectura (7.º criterio): registra cada texto dibujado (posición en el fotograma, tamaño,
// progreso de entrada, opacidad, desenfoque, oclusión por los equipos 3D) 20 veces por segundo.
// node lectura.mjs  -> review/lectura_raw.json ; luego python lectura.py
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const ws = path.resolve(root, '../../../..');
const outFile = path.join(root, 'review', 'lectura_raw.json');
const FPS = 20, NW = 3;
const DUR = JSON.parse(fs.readFileSync(path.join(root, 'beats.json'))).bars * 2;
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(ws, '.browsers');
const { chromium } = await import('playwright');

const mime = { '.glb': 'model/gltf-binary', '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.ttf': 'font/ttf', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const base = rel.startsWith('/node_modules/three/') ? ws : root;
  const file = path.resolve(base, '.' + (rel === '/' ? '/index.html' : rel));
  if (!file.startsWith(base + path.sep)) { res.writeHead(403).end(); return; }
  fs.readFile(file, (err, b) => {
    if (err) { res.writeHead(404).end(); return; }
    res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream'); res.end(b);
  });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}/`;
const LAUNCH = { headless: true, args: ['--use-angle=d3d11', '--force_high_performance_gpu', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization'] };

function instrument() {
  const R = [], DEVF = [], pend = { phone: [], imac: [] };
  let SUP = 0, order = 0;
  const kindOf = c => c === STAGE.devs.phone.ctx ? 'phone' : c === STAGE.devs.imac.ctx ? 'imac' : 'main';
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  function rec(s, x, y, size, prog, al, o = {}, centered = false) {
    if (SUP) return;
    const k = kindOf(ctx), m = ctx.getTransform();
    let cx = x, cy = y - size * 0.35;
    if (!centered) {
      const w = tw(String(s), o.w || 500, size, o.f || 'Inter');
      const a = o.a || 'left';
      cx = a === 'left' ? x + w / 2 : a === 'right' ? x - w / 2 : x;
    } else cy = y;
    const X = m.a * cx + m.c * cy + m.e, Y = m.b * cx + m.d * cy + m.f;
    const blur = ctx.filter && ctx.filter !== 'none' ? parseFloat(ctx.filter.slice(5)) || 0 : 0;
    const r = { s: String(s), k, X, Y, h: size * Math.hypot(m.c, m.d), prog, al: ctx.globalAlpha * (al ?? 1), blur, o: order++, occ: 0 };
    if (k === 'main') R.push(r); else pend[k].push(r);
  }
  const _txt = txt, _rise = rise, _rw = riseWords, _roll = roll, _bub = drawBubbleText, _dev = devices, _ps = phoneScreen, _ui = asesorUI;
  window.txt = function (s, x, y, o = {}) { rec(s, x, y, o.s || 34, 1, o.al, o); return _txt.apply(this, arguments); };
  window.rise = function (s, x, y, prog, o = {}) {
    const p = clamp(prog); if (p > 0) rec(s, x, y, o.s || 34, p, o.al, o);
    SUP++; try { return _rise.apply(this, arguments); } finally { SUP--; }
  };
  window.riseWords = function (parts, x, y, t, t0, o = {}) {
    const st = o.stagger ?? 0.07, d = o.dur ?? 0.5, n = parts.length;
    const p = P(t, t0 + (n - 1) * st, d), p0 = P(t, t0, d);
    if (p0 > 0) rec(parts.map(q => q[0]).join(' '), x, y, o.s || 34, p, o.al, Object.assign({}, o, { a: 'left' }));
    SUP++; try { return _rw.apply(this, arguments); } finally { SUP--; }
  };
  window.roll = function (from, to, x, y, prog, o = {}) {
    if (prog > 0) rec(to, x, y, o.s || 40, clamp(prog), undefined, Object.assign({ a: 'right' }, o));
    SUP++; try { return _roll.apply(this, arguments); } finally { SUP--; }
  };
  window.drawBubbleText = function (m, x, y) {
    rec(m.text, x + m.bw / 2, y + m.h / 2, BUB.s, 1, undefined, {}, true);
    SUP++; try { return _bub.apply(this, arguments); } finally { SUP--; }
  };
  window.phoneScreen = function () { pend.phone = []; return _ps.apply(this, arguments); };
  window.asesorUI = function () { if (kindOf(ctx) === 'imac') pend.imac = []; return _ui.apply(this, arguments); };
  const inQuad = (x, y, q) => {
    let s = 0;
    for (let i = 0; i < 4; i++) {
      const a = q[i], b = q[(i + 1) % 4];
      const c = (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0]);
      if (c !== 0) { if (s === 0) s = Math.sign(c); else if (Math.sign(c) !== s) return false; }
    }
    return true;
  };
  window.devices = function (o, post = {}) {
    const ret = _dev.apply(this, arguments);
    const blur = post.blur || 0, alpha = post.alpha ?? 1;
    for (const k of ['phone', 'imac']) {
      if (!o[k]) continue;
      const d = STAGE.devs[k], cw = d.canvas.width, chh = d.canvas.height;
      const q = [[0, 0], [cw, 0], [cw, chh], [0, chh]].map(([a, b]) => STAGE.project(k, a, b));
      const c = STAGE.project(k, cw / 2, chh / 2);
      // cuerpo del equipo algo mayor que la pantalla
      const qe = q.map(p => [c[0] + (p[0] - c[0]) * 1.08, c[1] + (p[1] - c[1]) * 1.08]);
      for (const r of R) if (r.k === 'main' && !r.occ && inQuad(r.X, r.Y, qe)) r.occ = 1;
      DEVF.push({ k, X: c[0], Y: c[1], hp: dist(q[0], q[3]), wp: dist(q[0], q[1]), blur, al: alpha });
      for (const r of pend[k]) {
        const p = STAGE.project(k, r.X, r.Y), p2 = STAGE.project(k, r.X, r.Y - r.h), p3 = STAGE.project(k, r.X + r.h, r.Y);
        R.push(Object.assign({}, r, { X: p[0], Y: p[1], h: Math.min(dist(p, p2), dist(p, p3)), blur: Math.max(r.blur, blur), al: r.al * alpha, o: order++, occ: 0 }));
      }
      pend[k] = [];
    }
    return ret;
  };
  window.audFrame = t => {
    R.length = 0; DEVF.length = 0; order = 0; pend.phone = []; pend.imac = [];
    setCtx(mainCtx); mainCtx.setTransform(1, 0, 0, 1, 0, 0); mainCtx.globalAlpha = 1; mainCtx.filter = 'none';
    drawFrame(t);
    const f = v => Math.round(v * 10) / 10;
    return {
      r: R.map(r => [r.s, r.k, f(r.X), f(r.Y), f(r.h), Math.round(r.prog * 1000) / 1000, Math.round(r.al * 1000) / 1000, f(r.blur), r.occ]),
      d: DEVF.map(d => [d.k, f(d.X), f(d.Y), f(d.hp), f(d.wp), d.blur, d.al]),
    };
  };
}

const n = FPS * DUR, chunk = Math.ceil(n / NW);
const t0 = Date.now();
let gpu = '';
const parts = await Promise.all(Array.from({ length: NW }, async (_, w) => {
  const b = await chromium.launch(LAUNCH);
  const page = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.error('PAGEERROR', e.message));
  await page.goto(url);
  await page.waitForFunction(() => window.ready || window.loadError, null, { timeout: 90000 });
  const err = await page.evaluate(() => window.loadError);
  if (err) throw new Error(err);
  if (w === 0) gpu = await page.evaluate(() => { const g = document.createElement('canvas').getContext('webgl2'); const e = g.getExtension('WEBGL_debug_renderer_info'); return g.getParameter(e.UNMASKED_RENDERER_WEBGL); });
  await page.evaluate(instrument);
  const out = [];
  const a = w * chunk, z = Math.min(n, a + chunk);
  for (let i = a; i < z; i += 50) {
    const ts = []; for (let j = i; j < Math.min(z, i + 50); j++) ts.push(j / FPS);
    const res = await page.evaluate(ts => ts.map(t => window.audFrame(t)), ts);
    res.forEach((r, j) => out.push(Object.assign({ t: ts[j] }, r)));
  }
  await b.close();
  return out;
}));
fs.mkdirSync(path.dirname(outFile), { recursive: true });
fs.writeFileSync(outFile, JSON.stringify({ fps: FPS, dur: DUR, frames: parts.flat() }));
console.log('GPU:', gpu);
console.log('fotogramas', n, ((Date.now() - t0) / 1000).toFixed(0) + ' s ->', outFile);
server.close();
