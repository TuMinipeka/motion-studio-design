// node tests/animacion/encuadre-zona.test.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const contexto = vm.createContext({});
vm.runInContext(fs.readFileSync(new URL('../../motion-studio/assets/plantilla/kit/camara.js', import.meta.url), 'utf8'), contexto);
const encuadrar = contexto.encuadreZona;
let casos = 0;
for (const [W, H] of [[1920, 1080], [1080, 1920], [640, 640]]) {
  for (const margen of [0, 0.08, 0.2]) {
    for (const zona of [
      { x: 640, y: 290, ancho: 460, alto: 440 },
      { x: -500, y: -200, ancho: 1800, alto: 80 },
      { x: 100, y: -1000, ancho: 100, alto: 2000 },
    ]) {
      const cam = encuadrar(zona, W, H, margen);
      const puntos = [[zona.x, zona.y], [zona.x + zona.ancho, zona.y + zona.alto]];
      const proyectados = puntos.map(([x, y]) => [W / 2 + (x - cam.x) * cam.zoom, H / 2 + (y - cam.y) * cam.zoom]);
      for (const [x, y] of proyectados) {
        assert.ok(x >= W * margen - 1e-8 && x <= W * (1 - margen) + 1e-8);
        assert.ok(y >= H * margen - 1e-8 && y <= H * (1 - margen) + 1e-8);
      }
      // Aprovecha el espacio: al menos un eje toca los límites interiores.
      assert.ok(Math.abs(proyectados[0][0] - W * margen) < 1e-8
        || Math.abs(proyectados[0][1] - H * margen) < 1e-8);
      assert.equal(cam.rot, 0);
      assert.equal(cam.zoom, encuadrar(zona, W, H, margen).zoom);
      casos++;
    }
  }
}
const valida = { x: 0, y: 0, ancho: 100, alto: 100 };
for (const [zona, W, H, margen] of [
  [{ ...valida, ancho: 0 }, 1920, 1080, 0.08],
  [{ ...valida, alto: -1 }, 1920, 1080, 0.08],
  [{ ...valida, x: NaN }, 1920, 1080, 0.08],
  [valida, 0, 1080, 0.08], [valida, 1920, Infinity, 0.08],
  [valida, 1920, 1080, -0.01], [valida, 1920, 1080, 0.5],
]) assert.throws(() => encuadrar(zona, W, H, margen), /encuadreZona/);
console.log(`OK: ${casos} encuadres y 7 entradas inválidas`);
