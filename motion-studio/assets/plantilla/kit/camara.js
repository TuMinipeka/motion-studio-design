'use strict';
// Motion Studio · kit/camara.js — cámara virtual 2D y diagnóstico opcional de puntos 3D.
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

// Sobre el hombro (diálogo): el que habla queda en el tercio opuesto al hombro del que escucha, que se dibuja grande
// en primer término (más oscuro y desenfocado: kit/profundidad.js). lado = 1 pone al que habla en el tercio derecho.
// W, H = cuadro de salida. Mantén el mismo `lado` en el plano y el contraplano invertido (−lado) para no cruzar el eje.
function encuadreHombro(hablante, W, H, lado = 1, nombre = 'medioCorto') {
  const cam = encuadre(nombre, hablante, H);
  return { ...cam, x: cam.x - lado * (W / 6) / cam.zoom };
}

// Respiración de cámara: un acercamiento lento y casi imperceptible durante un plano fijo (1–2 % en 2–3 s mantiene
// vivo un diálogo o una pausa sin que se note el movimiento). Devuelve la cámara ajustada; `hacia` = [x, y] del mundo
// al que se acerca (por defecto, el centro actual). cantidad < 0 = se aleja.
function respira(cam, t, t0, t1, cantidad = 0.015, hacia = null) {
  const k = prog(t, t0, t1), z = 1 + cantidad * k;
  const [hx, hy] = hacia || [cam.x, cam.y];
  return { ...cam, zoom: cam.zoom * z, x: lerp(cam.x, hx, 1 - 1 / z), y: lerp(cam.y, hy, 1 - 1 / z) };
}

// Encuadra una zona del mundo (rostro, manos, texto, objeto) conservando sus cuatro bordes.
// La zona debe incluir el recorrido de la acción, no solo su pose inicial. Cámara fija, sin rotación.
// margen es una fracción de cada lado del cuadro; no depende de un estilo o tipo de sujeto.
function encuadreZona(zona, W, H, margen = 0.08) {
  const { x, y, ancho, alto } = zona;
  if (![x, y, ancho, alto, W, H, margen].every(Number.isFinite)
    || ancho <= 0 || alto <= 0 || W <= 0 || H <= 0 || margen < 0 || margen >= 0.5) {
    throw new Error('encuadreZona: zona y cuadro positivos; margen entre 0 y 0.5 (exclusivo).');
  }
  return { x: x + ancho / 2, y: y + alto / 2,
    zoom: Math.min(W * (1 - 2 * margen) / ancho, H * (1 - 2 * margen) / alto), rot: 0 };
}

// Diagnóstico opcional para Three.js: puntos del mundo imprescindibles para explicar una acción.
// No detecta oclusiones, tamaño legible ni solapamientos con la interfaz. Úsalo en revisión.
function comprobarPuntos3D(camara, puntos, margen = 0.05) {
  if (!Array.isArray(puntos) || !puntos.length || !Number.isFinite(margen) || margen < 0 || margen >= 0.5) {
    throw new Error('comprobarPuntos3D: puntos no vacíos y margen entre 0 y 0.5 (exclusivo).');
  }
  camara.updateMatrixWorld(true);
  return puntos.map(({ id, punto }) => {
    if (![punto.x, punto.y, punto.z].every(Number.isFinite)) throw new Error('comprobarPuntos3D: punto no finito');
    const local = punto.clone().applyMatrix4(camara.matrixWorldInverse);
    const p = punto.clone().project(camara), x = (p.x + 1) / 2, y = (1 - p.y) / 2;
    const frente = local.z < 0;
    return { id, x, y, frente, dentro: frente && p.z >= -1 && p.z <= 1
      && x >= margen && x <= 1 - margen && y >= margen && y <= 1 - margen };
  });
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

// Punto del mundo → punto del cuadro con esta cámara (sin temblor). Sirve para anclar al mundo lo que se dibuja fuera
// de la cámara: un bocadillo junto a la cabeza, una etiqueta, un brillo de interfaz.
function proyectar(cam, [x, y], W, H) {
  const c = Math.cos(cam.rot || 0), s = Math.sin(cam.rot || 0), dx = (x - cam.x) * cam.zoom, dy = (y - cam.y) * cam.zoom;
  return [W / 2 + dx * c - dy * s, H / 2 + dx * s + dy * c];
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
