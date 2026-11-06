// Un mismo reloj para actuación, captions y audio: datos de produccion.py.
(function (g) {
  'use strict';
  function crearSincro(datos) {
    if (datos.version !== 1 || !(datos.fps > 0)) throw new Error('sincro.json inválido');
    const impactos = new Map(datos.impactos.map(e => [e.id, e]));
    return {
      impacto(id) {
        if (!impactos.has(id)) throw new Error(`Impacto desconocido: ${id}`);
        return impactos.get(id).fotograma / datos.fps;
      },
      subtitulo(t) { return datos.subtitulos.find(c => c.inicio <= t && t < c.fin)?.texto || ''; },
      plano(t) {
        const f = Math.floor(t * datos.fps + 1e-7);
        return datos.planos.find(p => p.inicio <= f && f < p.fin)?.id || null;
      },
    };
  }
  g.crearSincro = crearSincro;
})(globalThis);
