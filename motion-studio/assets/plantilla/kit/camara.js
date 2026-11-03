'use strict';
// Motion Studio · kit/camara.js — cámara virtual 2D: encuadres con nombre, movimientos con claves, temblor y paralaje.
// Requiere lib.js. Todo es función de t.
//
//   const sujeto = { x: 540, y: 1500, alto: 900 };   // lo que filmas: centro, base (pies, suelo) y alto en px del mundo
//   const cam = claves(t, [[0, encuadre('general', sujeto)], [2, encuadre('medio', sujeto), 'suave'],
//                          [2.01, encuadre('primerPlano', sujeto), 'escalon']]);        // 'escalon' = corte seco
//   const sacudida = temblor(t, [[1.2, 30]], 7);
//   aplicarCamara(ctx, cam, W, H, sacudida);   ... dibuja el mundo ...   ctx.restore();
//
// La cámara es {x, y, zoom, rot}: el punto del mundo que queda en el centro del cuadro, el aumento y el giro (rad).

// Encuadres clásicos calculados desde el sujeto = {x, y, alto}: x centro, y = su base (pies, suelo) y alto en px del
// mundo. Sirve para un personaje que dibujes tú, un objeto o un bloque de texto.
//   general     el sujeto entero con aire alrededor (ubica la escena)        ~45 % del alto del cuadro
//   conjunto    el sujeto entero, ajustado                                  ~80 %
//   medio       de la cintura hacia arriba (acción con las manos)
//   medioCorto  del pecho hacia arriba (reacción, diálogo)
//   primerPlano la cabeza llena el ancho (emoción)
//   detalle     un punto concreto muy cerca: `foco` = [x, y] del mundo
// H = alto del cuadro de salida (1920 en vertical, 1080 en horizontal).
function encuadre(nombre, sujeto, H = 1920, foco = null) {
  const { x, y, alto } = sujeto;
  const tipos = {             // visible = fracción del alto del sujeto que entra en el cuadro; centro = altura (0 pies, 1 coronilla)
    general: { visible: 2.2, centro: 0.5 },
    conjunto: { visible: 1.25, centro: 0.5 },
    medio: { visible: 0.75, centro: 0.72 },
    medioCorto: { visible: 0.55, centro: 0.8 },
    primerPlano: { visible: 0.5, centro: 0.86 },
    detalle: { visible: 0.2, centro: 0.86 },
  };
  const e = tipos[nombre];
  if (!e) throw new Error(`encuadre desconocido: ${nombre}`);
  return { x: foco ? foco[0] : x, y: foco ? foco[1] : y - alto * e.centro, zoom: H / (alto * e.visible), rot: 0 };
}

// Temblor por impulsos: [[t0, amplitud px, duracion s?], ...]. Decae y usa ruido suave con semilla (no vibra a lo loco).
function temblor(t, impulsos, semilla = 1) {
  let dx = 0, dy = 0, rot = 0;
  impulsos.forEach(([t0, amp, dur = 0.5], i) => {
    if (t < t0) return;
    const k = Math.exp(-((t - t0) / dur) * 4) * amp;
    dx += k * ruidoSuave(semilla + i * 3, t, 22); dy += k * ruidoSuave(semilla + i * 3 + 1, t, 22); rot += k * 0.0012 * ruidoSuave(semilla + i * 3 + 2, t, 18);
  });
  return { dx, dy, rot };
}

// Cámara en mano: deriva lenta y continua (documental, tensión). amp en px.
function camaraEnMano(t, amp = 8, semilla = 3) {
  return { dx: amp * ruidoSuave(semilla, t, 0.7), dy: amp * 0.7 * ruidoSuave(semilla + 1, t, 0.6), rot: 0.002 * ruidoSuave(semilla + 2, t, 0.5) };
}

// Hace ctx.save() y coloca la cámara; termina con ctx.restore() después de dibujar el mundo.
// `extra` suma desplazamientos en pantalla (temblor, cámara en mano).
function aplicarCamara(ctx, cam, W, H, ...extra) {
  let dx = 0, dy = 0, rot = cam.rot || 0;
  for (const e of extra) if (e) { dx += e.dx || 0; dy += e.dy || 0; rot += e.rot || 0; }
  ctx.save();
  ctx.translate(W / 2 + dx, H / 2 + dy); ctx.rotate(rot); ctx.scale(cam.zoom, cam.zoom); ctx.translate(-cam.x, -cam.y);
}

// Paralaje: cada capa tiene su propia cámara, que se mueve una fracción de lo que se mueve la principal respecto a una
// cámara de referencia `cam0` (normalmente el encuadre de apertura). profundidad 1 = plano del sujeto, 0.3 = fondo lejano,
// 1.5 = primer término. Se llama FUERA de aplicarCamara, en el orden de fondo a frente; dibuja la capa en coordenadas
// del mundo como cualquier otra cosa.
function paralaje(ctx, cam, cam0, profundidad, W, H, dibujar, ...extra) {
  const p = profundidad;
  const capa = { x: cam0.x + (cam.x - cam0.x) * p, y: cam0.y + (cam.y - cam0.y) * p,
    zoom: cam0.zoom * Math.pow(cam.zoom / cam0.zoom, p), rot: (cam.rot || 0) * p };
  aplicarCamara(ctx, capa, W, H, ...extra);
  dibujar(ctx);
  ctx.restore();
}
