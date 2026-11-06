'use strict';
// Motion Studio · kit/luz.js — luz motivada para escenas 2D: halos de fuentes visibles, haces volumétricos, charcos de
// luz en el suelo, viñeta y tramado contra escalones. Requiere lib.js. Todo es función de los argumentos (y de t).
//
//   halo(ctx, 820, 240, 260, '#FFB45C', 0.9);                          // farola: núcleo + resplandor sumado
//   charco(ctx, 820, 900, 300, 70, '#FFB45C', 0.6);                    // su luz en la acera
//   haz(ctx, [[790, 250], [850, 250], [1060, 920], [580, 920]], 820, 250, 820, 920, '#FFB45C', 0.5, t, 3, 40);
//   vineta(ctx, W, H, 0.55);                                           // esquinas oscuras: centra la mirada
//   tramado(ctx, W, H);                                                // al final del fotograma: sin escalones en degradados oscuros
//
// Una luz cuenta algo (la farola del paradero, el celular a oscuras): ponla donde la escena la justifica y deja que
// ilumine también al personaje y al suelo; un halo suelto sin superficie que lo reciba parece una pegatina.

// Fuente visible: núcleo + resplandor, sumado (modo 'lighter').
function halo(ctx, x, y, r, color, int = 1) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, colorAlfa(color, 0.9 * int)); g.addColorStop(0.25, colorAlfa(color, 0.35 * int)); g.addColorStop(1, colorAlfa(color, 0));
  ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2); ctx.restore();
}

// Haz volumétrico: polígono con degradado de (x0, y0) a (x1, y1) y polvo sembrado que solo existe dentro del haz.
// `motas` = número de partículas; se mueven poco con ruidoSuave (t), siempre las mismas para la misma semilla.
function haz(ctx, puntos, x0, y0, x1, y1, color, int = 0.6, t = 0, semilla = 1, motas = 40) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.beginPath(); puntos.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.closePath();
  const g = ctx.createLinearGradient(x0, y0, x1, y1);
  g.addColorStop(0, colorAlfa(color, 0.42 * int)); g.addColorStop(1, colorAlfa(color, 0));
  ctx.fillStyle = g; ctx.fill(); ctx.clip();
  const xs = puntos.map(q => q[0]), ys = puntos.map(q => q[1]);
  const ax = Math.min(...xs), bx = Math.max(...xs), ay = Math.min(...ys), by = Math.max(...ys);
  for (let i = 0; i < motas; i++) {
    const px = lerp(ax, bx, srand(semilla, i)) + ruidoSuave(semilla + i, t, 0.3) * 12;
    const py = lerp(ay, by, srand(semilla + 7, i)) + ruidoSuave(semilla + 50 + i, t, 0.2) * 10;
    ctx.fillStyle = colorAlfa(color, (0.25 + 0.5 * srand(semilla + 3, i)) * int);
    ctx.beginPath(); ctx.arc(px, py, 1 + 1.6 * srand(semilla + 5, i), 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

// Charco de luz: la mancha elíptica que una fuente deja en el suelo (acera bajo la farola, mesa bajo la lámpara).
function charco(ctx, x, y, rx, ry, color, int = 0.6) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.translate(x, y); ctx.scale(1, ry / rx);
  const g = ctx.createRadialGradient(0, 0, 0, 0, 0, rx);
  g.addColorStop(0, colorAlfa(color, 0.55 * int)); g.addColorStop(0.55, colorAlfa(color, 0.22 * int)); g.addColorStop(1, colorAlfa(color, 0));
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, rx, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

// Niebla de horizonte: banda de aire que aclara y aplana lo lejano. y0 = horizonte, alto = espesor hacia arriba y abajo.
function nieblaHorizonte(ctx, W, y0, alto, color, int = 0.5) {
  ctx.save();
  const g = ctx.createLinearGradient(0, y0 - alto, 0, y0 + alto);
  g.addColorStop(0, colorAlfa(color, 0)); g.addColorStop(0.5, colorAlfa(color, int)); g.addColorStop(1, colorAlfa(color, 0));
  ctx.fillStyle = g; ctx.fillRect(0, y0 - alto, W, alto * 2); ctx.restore();
}

// Viñeta: oscurece las esquinas (fuerza 0–1). `centro` = [x, y] en fracciones del cuadro desplaza el foco de la mirada.
function vineta(ctx, W, H, fuerza = 0.5, centro = [0.5, 0.5], color = '#000000') {
  const cx = W * centro[0], cy = H * centro[1], r = Math.hypot(W, H) * 0.62;
  ctx.save();
  const g = ctx.createRadialGradient(cx, cy, r * 0.45, cx, cy, r);
  g.addColorStop(0, colorAlfa(color, 0)); g.addColorStop(1, colorAlfa(color, fuerza));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}

// Tramado determinista contra los escalones (banding) de los degradados oscuros: ruido fijo de ±3 niveles en modo
// 'overlay'. La tesela se crea una vez con semilla fija: no es estado que cambie entre fotogramas.
let _teselaTramado = null;
function tramado(ctx, W, H, fuerza = 1) {
  if (!_teselaTramado) {
    const c = document.createElement('canvas'); c.width = c.height = 256;
    const x = c.getContext('2d'); x.reset();
    const im = x.createImageData(256, 256), r = mulberry32(4501);
    for (let i = 0; i < 256 * 256; i++) { const v = 128 + Math.round((r() - 0.5) * 6); im.data.set([v, v, v, 255], i * 4); }
    x.putImageData(im, 0, 0); _teselaTramado = c;
  }
  ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = clamp(fuerza);
  for (let y = 0; y < H; y += 256) for (let x = 0; x < W; x += 256) ctx.drawImage(_teselaTramado, x, y);
  ctx.restore();
}
