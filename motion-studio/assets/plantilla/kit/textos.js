'use strict';
// Motion Studio · kit/textos.js — diálogo junto al personaje y tarjetas de cita que entran línea a línea.
// Requiere lib.js y las fuentes ya cargadas. Todo el texto pasa por crearTexto (determinista; nunca fillText directo).
// Cada función recibe el contexto donde dibujar (el del cuadro o el lienzo de un plano dentro de una transición).
//
//   const tx = crearTextos(ctx);                               // después de document.fonts.ready
//   tx.bocadillo(c, t, { texto: 'Empieza por un minuto.', inicio: 3.2, fin: 5.6 },
//                { x: 1180, y: 330, lado: 1, font: '700 38px Interfaz' });   // (x, y) = cabeza de quien habla
//   tx.cita(c, t, { lineas: ['Lo pequeño, repetido,', 'se vuelve grande.'], autor: '— Autor', inicio: 8, fin: 13 },
//           { x: W / 2, y: H / 2, font: '400 64px Serifa', fontAutor: '400 34px Serifa' });
//   const dur = lecturaMinima('Lo pequeño, repetido, se vuelve grande.');   // segundos para leerlo con calma
//
// Diálogo: el color separa voces (blanco = dice, acento = piensa). Ancla el texto a la cabeza que habla y déjalo a un
// lado, sin tapar la cara. Duración: lecturaMinima() es el mínimo; súmale la pausa que pida la escena.

// Segundos mínimos para leer un texto: ~3 palabras por segundo + 0,6 s para encontrarlo, nunca menos de `minimo`.
function lecturaMinima(texto, palabrasPorSegundo = 3, minimo = 1.2) {
  const n = String(texto).trim().split(/\s+/).filter(Boolean).length;
  return Math.max(minimo, n / palabrasPorSegundo + 0.6);
}

function crearTextos(ctxBase) {
  const { texto, medir } = crearTexto(ctxBase);

  // Placa de fondo con bordes suaves (difusa), para que el texto se lea sobre cualquier imagen.
  function placa(c, x, y, w, h, color, alfa, r) {
    c.save();
    c.filter = `blur(${Math.round(r * 0.6)}px)`;
    c.fillStyle = colorAlfa(color, alfa);
    c.beginPath(); c.roundRect(x, y, w, h, r); c.fill();
    c.restore();
  }

  // Bocadillo anclado: linea = {texto, inicio, fin} ('\n' parte líneas). op: x, y (ancla: la cabeza), lado (1 = a la
  // derecha del ancla, −1 = izquierda, 0 = centrado encima), separacion, font, color, placa ({color, alfa} o null),
  // entrada/salida (s), interlineado.
  function bocadillo(c, t, linea, op) {
    const { inicio, fin } = linea;
    const { x, y, lado = 0, separacion = 40, font = '700 40px sans-serif', color = '#FFFFFF',
      placa: pl = { color: '#000000', alfa: 0.55 }, entrada = 0.18, salida = 0.22, interlineado = 1.25 } = op;
    if (t < inicio || t > fin) return;
    const k = ease.sale(Math.min(prog(t, inicio, inicio + entrada), 1 - prog(t, fin - salida, fin)));
    const lineas = String(linea.texto).split('\n');
    const size = +(font.match(/(\d+(?:\.\d+)?)px/) || [0, 40])[1], alto = size * interlineado;
    const ancho = Math.max(...lineas.map(l => medir(l, font)));
    const pad = size * 0.45, w = ancho + pad * 2, h = alto * lineas.length + pad * 1.2;
    const cx = x + lado * (separacion + w / 2), cy = y - separacion - h / 2;
    c.save();
    c.globalAlpha = k;
    const s = lerp(0.96, 1, k);
    c.translate(cx, cy + (1 - k) * 8); c.scale(s, s);
    if (pl) placa(c, -w / 2, -h / 2, w, h, pl.color, pl.alfa, size * 0.5);
    lineas.forEach((l, i) => texto(l, font, color, 0, Math.round(-h / 2 + pad * 0.6 + alto * (i + 0.5)), { ctx: c }));
    c.restore();
  }

  // Cita sobre negro (o sobre una imagen oscura): cada línea entra con fundido y una subida corta, escalonadas; el
  // autor llega al final; todo se funde al terminar. cita = {lineas, autor?, inicio, fin}. op: x, y (centro del bloque),
  // font, fontAutor, color, colorAutor, escalonado (s entre líneas), entrada, subida (px), interlineado, fundido (s).
  function cita(c, t, cit, op) {
    const { inicio, fin, lineas, autor } = cit;
    const { x, y, font = '400 64px serif', fontAutor = '400 34px serif', color = '#F2F2F2', colorAutor = '#A9A9A9',
      escalonado = 0.9, entrada = 0.6, subida = 10, interlineado = 1.35, fundido = 0.6 } = op;
    if (t < inicio || t > fin) return;
    const size = +(font.match(/(\d+(?:\.\d+)?)px/) || [0, 64])[1], paso = size * interlineado;
    const filas = [...lineas.map(l => [l, font, color]), ...(autor ? [[autor, fontAutor, colorAutor]] : [])];
    const y0 = y - (paso * (filas.length - 1)) / 2, salidaK = 1 - prog(t, fin - fundido, fin);
    filas.forEach(([l, f, col], i) => {
      const t0 = inicio + i * escalonado + (autor && i === filas.length - 1 ? escalonado * 0.4 : 0);
      const k = ease.sale(prog(t, t0, t0 + entrada));
      if (k <= 0) return;
      c.save(); c.globalAlpha = k * salidaK;
      texto(l, f, col, x, Math.round(y0 + i * paso + (1 - k) * subida), { ctx: c });
      c.restore();
    });
  }

  return { bocadillo, cita, medir, texto };
}
