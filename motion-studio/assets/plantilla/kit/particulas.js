'use strict';
// Motion Studio · kit/particulas.js — lluvia, salpicaduras, hojas que caen y polvo en suspensión. Requiere lib.js.
// Cada partícula i es una función cerrada de (semilla, i, t): no hay simulación ni estado, así que cualquier fotograma
// se puede renderizar suelto, en cualquier orden. Las trayectorias se repiten en bucle sin saltos visibles porque cada
// partícula reaparece fuera de cuadro.
//
//   lluvia(ctx, t, { W, H, n: 260, vel: 1900, angulo: 0.12, luz: (x, y) => conoFarola(x, y) });
//   salpicaduras(ctx, t, { W, ySuelo: 980, n: 40 });
//   hojas(ctx, t, { W, H, n: 18, colores: ['#E39B3B', '#C9662A', '#F2C14E'] });
//   polvo(ctx, t, { zona: { x: 600, y: 200, ancho: 500, alto: 700 }, n: 60, color: '#FFE2B0' });
//
// Úsalas con intención: la lluvia cuenta adversidad, las hojas el paso del tiempo, el polvo el silencio de un cuarto.

const envolver = (v, m) => ((v % m) + m) % m;   // módulo siempre positivo: la partícula reaparece por el otro lado

// Lluvia en trazos. `luz(x, y)` opcional devuelve 0–1: las gotas brillan más dentro de un cono de luz (así se ve la
// lluvia «solo donde hay luz», como en la vida real). `capas` reparte las gotas en profundidad: las cercanas son más
// largas, rápidas y transparentes.
function lluvia(ctx, t, op) {
  const { W, H, n = 220, vel = 1800, largo = 38, angulo = 0.1, grosor = 1.6, color = '#BFD3E6', alfa = 0.35,
    semilla = 11, luz = null } = op;
  const dx = Math.sin(angulo), dy = Math.cos(angulo), alto = H * 1.25;
  ctx.save(); ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const z = srand(semilla + 4, i), v = vel * lerp(0.7, 1.3, z), L = largo * lerp(0.6, 1.5, z);
    const y = envolver(srand(semilla + 1, i) * alto + v * t, alto) - H * 0.12;
    const x = srand(semilla, i) * (W + alto * dx) - alto * dx * 0.5 + (y + H * 0.12) * dx;
    const k = luz ? clamp(0.25 + luz(x, y)) : 1;
    ctx.strokeStyle = colorAlfa(color, alfa * k * lerp(0.6, 1, 1 - z * 0.5));
    ctx.lineWidth = grosor * lerp(0.7, 1.4, z);
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - dx * L, y - dy * L); ctx.stroke();
  }
  ctx.restore();
}

// Salpicaduras sobre el suelo: anillos que nacen y se apagan en 0,18 s, cada uno con su periodo y fase.
function salpicaduras(ctx, t, op) {
  const { W, ySuelo, n = 40, color = '#D6E4F2', alfa = 0.5, semilla = 23, profundidad = 60, luz = null } = op;
  ctx.save(); ctx.lineWidth = 1.4;
  for (let i = 0; i < n; i++) {
    const periodo = lerp(0.35, 0.9, srand(semilla, i)), u = envolver(t + srand(semilla + 1, i) * periodo, periodo) / periodo;
    if (u > 0.2) continue;
    const k = u / 0.2, x = srand(semilla + 2, i) * W, y = ySuelo + srand(semilla + 3, i) * profundidad;
    const l = luz ? clamp(0.25 + luz(x, y)) : 1;
    ctx.strokeStyle = colorAlfa(color, alfa * (1 - k) * l);
    ctx.beginPath(); ctx.ellipse(x, y, 3 + 9 * k, (3 + 9 * k) * 0.3, 0, 0, Math.PI * 2); ctx.stroke();
  }
  ctx.restore();
}

// Hojas que caen con vaivén y giro. `dibujar(ctx, i, color)` opcional reemplaza la forma (por defecto, una hoja simple
// en (0, 0) de unos 22 px).
function hojas(ctx, t, op) {
  const { W, H, n = 16, vel = 70, viento = 25, vaiven = 40, colores = ['#E39B3B', '#C9662A', '#F2C14E'], semilla = 31,
    escala = 1, dibujar = null } = op;
  const alto = H + 120;
  for (let i = 0; i < n; i++) {
    const s = escala * lerp(0.6, 1.3, srand(semilla + 4, i)), f = lerp(0.25, 0.6, srand(semilla + 5, i));
    const y = envolver(srand(semilla + 1, i) * alto + vel * s * t, alto) - 60;
    const x = envolver(srand(semilla, i) * (W + 200) + viento * t + vaiven * Math.sin(2 * Math.PI * f * t + i), W + 200) - 100;
    const rot = 2 * Math.PI * srand(semilla + 2, i) + (1.2 + srand(semilla + 3, i)) * Math.sin(2 * Math.PI * f * t + i * 0.7);
    const color = colores[Math.floor(srand(semilla + 6, i) * colores.length)];
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s * (0.55 + 0.45 * Math.abs(Math.cos(2 * Math.PI * f * t + i))));
    if (dibujar) dibujar(ctx, i, color);
    else {
      ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(-12, 0); ctx.quadraticCurveTo(0, -9, 12, 0); ctx.quadraticCurveTo(0, 9, -12, 0); ctx.fill();
      ctx.strokeStyle = colorAlfa('#000000', 0.25); ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(-12, 0); ctx.lineTo(12, 0); ctx.stroke();
    }
    ctx.restore();
  }
}

// Polvo en suspensión: motas que derivan despacio y titilan dentro de una zona (útil dentro de un haz de luz).
function polvo(ctx, t, op) {
  const { zona, n = 50, color = '#FFFFFF', alfa = 0.5, semilla = 41, deriva = 18, rMax = 2.4 } = op;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const x = zona.x + srand(semilla, i) * zona.ancho + deriva * ruidoSuave(semilla + 100 + i, t, 0.15);
    const y = zona.y + srand(semilla + 1, i) * zona.alto + deriva * 0.7 * ruidoSuave(semilla + 300 + i, t, 0.12);
    const a = alfa * (0.4 + 0.6 * (0.5 + 0.5 * ruidoSuave(semilla + 500 + i, t, 0.6)));
    ctx.fillStyle = colorAlfa(color, a);
    ctx.beginPath(); ctx.arc(x, y, 0.6 + rMax * srand(semilla + 2, i), 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}
