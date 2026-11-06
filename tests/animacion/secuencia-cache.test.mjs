import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { huellaProyecto } from '../../motion-studio/assets/plantilla/cache.mjs';
import '../../motion-studio/assets/plantilla/kit/secuencia.js';
import '../../motion-studio/assets/plantilla/kit/sincro.js';

test('secuencia resuelve tiempos en cualquier orden, limita referencias y falla en recurso ausente', async () => {
  const prevFetch = globalThis.fetch, prevBitmap = globalThis.createImageBitmap;
  let cerrados = 0;
  globalThis.fetch = async url => ({ok:!url.includes('0003'),blob:async()=>url});
  globalThis.createImageBitmap = async src => ({src,close(){cerrados++;}});
  try {
    const s = crearSecuencia({ ruta:'f', cantidad:4, fps:12, cache:2 });
    assert.equal(s.indice(1 / 12), 1);
    assert.equal(s.indice(-1), 0);
    assert.equal(s.indice(999), 3);
    for (const t of [0, 1 / 12, 2 / 12, 0]) assert.equal((await s.fotograma(t)).src, `f${String(s.indice(t)).padStart(4,'0')}.png`);
    assert.equal(s.enCache, 2);
    assert.equal(cerrados, 2);
    await assert.rejects(s.fotograma(3 / 12), /No se pudo cargar/);
    assert.equal((await s.fotograma(0)).src, 'f0000.png');
    s.vaciar(); assert.equal(s.enCache, 0); assert.equal(cerrados, 4);
  } finally { globalThis.fetch = prevFetch; globalThis.createImageBitmap = prevBitmap; }
});

test('sincro no cruza subtítulos ni planos y rechaza impactos desconocidos', () => {
  const s = crearSincro({version:1,fps:24,impactos:[{id:'x',fotograma:12}],subtitulos:[{inicio:0,fin:1,texto:'Hola'}],planos:[{id:'P',inicio:0,fin:24}]});
  assert.equal(s.impacto('x'), 0.5);
  assert.equal(s.subtitulo(1), '');
  assert.equal(s.plano(1), null);
  assert.throws(() => s.impacto('y'), /desconocido/);
});

test('caché cambia al modificar código, recursos o perfil; resultados no se incluyen', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'motion-cache-'));
  try {
    fs.writeFileSync(path.join(root,'index.html'), 'a');
    const a = huellaProyecto(root);
    fs.mkdirSync(path.join(root,'review'));
    fs.writeFileSync(path.join(root,'review','frame.png'),'salida');
    assert.equal(huellaProyecto(root), a);
    fs.writeFileSync(path.join(root,'mezcla.wav'),'audio que se volverá a unir');
    assert.equal(huellaProyecto(root), a);
    fs.writeFileSync(path.join(root,'index.html'),'b');
    const b = huellaProyecto(root); assert.notEqual(a,b);
    fs.writeFileSync(path.join(root,'capa.png'),'recurso');
    assert.notEqual(huellaProyecto(root),b);
    assert.notEqual(huellaProyecto(root,{extra:{fps:24}}),huellaProyecto(root,{extra:{fps:30}}));
  } finally { fs.rmSync(root,{recursive:true,force:true}); }
});
