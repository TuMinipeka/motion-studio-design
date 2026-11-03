'use strict';
// Motion Studio · kit/transiciones.js — enlaces entre planos. Requiere lib.js.
//
// Cada plano se escribe como una función que dibuja en el contexto que recibe: plano(ctx, t). Así la transición puede
// dibujar los dos planos en lienzos auxiliares y componerlos. Los lienzos se crean una vez y se limpian enteros en cada
// uso, de modo que el resultado depende solo de t.
//
//   const tr = crearTransiciones(W, H);                    // al cargar, una vez
//   tr.dibujar(ctx, t, { inicio: 3.0, dur: 0.35, tipo: 'whip', dir: 1 }, planoA, planoB);
//
// Tipos:
//   corte        cambio seco en `inicio` (no usa dur)
//   whip         barrido de cámara rápido con estela de movimiento; dir 1 = hacia la derecha, -1 = izquierda
//   empuje       el plano B empuja al A fuera del cuadro (dir como en whip; vertical con eje: 'y')
//   barrido      cortinilla con borde inclinado y una franja de color (op.color)
//   iris         círculo que se abre desde op.centro [x, y] (p. ej. los ojos del personaje): enlaza por un punto de interés
//   zoomAtraves  el plano A se acerca hasta atravesarse y B llega desde lejos (cambio de escala, energía)
//   flash        destello en el punto medio, para golpes de música
//   forma        corte por forma (match cut): op.forma(ctx, k) traza el contorno por donde aparece B y crece con k
//
// Duraciones de referencia: corte 0; whip 0.25–0.4 s; empuje y barrido 0.4–0.6 s; iris 0.5–0.8 s; zoomAtraves 0.4–0.6 s.

function crearTransiciones(W, H) {
  const lienzo = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; };
  const A = lienzo(), B = lienzo();

  function pintar(c, plano, t) {
    const x = c.getContext('2d'); x.reset(); plano(x, t);       // reset: lienzo y estado limpios en cada uso
    return c;
  }
  // estela: la imagen en (x, y) y n copias cada vez más tenues hacia (x + tx, y + ty), el lado de donde viene:
  // desenfoque de movimiento determinista.
  function estela(ctx, img, x, y, tx, ty, n) {
    for (let i = n; i >= 1; i--) { ctx.globalAlpha = 0.35 * (1 - i / (n + 1)); ctx.drawImage(img, x + tx * i / n, y + ty * i / n); }
    ctx.globalAlpha = 1; ctx.drawImage(img, x, y);
  }

  function dibujar(ctx, t, op, planoA, planoB) {
    const { inicio, dur = 0.4, tipo = 'corte', dir = 1 } = op;
    if (tipo === 'corte' || t < inicio) { (t < inicio ? planoA : planoB)(ctx, t); return; }
    if (t >= inicio + dur) { planoB(ctx, t); return; }
    const k = prog(t, inicio, inicio + dur);
    ctx.save();
    if (tipo === 'whip') {
      // paneo continuo muy rápido: A sale y B entra pegados (nunca queda el cuadro vacío), con una estela que crece
      // con la velocidad, máxima en el centro del movimiento
      const e = ease.suave(k), vel = Math.sin(k * Math.PI), n = 3 + Math.round(vel * 9), rastro = dir * vel * W * 0.35;
      estela(ctx, pintar(A, planoA, t), -dir * W * e, 0, rastro, 0, n);
      estela(ctx, pintar(B, planoB, t), dir * W * (1 - e), 0, rastro, 0, n);
    } else if (tipo === 'empuje') {
      const e = ease.suave(k), vx = op.eje === 'y' ? 0 : dir, vy = op.eje === 'y' ? dir : 0;
      ctx.drawImage(pintar(A, planoA, t), -vx * W * e, -vy * H * e);
      ctx.drawImage(pintar(B, planoB, t), vx * W * (1 - e), vy * H * (1 - e));
    } else if (tipo === 'barrido') {
      const e = ease.suave(k), inc = H * 0.18, x = lerp(-inc - 60, W + inc + 60, e);
      ctx.drawImage(pintar(A, planoA, t), 0, 0);
      const borde = (o) => { ctx.beginPath(); ctx.moveTo(-10, -10); ctx.lineTo(x + inc + o, -10); ctx.lineTo(x - inc + o, H + 10); ctx.lineTo(-10, H + 10); ctx.closePath(); };
      ctx.save(); borde(0); ctx.clip(); ctx.drawImage(pintar(B, planoB, t), 0, 0); ctx.restore();
      ctx.fillStyle = op.color || '#FFFFFF'; ctx.beginPath(); ctx.moveTo(x + inc, -10); ctx.lineTo(x + inc + 28, -10); ctx.lineTo(x - inc + 28, H + 10); ctx.lineTo(x - inc, H + 10); ctx.fill();
    } else if (tipo === 'iris') {
      const [cx, cy] = op.centro || [W / 2, H / 2], r = Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy)) * ease.entraExpo(k) + 1;
      ctx.drawImage(pintar(A, planoA, t), 0, 0);
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.clip(); ctx.drawImage(pintar(B, planoB, t), 0, 0);
    } else if (tipo === 'zoomAtraves') {
      const [cx, cy] = op.centro || [W / 2, H / 2];
      if (k < 0.5) { const z = 1 + ease.entraExpo(k * 2) * 5; ctx.translate(cx, cy); ctx.scale(z, z); ctx.translate(-cx, -cy); ctx.drawImage(pintar(A, planoA, t), 0, 0); }
      else { const z = lerp(0.35, 1, ease.saleExpo((k - 0.5) * 2)); ctx.translate(cx, cy); ctx.scale(z, z); ctx.translate(-cx, -cy); ctx.drawImage(pintar(B, planoB, t), 0, 0); }
    } else if (tipo === 'flash') {
      (k < 0.5 ? planoA : planoB)(ctx, t);
      ctx.globalAlpha = Math.pow(1 - Math.abs(k - 0.5) * 2, 2); ctx.fillStyle = op.color || '#FFFFFF'; ctx.fillRect(0, 0, W, H);
    } else if (tipo === 'forma') {
      ctx.drawImage(pintar(A, planoA, t), 0, 0);
      op.forma(ctx, ease.sale(k)); ctx.clip(); ctx.drawImage(pintar(B, planoB, t), 0, 0);
    } else throw new Error(`transición desconocida: ${tipo}`);
    ctx.restore();
  }

  // Encadena planos: lista = [{fin, plano, salida?: {tipo, dur, ...}}, ...]. La salida de cada plano empieza en su `fin`.
  // Es el montaje completo en una llamada:  tr.montaje(ctx, t, [{fin: 3, plano: p1, salida: {tipo: 'whip'}}, {fin: 6, plano: p2}])
  function montaje(ctx, t, lista) {
    let i = lista.findIndex(p => t < p.fin + (p.salida?.dur ?? 0));
    if (i < 0) i = lista.length - 1;
    const p = lista[i], sig = lista[i + 1];
    if (sig && p.salida && t >= p.fin) dibujar(ctx, t, { ...p.salida, inicio: p.fin }, p.plano, sig.plano);
    else p.plano(ctx, t);
  }

  return { dibujar, montaje };
}
