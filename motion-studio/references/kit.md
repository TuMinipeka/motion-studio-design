# Kit de movimiento: curvas, cámara, transiciones y técnicas de imagen

El proyecto trae en `kit/` y `lib.js` piezas para el movimiento, la cámara y el montaje, que son iguales en cualquier estilo. Lo que se ve (personajes, objetos, escenarios) se diseña para cada pieza. El kit ofrece recursos; un plano fijo o un corte directo son válidos cuando sirven al relato.

Ejemplo completo y funcionando, pensado para 1080×1920, unos 8 s:

```bash
node render.mjs --pagina=kit/ejemplo.html --frames=1.2,3.6,6.5
```

Consúltalo si necesitas un ejemplo de estructura: planos como funciones, montaje con transiciones, principios de animación con `claves()` y `resorte()` (una pelota con anticipación, aplastamiento y rebote) y cámara calculada desde el sujeto.

Carga, en este orden: `lib.js`, `kit/camara.js` y `kit/transiciones.js`, y los módulos de técnicas que use la pieza: `kit/profundidad.js`, `kit/luz.js`, `kit/particulas.js`, `kit/escritura.js` y `kit/textos.js`. La plantilla `index.html` ya los incluye todos; quita los que no uses.

`kit/tecnicas.html` muestra esas técnicas funcionando, unos 12,5 s en 16:9:
- diálogo sobre el hombro con cambio de foco y bokeh;
- párpados;
- calendario con X que se aceleran y «1 MIN» escrito a mano;
- calle de noche con farola y lluvia;
- cita línea a línea.

```bash
node render.mjs --pagina=kit/tecnicas.html --frames=1.0,3.5,6.1,8.5,11.4
```

## Movimiento: `lib.js`

| Pieza | Para qué |
|---|---|
| `claves(t, [[t, valor, curva], …])` | Animación pose a pose. `valor` puede ser número, array u objeto (una pose, una cámara). `curva` es la del tramo que llega a esa clave. |
| `ease.*` | `sale` (llegar), `entra` (irse), `suave` (cámara), `saleBack` (pasarse y volver), `saleExpo` (golpe rápido), `saleElastica`, `escalon` (mantener y cortar). |
| `resorte(dt, frec, amort)` | Rebote físico analítico, sin estado: follow-through, objetos que se asientan, textos que caen. |
| `mezclar(a, b, k)` | Interpola poses, cámaras, colores en arrays… |
| `ruidoSuave(semilla, t, frec)` | Variación continua con semilla: respiración, cámara en mano, temblor vivo. |

**Reglas de timing** (a 30 fps; a 60 fps, el doble de fotogramas):

| Fase | Duración |
|---|---|
| Anticipación | 4–8 fotogramas (0,15–0,25 s), en sentido contrario a la acción |
| Acción | 3–6 fotogramas si es un golpe; 10–20 si es un gesto |
| Rebote o asentamiento | 6–12 fotogramas con `saleBack` o `resorte` |
| Mantener la pose | El tiempo necesario para leerla (0,3–0,8 s). Puede ser quieta; movimiento secundario solo si expresa el estado del sujeto |

Estos tiempos son orientativos: un gesto delicado no necesita el rebote de un golpe. Varía las curvas según peso e intención.

## Personajes: diséñalos para cada pieza

El kit no trae un personaje. Una versión anterior traía un muñeco con esqueleto de vista frontal, IK y poses, y se retiró tras probarlo con otro modelo. El resultado caminaba deslizándose, movía un solo brazo con el resto del cuerpo congelado y no tenía peso. En ese mismo video, los mejores momentos fueron los que no usaban el cuerpo: los ojos, el parpadeo, la mirada al cielo y los cortes. Un rig genérico empuja a mover articulaciones como una marioneta en lugar de actuar.

Diseña el personaje que pida el brief y anímalo con estos principios, usando `claves()`, `resorte()` y `ruidoSuave()`:

