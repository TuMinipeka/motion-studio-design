// node tests/animacion/puntos-3d.test.mjs [ruta a three.module.js instalado]
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { pathToFileURL } from 'node:url';
const THREE = await import(process.argv[2] ? pathToFileURL(process.argv[2]).href : 'three');
const c = vm.createContext({});
vm.runInContext(fs.readFileSync(new URL('../../motion-studio/assets/plantilla/kit/camara.js', import.meta.url), 'utf8'), c);
for (const cam of [new THREE.PerspectiveCamera(50, 9 / 16, 0.1, 100), new THREE.OrthographicCamera(-2, 2, 2, -2, 0.1, 100)]) {
  cam.position.set(0, 0, 5); cam.lookAt(0, 0, 0); cam.updateProjectionMatrix();
  const puntos = [
    { id: 'centro', punto: new THREE.Vector3(0, 0, 0) },
    { id: 'lateral', punto: new THREE.Vector3(100, 0, 0) },
    { id: 'detras', punto: new THREE.Vector3(0, 0, 6) },
    { id: 'lejano', punto: new THREE.Vector3(0, 0, -200) },
  ];
  const inicial = puntos.map(p => p.punto.toArray());
  const r = c.comprobarPuntos3D(cam, puntos);
  assert.equal(r[0].dentro, true); assert.equal(r[0].x, 0.5); assert.equal(r[0].y, 0.5);
  for (const i of [1, 2, 3]) assert.equal(r[i].dentro, false);
  assert.equal(r[2].frente, false);
  assert.deepEqual(puntos.map(p => p.punto.toArray()), inicial);
  assert.throws(() => c.comprobarPuntos3D(cam, []), /comprobarPuntos3D/);
  assert.throws(() => c.comprobarPuntos3D(cam, puntos, 0.5), /comprobarPuntos3D/);
  assert.throws(() => c.comprobarPuntos3D(cam, puntos, NaN), /comprobarPuntos3D/);
  assert.throws(() => c.comprobarPuntos3D(cam, [{ id: 'invalido', punto: new THREE.Vector3(NaN, 0, 0) }]), /no finito/);
  // Puntos definidos desde pantalla: el margen se aplica en ambos ejes y no solo a un caso central.
  const desdePantalla = (x, y, z = 0) => new THREE.Vector3(2 * x - 1, 1 - 2 * y, z).unproject(cam);
  for (const [x, y, dentro] of [[0.06, 0.5, true], [0.04, 0.5, false], [0.5, 0.96, false], [0.5, 0.06, true]]) {
    const r = c.comprobarPuntos3D(cam, [{ id: 'margen', punto: desdePantalla(x, y) }])[0];
    assert.ok(Math.abs(r.x - x) < 1e-10); assert.ok(Math.abs(r.y - y) < 1e-10);
    assert.equal(r.dentro, dentro);
  }
  assert.equal(c.comprobarPuntos3D(cam, [{ id: 'antes-near', punto: new THREE.Vector3(0, 0, 4.95) }])[0].dentro, false);
}
console.log('OK: perspectiva, ortográfica, márgenes, planos de recorte, detrás de cámara, entradas inválidas y puntos sin mutar');
