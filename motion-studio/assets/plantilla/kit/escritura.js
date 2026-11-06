'use strict';
// Motion Studio · kit/escritura.js — escritura a mano que aparece mientras se escribe: trazos con punta (rotulador,
// lápiz), marcas (X, chulo, círculo, subrayado) y revelado de texto con la mano siguiendo el borde. Requiere lib.js.
//
//   const x1 = marcaX(400, 300, 90, 5);                          // un trazado: lista de trazos (polilíneas)
//   const punta = escribir(ctx, x1, prog(t, 2.0, 2.6), { color: '#D93A3A', ancho: 10 });
//   dibujarMano(punta);                                           // la mano o el rotulador van donde está la punta
//
//   const esc = crearEscritura(W, H);                            // al cargar: un lienzo para el texto completo
//   const tx = crearTexto(esc.ctx);                               // texto determinista sobre ese lienzo
//   const p = esc.revelar(ctx, prog(t, 3, 4.5), { x: 300, y: 380, ancho: 520, alto: 200, letras: 5 },
//                         c => tx.texto('1 MIN', '220px Marcador', '#D93A3A', 560, 480));
//
// El tiempo de escritura sale del largo: ~0,25–0,4 s por letra a mano, ~0,35 s por trazo de una X. Entre trazos, la
// punta viaja por el aire (`salto`), sin pintar: así la mano no se teletransporta.

// Prepara un trazado: trazos = [[[x, y], …], …]. `salto` = fracción del recorrido aéreo entre trazos que cuenta como
// tiempo (0 = la punta salta al siguiente trazo sin pausa).
function crearTrazado(trazos, salto = 0.35) {
  const partes = [];   // tramos tinta y aire, en orden, con su largo
  trazos.forEach((pts, i) => {
    if (i > 0 && salto > 0) {
      const a = trazos[i - 1][trazos[i - 1].length - 1], b = pts[0];
      partes.push({ aire: true, pts: [a, b], largo: Math.hypot(b[0] - a[0], b[1] - a[1]) * salto });
    }
    let L = 0; for (let j = 1; j < pts.length; j++) L += Math.hypot(pts[j][0] - pts[j - 1][0], pts[j][1] - pts[j - 1][1]);
    partes.push({ aire: false, pts, largo: L });
  });
  return { partes, largo: partes.reduce((s, p) => s + p.largo, 0) };
}

// punto a distancia l a lo largo de una polilínea
function puntoEn(pts, l) {
  for (let j = 1; j < pts.length; j++) {
    const s = Math.hypot(pts[j][0] - pts[j - 1][0], pts[j][1] - pts[j - 1][1]);
    if (l <= s || j === pts.length - 1) {
      const k = s ? clamp(l / s) : 1;
      return { x: lerp(pts[j - 1][0], pts[j][0], k), y: lerp(pts[j - 1][1], pts[j][1], k),
        angulo: Math.atan2(pts[j][1] - pts[j - 1][1], pts[j][0] - pts[j - 1][0]) };
    }
    l -= s;
  }
  return { x: pts[0][0], y: pts[0][1], angulo: 0 };
}

// Dibuja el trazado hasta k (0–1) y devuelve la punta {x, y, angulo, tocando}. op: color, ancho, textura (veta de
// rotulador: un segundo trazo fino y claro desplazado), alfa.
function escribir(ctx, trazado, k, op = {}) {
  const { color = '#D93A3A', ancho = 8, textura = true, alfa = 1 } = op;
  let resto = clamp(k) * trazado.largo, punta = null;
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const p of trazado.partes) {
    const l = Math.min(resto, p.largo);
    if (p.aire) {
      if (l < p.largo) { const q = puntoEn(p.pts, p.largo ? l / p.largo * Math.hypot(p.pts[1][0] - p.pts[0][0], p.pts[1][1] - p.pts[0][1]) : 0); punta = { ...q, tocando: false }; }
    } else if (l > 0) {
      const pts = [p.pts[0]]; let acum = 0;
      for (let j = 1; j < p.pts.length; j++) {
        const s = Math.hypot(p.pts[j][0] - p.pts[j - 1][0], p.pts[j][1] - p.pts[j - 1][1]);
        if (acum + s >= l) { const q = puntoEn([p.pts[j - 1], p.pts[j]], l - acum); pts.push([q.x, q.y]); break; }
        pts.push(p.pts[j]); acum += s;
      }
      const trazar = () => { ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.stroke(); };
      ctx.globalAlpha = alfa; ctx.strokeStyle = color; ctx.lineWidth = ancho; trazar();
      if (textura) {
        ctx.save(); ctx.translate(ancho * 0.16, -ancho * 0.12); ctx.globalAlpha = 0.22 * alfa; ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = ancho * 0.28; trazar(); ctx.restore();
      }
      if (l < p.largo) { const q = puntoEn(p.pts, l); punta = { ...q, tocando: true }; }
    }
    resto -= p.largo;
    if (resto < 0) break;
  }
  ctx.restore();
  if (!punta) { const u = trazado.partes[trazado.partes.length - 1], q = puntoEn(u.pts, u.largo); punta = { ...q, tocando: false }; }
  return punta;
}