- **Dibuja para el plano.** El personaje no tiene que ser un esqueleto completo: puede ser una cabeza en primer plano, una mano con un objeto, una silueta o un cuerpo sin piernas detrás de una mesa. Muestra solo lo que el plano necesita y dibújalo con detalle. Lo que no se puede animar bien, sácalo de cuadro o cúbrelo con un corte.
- **Evita caminar de frente.** Es lo más difícil de hacer creíble en 2D. Usa perfil o tres cuartos, corta antes y después del desplazamiento, o muestra solo el efecto (la cámara que avanza, el fondo con paralaje, los pies en un detalle).
- **Peso y equilibrio.** El cuerpo entero participa en cada gesto. Cuando sube un brazo, el hombro sube, el torso se inclina un poco y la cabeza compensa. Nada se mueve solo.
- **Escalona los movimientos.** Los ojos van primero, luego la cabeza, luego el torso y al final los brazos y el pelo: desfasa sus claves 2–4 fotogramas. El pelo, la ropa y los objetos colgantes siguen con retraso y se asientan con `resorte()`.
- **Arcos, no líneas.** Las manos y la cabeza se mueven en arco entre poses: interpola un ángulo, no una posición recta.
- **Anticipación y asentamiento.** Úsalos según peso e intención; no impongas rebote a miradas, diálogo o manos que deben mantener contacto.
- **Silueta legible.** Cada pose clave se entiende en negro sobre blanco. Si dos poses tienen la misma silueta, el cambio no se lee.
- **La cara cuenta más que el cuerpo** en formato vertical. Párpados, cejas, dirección de la mirada y un parpadeo a tiempo transmiten más que un brazo que sube. Planifica primeros planos para la emoción.
- **Vida en reposo.** Una pose mantenida respira (escala del pecho de ±1–2 % con `Math.sin(t)`), parpadea cada 2–5 s y deriva un poco con `ruidoSuave()`. Respeta una inmovilidad deliberada; evita balanceos automáticos de todas las partes.

Antes de extender el personaje a toda la pieza, haz una prueba de movimiento de su gesto principal con `--prueba` y revísala reproduciéndola.

## Cámara: `kit/camara.js`

```js
const sujeto = { x, y: pies, alto };                            // lo que filmas; la cámara se calcula antes de dibujar
const cam = claves(t, [[0, encuadre('general', sujeto, H)], [2, encuadre('medio', sujeto, H), 'suave'],
                       [2.01, encuadre('primerPlano', sujeto, H), 'escalon']]);   // escalon = corte seco
aplicarCamara(ctx, cam, W, H, temblor(t, [[tGolpe, 30, 0.45]]), camaraEnMano(t, 8));
/* … dibujar el mundo … */  ctx.restore();
paralaje(ctx, cam, cam0, 0.35, W, H, dibujarFondo);            // capas a otra distancia, fuera de aplicarCamara
```

**Zona de interés y nitidez.** Para una reacción, una mano o un texto, encuadra su región de acción en vez de ampliar toda la escena sin destino:

```js
const cam = encuadreZona({ x: 640, y: 290, ancho: 460, alto: 440 }, W, H, 0.08);
aplicarCamara(ctx, cam, W, H);  // dibuja el mundo y termina con ctx.restore()
```

`encuadreZona` conserva el rectángulo completo con un margen en ambos ejes, también en horizontal. Incluye las poses extremas en la zona. Es una garantía geométrica para esa cámara sin giro; no detecta personajes, oclusiones ni juzga la composición. Si después interpolas, rotas o añades temblor, revisa otra vez los extremos.

Si el sujeto se dibuja en una capa rasterizada, dimensiona esa capa para el mayor aumento de la toma: una capa de 600 px ampliada 2,1 veces necesita unos 1260 px de detalle de origen. Dibuja de nuevo a esa densidad y compón en sus dimensiones lógicas; ampliar los píxeles existentes no recupera detalle. Reserva esa densidad para las capas y planos que lo necesitan, con tamaños de caché fijos por toma; no dupliques toda la resolución o los fps por rutina.

**Puntos críticos en Three.js (opcional).** Si el proyecto ya usa Three.js, `comprobarPuntos3D(camara, [{ id, punto }], margen)` proyecta sus `Vector3` en coordenadas normalizadas de pantalla (x de izquierda a derecha, y de arriba abajo). Devuelve `dentro` y `frente`, sin mutar los puntos. Actualiza la proyección de la cámara si cambias su fov o proporción y llama al diagnóstico después de fijar la cámara del instante.

```js
const revision = comprobarPuntos3D(cam, [
  { id: 'entrada', punto: entradaDelFlujo },
  { id: 'salida', punto: salidaDelFlujo },
], 0.05);
// Revisa los resultados en los instantes clave; no hace falta ejecutarlo en cada fotograma exportado.
```

Solo comprueba esos puntos, su profundidad y márgenes: no el volumen entero, oclusiones, textos del HUD ni legibilidad. El margen es del cuadro completo, no una zona segura de plataforma. Para una explicación espacial, aplica también `references/estilos.md`.

