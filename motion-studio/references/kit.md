# Kit de movimiento: curvas, cámara y transiciones

El proyecto trae en `kit/` y `lib.js` piezas para el movimiento, la cámara y el montaje, que son iguales en cualquier estilo. Lo que se ve (personajes, objetos, escenarios) se diseña para cada pieza. El kit ofrece recursos; un plano fijo o un corte directo son válidos cuando sirven al relato.

Ejemplo completo y funcionando, pensado para 1080×1920, unos 8 s:

```bash
node render.mjs --pagina=kit/ejemplo.html --frames=1.2,3.6,6.5
```

Consúltalo si necesitas un ejemplo de estructura: planos como funciones, montaje con transiciones, principios de animación con `claves()` y `resorte()` (una pelota con anticipación, aplastamiento y rebote) y cámara calculada desde el sujeto.

Carga, en este orden: `lib.js`, `kit/camara.js` y `kit/transiciones.js`. La plantilla `index.html` ya los incluye.

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

Un buen enlace conserva algo entre los planos: posición, forma, dirección del movimiento o color.

## Determinismo

- El kit no guarda estado entre fotogramas.
- `crearTransiciones` crea sus lienzos una vez y los limpia (`reset()`) cada vez que los usa.

Si añades piezas propias, sigue las mismas reglas: crea lienzos y cachés al cargar, nunca dentro de `render(t)`, y comprueba con `node render.mjs --determinismo` incluyendo instantes en mitad de cada transición.