// ---------- marcas a mano (con un temblor fijo por semilla: dos X nunca son idénticas, pero cada una es siempre igual) ----------
const _tiembla = (semilla, i, amp) => (srand(semilla, i) - 0.5) * 2 * amp;
function _linea(x0, y0, x1, y1, semilla, base, amp, n = 8) {
  return Array.from({ length: n + 1 }, (_, i) => {
    const k = i / n, bombeo = Math.sin(Math.PI * k) * _tiembla(semilla, base + 99, amp * 1.5);
    const nx = -(y1 - y0), ny = x1 - x0, L = Math.hypot(nx, ny) || 1;
    return [lerp(x0, x1, k) + nx / L * bombeo + _tiembla(semilla, base + i, amp * 0.3), lerp(y0, y1, k) + ny / L * bombeo + _tiembla(semilla, base + 50 + i, amp * 0.3)];
  });
}
// X tachando: dos trazos, el segundo empieza arriba a la derecha (como se tacha de verdad).
function marcaX(x, y, tam, semilla = 1) {
  const h = tam / 2, a = tam * 0.05;
  return crearTrazado([_linea(x - h, y - h, x + h, y + h, semilla, 0, a), _linea(x + h, y - h, x - h, y + h, semilla, 200, a)]);
}
// Chulo (visto bueno): un solo trazo, bajada corta y subida larga.
function marcaCheck(x, y, tam, semilla = 1) {
  const a = tam * 0.04, p1 = [x - tam * 0.45, y], p2 = [x - tam * 0.12, y + tam * 0.33], p3 = [x + tam * 0.5, y - tam * 0.45];
  return crearTrazado([[..._linea(...p1, ...p2, semilla, 0, a, 5), ..._linea(...p2, ...p3, semilla, 100, a, 9).slice(1)]]);
}
// Círculo a mano: algo más de una vuelta, que no cierra exacto.
function circuloAMano(x, y, rx, ry, semilla = 1) {
  const n = 48, giro = 2 * Math.PI * 1.08, a0 = -2.2 + _tiembla(semilla, 1, 0.3);
  return crearTrazado([Array.from({ length: n + 1 }, (_, i) => {
    const u = i / n, r = 1 + _tiembla(semilla, 10 + Math.floor(i / 6), 0.03) + 0.04 * u;
    return [x + Math.cos(a0 + giro * u) * rx * r, y + Math.sin(a0 + giro * u) * ry * r];
  })]);
}
// Subrayado: una línea con un poco de onda y el final que sube.
function subrayado(x0, y, x1, semilla = 1) {
  const a = (x1 - x0) * 0.008;
  const pts = _linea(x0, y, x1, y - (x1 - x0) * 0.03, semilla, 0, a, 12);
  return crearTrazado([pts]);
}

// ---------- texto que se escribe ----------
// Revela un texto ya compuesto (con crearTexto sobre `esc.ctx`) de izquierda a derecha con borde suave, y devuelve la
// punta: avanza con el borde y sube y baja una vez por letra, como una mano que escribe. No traza cada letra: para eso,
// usa escribir() con los trazos de una fuente de un solo trazo (p. ej. Hershey, de dominio público).
function crearEscritura(W, H) {
  const O = document.createElement('canvas'), M = document.createElement('canvas');
  O.width = M.width = W; O.height = M.height = H;
  const ctxO = O.getContext('2d');
  function revelar(ctx, k, caja, dibujar, op = {}) {
    const { suave = 18, letras = 4 } = op, kk = clamp(k), borde = caja.x + caja.ancho * kk;
    ctxO.reset(); dibujar(ctxO);
    const m = M.getContext('2d'); m.reset();
    m.drawImage(O, 0, 0);
    // una sola máscara: opaca hasta el borde − suave y transparente desde el borde (destination-in recorta todo lo demás)
    m.globalCompositeOperation = 'destination-in';
    const g = m.createLinearGradient(0, 0, Math.max(1, borde), 0);
    g.addColorStop(0, '#000'); g.addColorStop(clamp((borde - suave) / Math.max(1, borde)), '#000'); g.addColorStop(1, 'rgba(0,0,0,0)');
    m.fillStyle = g; m.fillRect(0, 0, W, H);
    if (kk > 0) ctx.drawImage(M, 0, 0);
    return { x: borde, y: caja.y + caja.alto * (0.5 - 0.36 * Math.cos(2 * Math.PI * letras * kk)), angulo: 0, tocando: kk > 0 && kk < 1 };
  }
  return { ctx: ctxO, revelar };
}