**Diálogo, respiración y anclas.**
- **Diálogo.** `encuadreHombro(hablante, W, H, lado)` pone a quien habla en un tercio y deja el otro tercio para el hombro de quien escucha. Ese hombro va en primer término, grande, oscuro y desenfocado (ver «Profundidad de campo»). Usa `−lado` en el contraplano, para no cruzar el eje.
- **Respiración.** `respira(cam, t, t0, t1, 0.015, [x, y])` acerca la cámara un 1–2 % durante un plano fijo hacia un punto que no se mueve en pantalla. Mantiene viva una conversación o una pausa sin que se note.
- **Anclas.** `proyectar(cam, [x, y], W, H)` convierte un punto del mundo en un punto del cuadro. Sirve para anclar algo que se dibuja fuera de la cámara, como un bocadillo junto a la cabeza.

```js
const cam = respira(encuadreHombro(vendedora, W, H, 1), t, plano.inicio, plano.fin, 0.02, cabeza);
const [hx, hy] = proyectar(cam, cabeza, W, H);   // ahí va el bocadillo
```

Ninguna de estas piezas arregla un tramo que `ritmo.py` marca como muerto: la respiración es casi imperceptible a propósito. Si falta acción, vuelve a la puesta en escena.

**Gramática de planos:**
- **`general`** ubica la escena.
- **`medio`**, para acciones con las manos.
- **`medioCorto`**, para reacciones.
- **`primerPlano`**, para la emoción.
- **`detalle`**, para un objeto o dato concreto.

Cambia de escala al revelar información o seguir la acción; `ritmo.py` no identifica ángulos ni evalúa el motivo del corte. Acota inicio, fin y zoom máximo; evita multiplicar el zoom por el tiempo indefinidamente. Verifica extremos y cruces de plano para que ojos, manos y texto necesario no queden recortados. Corta en la acción: el corte cae en mitad del gesto, no antes ni después. Para seguir un salto, mueve la cámara con la altura y abre el plano. No dejes que la cabeza salga del cuadro sin intención.

## Transiciones: `kit/transiciones.js`

```js
const tr = crearTransiciones(W, H);                               // al cargar, una vez
function plano1(c, t) { … }  function plano2(c, t) { … }          // cada plano dibuja en el contexto que recibe
tr.montaje(ctx, t, [ { fin: 2.6, plano: plano1, salida: { tipo: 'whip', dur: 0.3, dir: 1 } },
                     { fin: 5.3, plano: plano2, salida: { tipo: 'iris', dur: 0.6, centro: [540, 700] } },
                     { fin: 99, plano: plano3 } ]);
```

| Tipo | Úsalo para |
|---|---|
| `corte` | Lo normal entre planos de la misma escena |
| `whip` (0,25–0,4 s) | Energía, cambio de lugar |
| `empuje` (0,4–0,6 s) | Secuencias, listas |
| `barrido` | Cambio de capítulo, con `color` de acento |
| `iris` (0,5–0,8 s) | Enlazar por un punto de interés: los ojos, un objeto |
| `zoomAtraves` | Entrar en una idea |
| `flash` | Golpe musical |
| `forma` (match cut) | Pasar de una forma a otra parecida: `op.forma(ctx, k)` traza el contorno |
| `parpados` (1,2–2 s) | Punto de vista del personaje: cierra sobre A, negro, abre sobre B desenfocado que se enfoca (despertar, «al día siguiente»). `parpadeos: 2` hace un primer intento a medias |

Un buen enlace conserva algo entre los planos: posición, forma, dirección del movimiento o color. El corte seco es la norma; reserva las transiciones con efecto para cambios de tiempo, de lugar o de punto de vista.

**Montaje que se acelera.** `aceleracion(inicio, n, d0, d1)` devuelve `n` intervalos `{i, inicio, fin}` cuya duración pasa de `d0` a `d1`. Sirve para comprimir una rutina que se repite: la misma función de plano con un dato distinto en cada repetición (el día, la excusa, los km). Que cada repetición cambie algo; si son idénticas, solo es relleno.

```js
const dias = aceleracion(35.4, 18, 1.4, 0.5);    // de 1,4 s a 0,5 s por plano
const lista = dias.map(d => ({ fin: d.fin, plano: (c, t) => alarma(c, t, d.i) }));
```

## Profundidad de campo: `kit/profundidad.js`

Separa primer término, sujeto y fondo, y guía la mirada como una lente. Cada capa se pinta en su lienzo y se desenfoca según su distancia al plano de foco. Para cambiar el foco de plano (*rack focus*), anima `foco` con `claves()`.

