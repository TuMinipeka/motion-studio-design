// node tests/animacion/kit-tecnicas.test.mjs
// Funciones puras del kit de técnicas: cámara (respira, proyectar, encuadreHombro), montaje que se acelera, trazados
// de escritura, tiempo de lectura y determinismo de partículas (mismas llamadas de dibujo para el mismo t, en
// cualquier orden).
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const base = new URL('../../motion-studio/assets/plantilla/', import.meta.url);
const leer = r => fs.readFileSync(new URL(r, base), 'utf8');
const ctxVm = vm.createContext({});
for (const r of ['lib.js', 'kit/camara.js', 'kit/transiciones.js', 'kit/escritura.js', 'kit/particulas.js', 'kit/textos.js'])
  vm.runInContext(leer(r), ctxVm);
const g = n => vm.runInContext(n, ctxVm);
const cerca = (a, b, e = 1e-6) => assert.ok(Math.abs(a - b) <= e, `${a} ≉ ${b}`);
let casos = 0;

// proyectar: el centro de la cámara cae en el centro del cuadro; respeta zoom y giro
{
  const proyectar = g('proyectar');
  const [x, y] = proyectar({ x: 300, y: 200, zoom: 2, rot: 0 }, [300, 200], 1920, 1080);
  cerca(x, 960); cerca(y, 540);
  const [x2, y2] = proyectar({ x: 0, y: 0, zoom: 2, rot: Math.PI / 2 }, [10, 0], 100, 100);
  cerca(x2, 50); cerca(y2, 70); casos += 2;
}

// respira: el punto `hacia` no se mueve en pantalla mientras la cámara se acerca
{
  const respira = g('respira'), proyectar = g('proyectar');
  const cam = { x: 500, y: 400, zoom: 1.3, rot: 0 }, hacia = [620, 330];
  const p0 = proyectar(cam, hacia, 1920, 1080);
  for (const t of [0, 0.7, 1.5, 3]) {
    const c = respira(cam, t, 0, 3, 0.02, hacia), p = proyectar(c, hacia, 1920, 1080);
    cerca(p[0], p0[0], 1e-6); cerca(p[1], p0[1], 1e-6);
    cerca(c.zoom, cam.zoom * (1 + 0.02 * Math.min(1, t / 3))); casos++;
  }
}

// encuadreHombro: el que habla queda en el tercio indicado
{
  const encuadreHombro = g('encuadreHombro'), proyectar = g('proyectar');
  const sujeto = { x: 1000, y: 900, alto: 500 };
  for (const lado of [1, -1]) {
    const cam = encuadreHombro(sujeto, 1920, 1080, lado), [x] = proyectar(cam, [sujeto.x, cam.y], 1920, 1080);
    cerca(x, 960 + lado * 320, 1e-6); casos++;
  }
}

// aceleracion: n planos contiguos, del primero al último con las duraciones pedidas, monótonos
{
  const aceleracion = g('aceleracion');
  const r = aceleracion(35.4, 18, 1.4, 0.5);
  assert.equal(r.length, 18); cerca(r[0].inicio, 35.4); cerca(r[0].fin - r[0].inicio, 1.4, 1e-3); cerca(r[17].fin - r[17].inicio, 0.5, 1e-3);
  for (let i = 1; i < r.length; i++) { cerca(r[i].inicio, r[i - 1].fin, 1e-3); assert.ok(r[i].fin - r[i].inicio <= r[i - 1].fin - r[i - 1].inicio + 1e-9); }
  assert.equal(aceleracion(0, 1, 2, 1).length, 1);
  for (const mal of [[0, 0, 1, 1], [0, 3, 0, 1], [0, 3, 1, -1]]) assert.throws(() => aceleracion(...mal), /aceleracion/);
  casos += 3;
}

// trazados: largo = tinta + aire·salto; puntoEn recorre la polilínea
{
  const crearTrazado = g('crearTrazado'), puntoEn = g('puntoEn');
  const tr = crearTrazado([[[0, 0], [100, 0]], [[100, 50], [100, 150]]], 0.5);
  cerca(tr.largo, 100 + 50 * 0.5 + 100);
  const p = puntoEn([[0, 0], [100, 0], [100, 100]], 150); cerca(p.x, 100); cerca(p.y, 50);
  const x = g('marcaX(400, 300, 90, 5)'), x2 = g('marcaX(400, 300, 90, 5)');
  assert.deepEqual(JSON.parse(JSON.stringify(x)), JSON.parse(JSON.stringify(x2)));   // la misma semilla, la misma X
  assert.notDeepEqual(JSON.parse(JSON.stringify(x)), JSON.parse(JSON.stringify(g('marcaX(400, 300, 90, 6)'))));
  casos += 3;
}

// lecturaMinima: ~3 palabras/s + 0,6 s, con mínimo
{
  const lecturaMinima = g('lecturaMinima');
  cerca(lecturaMinima('uno dos tres cuatro cinco seis'), 2.6); cerca(lecturaMinima('Hola.'), 1.2); casos += 2;
}

// partículas: mismas llamadas de dibujo para el mismo t, aunque antes se hayan pedido otros t
{
  const espia = () => {
    const log = [];
    const ctx = new Proxy({}, { get: (o, k) => (k in o ? o[k] : (...a) => { log.push([k, ...a.map(v => (typeof v === 'number' ? +v.toFixed(6) : typeof v))]); }),
      set: (o, k, v) => { log.push(['=', k, v]); return true; } });
    return { ctx, log };
  };
  const op = 'W: 1920, H: 1080, n: 60, luz: (x, y) => (x > 900 ? 1 : 0)';
  for (const fn of ['lluvia', 'hojas']) {
    const a = espia(), b = espia();
    ctxVm.__a = a.ctx; ctxVm.__b = b.ctx;
    g(`${fn}(__a, 3.7, { ${op} })`);
    g(`${fn}(__b, 9.1, { ${op} }); ${fn}(__b, 0.2, { ${op} })`); b.log.length = 0;
    g(`${fn}(__b, 3.7, { ${op} })`);
    assert.deepEqual(a.log, b.log, `${fn} depende del orden de t`); casos++;
  }
}

console.log(`OK: ${casos} comprobaciones del kit de técnicas`);
