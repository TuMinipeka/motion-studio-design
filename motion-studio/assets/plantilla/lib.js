'use strict';
// Utilidades puras para un video que es función de t. Nada aquí guarda estado entre fotogramas.

// Ruido con semilla determinista: la misma semilla da siempre la misma secuencia. Nunca uses Math.random.
function mulberry32(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
// Valor sembrado por (semilla, índice): sin estado, se puede evaluar en cualquier orden.
const srand = (seed, i = 0) => mulberry32((seed * 7919 + i * 104729 + 13) | 0)();

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
// progreso 0..1 de t dentro de [t0, t1]
const prog = (t, t0, t1) => clamp((t - t0) / (t1 - t0));
const easeOutCubic = k => 1 - Math.pow(1 - k, 3);
const easeInOutCubic = k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);

// Texto determinista para canvas 2D. Chrome cachea los glifos según lo que ya dibujó: el mismo fillText bajo una
// escala, rotación o posición fraccionaria puede variar un nivel de color según el orden en que se pidieron los t,
// y `render.mjs --determinismo` falla. Cada cadena se rasteriza una sola vez, sin transformar, en un lienzo por CPU
// (`willReadFrequently`), y se dibuja como imagen: drawImage sí es estable bajo cualquier transformación.
// La memoria es la de una función pura (cadena, fuente, color) -> imagen; no cambia lo que se ve según el orden de t.
//   const { texto, numero, medir } = crearTexto(ctx);      // después de cargar las fuentes
//   texto('HOY.', '300px Titulo', '#fff', x, y);            // centrado en x, y = centro vertical
//   texto('Hola', '800 64px Interfaz', '#fff', x, y, { align: 'left', borde: 12, sombra: true });
//   numero(String(n), '200px Titulo', acento, x, y);        // contadores: se compone carácter a carácter
function crearTexto(ctx) {
  const memo = new Map();
  function sprite(txt, font, color, borde = 0, sombra = false, colorBorde = '#000') {
    const key = [txt, font, color, borde, sombra, colorBorde].join('|');
    let s = memo.get(key); if (s) return s;
    const size = +(font.match(/(\d+(?:\.\d+)?)px/) || [0, 48])[1], pad = Math.ceil(size * 0.4) + borde;
    const c = document.createElement('canvas'), x = c.getContext('2d', { willReadFrequently: true });
    x.font = font; const w = x.measureText(txt).width;
    c.width = Math.ceil(w + pad * 2); c.height = Math.ceil(size * 1.6 + pad * 2);
    x.font = font; x.textBaseline = 'middle'; x.lineJoin = 'round';
    if (sombra) { x.fillStyle = 'rgba(0,0,0,0.55)'; x.fillText(txt, pad + size * 0.04, c.height / 2 + size * 0.06); }
    if (borde) { x.strokeStyle = colorBorde; x.lineWidth = borde; x.strokeText(txt, pad, c.height / 2); }
    x.fillStyle = color; x.fillText(txt, pad, c.height / 2);
    s = { c, w, pad }; memo.set(key, s); return s;
  }
  const medir = (txt, font, op = {}) => sprite(txt, font, op.color || '#000', op.borde, op.sombra, op.colorBorde).w;
  function texto(txt, font, color, x, y, op = {}) {
    const s = sprite(txt, font, color, op.borde, op.sombra, op.colorBorde);
    const dx = op.align === 'left' ? 0 : op.align === 'right' ? s.w : s.w / 2;
    ctx.drawImage(s.c, x - s.pad - dx, y - s.c.height / 2);
    return s.w;
  }
  function numero(txt, font, color, x, y, op = {}) {
    const chars = [...txt], ws = chars.map(ch => medir(ch, font, { ...op, color }));
    let px = x - (op.align === 'left' ? 0 : ws.reduce((a, w) => a + w, 0) / 2);
    chars.forEach((ch, i) => { texto(ch, font, color, px, y, { ...op, align: 'left' }); px += ws[i]; });
  }
  return { texto, numero, medir };
}