```js
const pf = crearProfundidad(W, H, 4);               // al cargar: un lienzo por capa
pf.componer(ctx, t, [
  { z: 7, dibujar: fondo },                          // z = distancia a cámara (unidades de la escena)
  { z: 3, dibujar: sujeto },
  { z: 0.9, dibujar: hombroDelQueEscucha },
], { foco: claves(t, [[0, 3], [1.8, 3], [2.5, 0.9, 'suave']]), apertura: 9, max: 22,
     niebla: { color: '#0B1020', densidad: 0.05 } });
bokehSembrado(c, t, zona, 9, ['#FFB45C', '#9FC3FF']); // luces desenfocadas del fondo (o bokeh([...]) a mano)
```

- **Desenfoque.** `apertura · |z − foco| / max(z, foco)` px, con tope `max`. Lo cercano se desenfoca más por unidad que lo lejano. `nitida: true` excluye una capa.
- **Niebla.** Funde cada capa con el color del aire según su distancia.
- **Costo.** Un lienzo y un desenfoque por capa. Usa 2–4 capas por plano y agrupa lo que está a la misma distancia.

## Luz motivada: `kit/luz.js`

`halo` (fuente visible), `haz` (cono volumétrico con polvo sembrado), `charco` (la luz en el suelo), `nieblaHorizonte`, `vineta` y `tramado` (contra los escalones de los degradados oscuros, al final del fotograma). Una luz tiene que estar justificada por la escena y tocar algo: el suelo, al personaje, la lluvia. Un halo suelto parece una pegatina.

## Partículas: `kit/particulas.js`

`lluvia`, `salpicaduras`, `hojas` y `polvo`. Cada partícula es una función cerrada de (semilla, índice, t): no hay simulación, así que cualquier fotograma se renderiza suelto.
- **Lluvia.** Con `luz: (x, y) => 0–1`, las gotas brillan dentro del cono de una farola, como en la vida real.
- **Uso.** Cuentan algo: la adversidad, el paso de las estaciones, el silencio de un cuarto. No las uses para tapar un tramo quieto.

## Escritura a mano: `kit/escritura.js`

La decisión del personaje se ve suceder: el trazo aparece mientras la punta avanza.

```js
const x = marcaX(cx, cy, 64, semilla);                        // también marcaCheck, circuloAMano, subrayado
const punta = escribir(ctx, x, prog(t, t0, t0 + 0.35), { color: '#D93A3A', ancho: 9 });
dibujarRotulador(punta);                                       // {x, y, angulo, tocando}

const esc = crearEscritura(W, H), tx = crearTexto(esc.ctx);   // al cargar
const p = esc.revelar(ctx, prog(t, 5.8, 6.6), { x, y, ancho, alto, letras: 4 }, c => tx.texto('1 MIN', fuente, rojo, cx, cy));
```

- **Trazados.** `crearTrazado(trazos, salto)` sirve para cualquier forma; `salto` es el tiempo que la punta viaja por el aire entre trazos.
- **Texto.** `revelar()` descubre el texto de izquierda a derecha y devuelve una punta que sube y baja una vez por letra. No traza cada letra: para eso, pasa a `escribir()` los trazos de una fuente de un solo trazo (Hershey, de dominio público).
- **Ritmo de referencia:** ~0,25–0,4 s por letra y ~0,35 s por X.

## Textos en escena: `kit/textos.js`

- **Bocadillo.** `bocadillo(c, t, {texto, inicio, fin}, {x, y, lado, font})` ancla el diálogo junto a la cabeza que habla, sobre una placa difusa, con una entrada corta. Usa color para separar voces: blanco para lo que dice, acento para lo que piensa.
- **Cita.** `cita(c, t, {lineas, autor, inicio, fin}, {x, y, font, escalonado})` hace entrar cada línea con un fundido y una subida corta, y funde todo al final.
- **Tiempo de lectura.** `lecturaMinima(texto)` calcula ~3 palabras/s + 0,6 s. Es el mínimo; súmale la pausa que pida la escena.
- **Contexto.** Todas reciben el contexto donde dibujar, también el lienzo de un plano dentro de una transición. `crearTexto` acepta `op.ctx` con el mismo fin.

## Determinismo

- El kit no guarda estado entre fotogramas.
- `crearTransiciones`, `crearProfundidad` y `crearEscritura` crean sus lienzos una vez y los limpian (`reset()`) cada vez que los usan.
- Partículas, marcas y bokeh sembrado dependen solo de su semilla, su índice y t.

Si añades piezas propias, sigue las mismas reglas: crea lienzos y cachés al cargar, nunca dentro de `render(t)`, y comprueba con `node render.mjs --determinismo` incluyendo instantes en mitad de cada transición.
