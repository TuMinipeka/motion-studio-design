// Recursos prerenderizados: índice absoluto, lectura bajo demanda y caché acotada.
// No reproduce un reloj: cada llamada resuelve el dibujo correspondiente a t.
(function (g) {
  'use strict';
  function crearSecuencia({ ruta, cantidad, fps, primero = 0, digitos = 4, extension = 'png', cache = 4 }) {
    if (typeof ruta !== 'string' || !ruta || !Number.isInteger(cantidad) || cantidad < 1
        || !Number.isFinite(fps) || fps <= 0 || !Number.isInteger(primero) || primero < 0
        || !Number.isInteger(digitos) || digitos < 1 || !Number.isInteger(cache) || cache < 1) {
      throw new Error('Secuencia: ruta, cantidad, fps, primero, digitos y cache inválidos');
    }
    const imagenes = new Map();
    let cola = Promise.resolve();
    const indice = t => {
      if (!Number.isFinite(t)) throw new Error('Secuencia: t debe ser finito');
      return Math.max(0, Math.min(cantidad - 1, Math.floor(t * fps + 1e-7)));
    };
    async function obtener(t) {
      const i = indice(t);
      if (imagenes.has(i)) {
        const im = imagenes.get(i); imagenes.delete(i); imagenes.set(i, im); return im;
      }
      const url = `${ruta}${String(primero + i).padStart(digitos, '0')}.${extension}`;
      let im;
      try {
        const respuesta = await fetch(url);
        if (!respuesta.ok) throw new Error(String(respuesta.status));
        im = await createImageBitmap(await respuesta.blob());
      } catch { throw new Error(`No se pudo cargar el recurso: ${url}`); }
      imagenes.set(i, im);
      while (imagenes.size > cache) {
        const viejo = imagenes.keys().next().value;
        imagenes.get(viejo).close(); imagenes.delete(viejo);
      }
      return im;
    }
    return {
      indice,
      // Serializa peticiones concurrentes sin depender del orden para elegir el índice.
      fotograma(t) { const p = cola.then(() => obtener(t)); cola = p.catch(() => {}); return p; },
      get enCache() { return imagenes.size; },
      vaciar() { for (const im of imagenes.values()) im.close(); imagenes.clear(); },
    };
  }
  g.crearSecuencia = crearSecuencia;
})(globalThis);
