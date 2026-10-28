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
