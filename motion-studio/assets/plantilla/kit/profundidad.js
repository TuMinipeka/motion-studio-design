'use strict';
// Motion Studio · kit/profundidad.js — profundidad de campo por capas, bokeh y niebla por distancia. Requiere lib.js.
//
// Cada capa es una función que dibuja en el contexto que recibe, como los planos del montaje: capa(c, t). Se pinta en
// su propio lienzo y se compone con un desenfoque proporcional a su distancia al plano de foco. Así se separan el
// primer término (una silueta de espaldas sobre el hombro), el sujeto nítido y el fondo con bokeh, y el foco puede
// cambiar de plano animando `foco` con claves() (rack focus).
//
//   const pf = crearProfundidad(W, H);                    // al cargar, una vez (crea los lienzos)
//   pf.componer(ctx, t, [
//     { z: 8,   dibujar: fondo },                          // z = distancia a cámara en unidades de la escena
//     { z: 3,   dibujar: sujeto },
//     { z: 0.8, dibujar: siluetaDeEspaldas },
//   ], { foco: claves(t, [[0, 3], [2, 0.8, 'suave']]), apertura: 6, max: 26, niebla: { color: '#0B1020', densidad: 0.05 } });
//
// - El desenfoque de una capa es `apertura · |z − foco| / max(z, foco)` px (relativo, como una lente: lo lejano se
//   desenfoca menos por unidad que lo cercano), con tope `max`. 0 = nítida.
// - Las capas se componen de lejos a cerca (z descendente). Su orden en la lista no importa.
// - `niebla` tiñe cada capa hacia `color` con fuerza 1 − e^(−densidad·z): lo lejano se funde con el aire.
// - Rendimiento: un lienzo W×H por capa (máximo `capas` en crearProfundidad) y un desenfoque por capa con foco fuera.
//   Usa 2–4 capas por plano; agrupa en una misma capa lo que está a la misma distancia.

function crearProfundidad(W, H, capas = 6) {
  const lienzos = Array.from({ length: capas }, () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; });

  function desenfoque(z, foco, apertura, max) {
    return Math.min(max, apertura * Math.abs(z - foco) / Math.max(z, foco, 1e-6));
  }

  function componer(ctx, t, lista, op = {}) {
    const { foco = 1, apertura = 6, max = 28, niebla = null } = op;
    if (lista.length > lienzos.length) throw new Error(`profundidad: ${lista.length} capas y solo hay ${lienzos.length} lienzos`);
    const orden = lista.map((c, i) => ({ ...c, i })).sort((a, b) => b.z - a.z || a.i - b.i);
    orden.forEach((capa, n) => {
      const c = lienzos[n], x = c.getContext('2d');
      x.reset();                                             // lienzo y estado limpios en cada uso
      capa.dibujar(x, t);
      if (niebla && niebla.densidad > 0) {
        const k = 1 - Math.exp(-niebla.densidad * capa.z);
        x.globalCompositeOperation = 'source-atop'; x.globalAlpha = clamp(k); x.fillStyle = niebla.color; x.fillRect(0, 0, W, H);
      }
      const r = capa.nitida ? 0 : desenfoque(capa.z, foco, apertura, max);
      ctx.save();
      if (r >= 0.5) ctx.filter = `blur(${r.toFixed(2)}px)`;
      if (capa.opacidad != null) ctx.globalAlpha = capa.opacidad;
      ctx.drawImage(c, 0, 0);
      ctx.restore();
    });
  }

  return { componer, desenfoque };
}

// Bokeh: puntos de luz desenfocados (farolas, ventanas, reflejos) como discos con el borde algo más brillante, sumados
// a lo que hay debajo. Dibújalo dentro de la capa lejana ANTES de su desenfoque o después, encima, con radio grande.
//   bokeh(ctx, [{ x, y, r: 40, color: '#FFB45C', int: 0.8 }, …])
function bokeh(ctx, luces) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (const { x, y, r, color, int = 0.7 } of luces) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, colorAlfa(color, 0.32 * int)); g.addColorStop(0.78, colorAlfa(color, 0.42 * int));
    g.addColorStop(0.93, colorAlfa(color, 0.6 * int)); g.addColorStop(1, colorAlfa(color, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

// Puntos de bokeh sembrados en una zona (copas de árboles, ciudad lejana): n discos con tamaño, color y brillo
// variables pero fijos para cada semilla. `parpadeo` (0–1) los hace respirar con ruidoSuave.
function bokehSembrado(ctx, t, zona, n, colores, op = {}) {
  const { semilla = 7, rMin = 14, rMax = 46, parpadeo = 0.25 } = op, luces = [];
  for (let i = 0; i < n; i++) {
    luces.push({ x: zona.x + srand(semilla, i) * zona.ancho, y: zona.y + srand(semilla + 1, i) * zona.alto,
      r: lerp(rMin, rMax, srand(semilla + 2, i)), color: colores[Math.floor(srand(semilla + 3, i) * colores.length)],
      int: 0.45 + 0.4 * srand(semilla + 4, i) + parpadeo * 0.3 * ruidoSuave(semilla + 50 + i, t, 0.35) });
  }
  bokeh(ctx, luces);
}
