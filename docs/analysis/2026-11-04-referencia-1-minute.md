# Referencia: técnicas de «1 MINUTE | An Animated Short Film» (Last Soul)

- **Video:** https://www.youtube.com/watch?v=NeWlC4bJTMs. Dura 4:59 y se analizó en 1080p (YouTube lo ofrece hasta 1440p).
- **Capítulos del autor:**
  - 0:00 Big Plans
  - 1:03 Giving Up
  - 2:10 One Minute
  - 2:57 Day by Day
  - 4:06 Where It Takes You
- **Fecha del análisis:** 4 nov 2026.
- **Estado:** la fase 1 de la integración está implementada en el kit (ver «Integración» y `CHANGELOG.md`). Las fases 2 y 3 siguen como propuesta.

## Cómo se analizó (para no inventar)
1. **Cortes y movimiento.** Se reprodujo el video en el navegador y se tomó un fotograma cada 0,2 s (1.495 muestras). De cada uno se midió la diferencia con el anterior y la luminancia.
   - Resultado: **96 cortes** y **97 planos**.
   - La **duración media de plano es ~3,0 s**, contando desde 0:04,2, cuando termina el negro inicial.
   - Hay 5 tramos a negro: 0:00–0:04,2, 0:28,4–0:30, 2:30,4–2:32,2, 2:56–3:02,6 y 3:37–3:43,6.
2. **Revisión visual.** Se armaron hojas de fotogramas con el punto medio de cada plano. En los planos con movimiento se revisaron secuencias cada 0,3–1 s.
3. **Movimiento de cámara medido.** Se compararon pares de fotogramas del mismo plano buscando la escala y el desplazamiento que mejor encajan. Una escala de 1,02 equivale a un acercamiento del 2 %.
4. **Guion de color medido.** Se calculó la saturación media cada 10 s.
5. **Límites del análisis.**
   - El audio no se analizó.
   - El software con que se hizo **no es observable**. Lo que se dice de cómo se hizo va marcado como **inferido**.

## Lo que define el estilo (resumen)
- **Personajes:** siluetas negras planas con ojos blancos; la emoción vive en los ojos y las cejas.
- **Fondos:**
  - **Interiores:** grises casi monocromos (saturación del 7–12 %).
  - **Exteriores nocturnos:** con **perspectiva 3D real**; las farolas y las casas cambian de perspectiva cuando la cámara avanza.
- **Cámara:**
  - en interiores, quieta o con **acercamientos lentos del 1–2 %**;
  - en exteriores, avanza o acompaña;
  - **no hay cámara en mano**: los planos medidos tienen desplazamiento 0.
- **Montaje:** casi todo es **corte seco**. La única transición «de efecto» es la **apertura de párpados**. El tiempo se comprime con **montajes de rutina que se aceleran**.
- **Guion de color:**
  - empieza gris (7–12 %);
  - se enciende en las carreras nocturnas (23–29 %);
  - estalla en la colina final (38–45 %);
  - vuelve a gris en la tienda.
- **Conclusión:** la calidad cinematográfica no sale de efectos llamativos. Sale de la **composición en profundidad**, la **luz motivada**, la **profundidad de campo**, la **contención** y el **color como arco emocional**.

## Tabla de efectos

Leyenda de viabilidad en `/motion-studio`: ✅ alta (encaja ya, poco trabajo) · 🟡 media (módulo nuevo) · 🔴 baja (cambia la arquitectura o el costo es alto).

| # | Efecto | Timestamps (medidos) | Funcionamiento observado y propósito | Implementación técnica (inferida → cómo la haríamos) | Herramientas gratuitas | Viabilidad |
|---|---|---|---|---|---|---|
| 1 | **Personaje silueta** (negro plano, ojos blancos con párpado y ceja) | Todo el video; p. ej. 0:04–0:08, 1:08,9, 2:28, 3:35 | Se lee al instante sobre fondos claros y es universal (sin rasgos ni etnia). Expresa con 3 piezas: ojos, párpados y cejas. Es barato de animar. | Relleno negro del cuerpo; ojos = elipses blancas recortadas por el párpado (el rig `stick.js` de Ojalá No ya lo hace) y cejas = trazos. Sería un modo `silueta` del rig (piel y ropa en `#0B0B0B`, sin luz de relleno, solo contorno de luz). | Canvas 2D | ✅ |
| 2 | **Exteriores 3D estilizados con cámara que avanza o acompaña** | 2:44–2:47 (la farola crece y pasa; las casas cambian de perspectiva); 3:09–3:10 (el corredor queda fijo en cuadro y la calle se mueve: *tracking*); 3:13 parque | Da escala, viaje y la sensación de «salir al mundo». Contrasta con los interiores quietos. | **Inferido:** escena 3D con sombreado plano (sin texturas), niebla por distancia y faroles emisivos; el personaje es 2D encima o un plano con su dibujo. **Nuestra versión:** Three.js con cámara en curva calculada desde `t`, `MeshBasicMaterial`/`MeshToonMaterial`, `scene.fog`, sprites para los halos y el personaje como textura de canvas (*billboard*), todo renderizado bajo demanda en `seek(t)`. | Three.js; pmndrs/postprocessing para bloom; Blender (bpy) si se prefieren fondos prerenderizados | 🔴 (módulo 3D completo) |
| 3 | **Profundidad de campo** (primer plano o fondo desenfocado, bokeh) | 0:09,9 (silueta de espaldas desenfocada); 1:08,9 (ventana desenfocada); 3:15 (reloj nítido con bokeh naranja de árboles); 4:18–4:22 (pasto cercano desenfocado) | Separa planos, guía la mirada y da un acabado «de lente». | Capas por profundidad en lienzos separados, cada una con `ctx.filter = blur(k·|z−foco|)`. El **bokeh** se dibuja en la capa lejana con discos brillantes de borde suave en modo `lighter`. Para el foco que cambia (*rack focus*), se anima `foco` con `claves()`. | Canvas 2D (filter blur, ya determinista en nuestro render); pmndrs `DepthOfFieldEffect` en 3D | ✅ |
| 4 | **Plano sobre el hombro** (silueta grande en primer plano) en diálogo | 0:09–0:20; 1:38–2:07 (1:38,5, 1:44,7, 1:54,7, 1:59,8, 2:06,1); 4:34–4:47 | Construye espacio y relación entre los dos. El plano/contraplano mantiene la dirección de pantalla. | Primer plano grande desplazado al borde, más oscuro y desenfocado (efecto 3); el interlocutor a un tercio. Es una plantilla de encuadre en `camara.js` (`encuadre('hombro', …)`). | Canvas 2D | ✅ |
| 5 | **Acercamiento lento** en planos fijos | Medido: 1:26–1:28,4 (+2 %), 1:40,6–1:42,9 (+2 %), 1:54–1:56,8 (+1 %), 0:04,6–0:08,2 (~+6 %, con el personaje caminando) | Mantiene vivo un plano quieto sin que se note, y sube la tensión del diálogo. | Escala 1,00 → 1,01–1,02 por cada 2–3 s, lineal o con `ease.suave`, hacia el punto de interés. Puede ser un preset «respira» de la cámara. | Canvas 2D (`aplicarCamara`) | ✅ |
| 6 | **Detalle extremo y alejamiento que revela** | 0:59,4–1:06,4: detalle de las X rojas del calendario, paneo y alejamiento medido de ≥6 % en 1,3 s (1:05,0–1:06,3) hasta revelar la nevera | Acumula el fracaso («todas tachadas») y después muestra su contexto. | Claves de cámara: detalle (escala 3–4×) → paneo sobre el objeto → alejamiento con `easeInOutCubic`. Hay que dibujar el detalle a resolución de pantalla (el rig ya rasteriza a escala). | `encuadre()`, `claves()` | ✅ |
| 7 | **Montaje de rutina que se acelera** | 0:35–1:00, con cortes en 35,4 · 36,6 · 37,4 · 38,8 … 57,0 · 57,8 · 58,6 · 59,4 s (planos de ~1,2–2 s que bajan a 0,4–0,8 s); y 3:02–3:18 (planos de 1,5–2 s, con los km del reloj subiendo: 0,69 → 1,41 → 2,94 → 5,00) | Comprime semanas en segundos. La aceleración transmite frustración y el crecimiento de los números transmite progreso. | Lista de cortes generada por una curva: `d_i = d0·(d1/d0)^(i/n)`. Cada repetición es **el mismo plano con un parámetro distinto** (día, excusa, km). Va en `eventos.json`, como hoy. | `claves()`; un ayudante nuevo `aceleracion(n, d0, d1)` | ✅ |
| 8 | **Motivo visual que rima** (alarma 5:30, calendario que cambia) | Celular a las 5:30 en 0:31, 0:39, 0:51, 2:35, 3:03, 3:24, 3:48, 3:53. Calendario: «10K EVERY DAY» con X (0:35–1:06) → «1 MIN» (2:19–2:24) → «1 MIN EVERY DAY» con chulos verdes (4:08) | El público mide el progreso con el mismo objeto. | Una sola función de plano con estado (`dia`, `marcas[]`), llamada en distintos momentos. | Canvas 2D | ✅ |
| 9 | **Transición de párpados** (punto de vista del personaje al despertar) | 0:28,4–0:30,2 · 2:30,4–2:32,5 · 3:02,3–3:03 | Pasa al «día siguiente» en primera persona. El negro se abre en una rendija horizontal con la imagen desenfocada, que después se enfoca. | Dos máscaras negras (arriba y abajo) con borde curvo que se separan con `ease.suave`, a veces con un parpadeo de 2 tiempos. La imagen de debajo va con `blur` de 12 → 0 px y viñeta. | Canvas 2D (máscara + filter) | ✅ (tipo nuevo `parpados` en `transiciones.js`) |
| 10 | **Escritura a mano sincronizada con el rotulador** | 2:19–2:24,4 («1 MIN» trazo a trazo siguiendo la punta); X rojas 0:35–0:59 | El gesto de escribir es la decisión del personaje y se ve suceder. | Letras como trazos de una sola línea (*centerline*), revelados por longitud acumulada (`setLineDash` + `lineDashOffset`, o un trazo parcial). La mano sigue el punto `p(L(t))`. Textura de rotulador con trazo irregular sembrado. | Canvas 2D; fuentes de un solo trazo (Hershey, dominio público); opentype.js para contornos de fuentes normales; Rough.js (con semilla) para el trazo de rotulador | ✅ |
| 11 | **Diálogo como texto junto al hablante** | 0:09,9 (la vendedora propone empezar por algo pequeño); 1:38–2:07; excusas en naranja junto al celular: 0:40,4 (el clima), 0:52 (el cansancio), 0:59 (es domingo) | Pone el diálogo en el espacio de la escena; el color separa el pensamiento (naranja) del diálogo (blanco). | `crearTexto` con placa oscura de bordes suaves (sombra con blur) anclada a la cabeza del hablante con desfase; entra con un fundido y una escala de 0,96 → 1 en 0,15 s. Hay que respetar la regla de tiempo de lectura del usuario. | Canvas 2D | ✅ |
| 12 | **Tarjeta de cita sobre negro, revelada por líneas** | 2:56–3:02,4 (cita sobre que nada grande se crea de repente: 2 líneas + atribución); 3:37–3:43,6 (cita sobre el hábito de presentarse cada día: 1 línea + atribución) | Pausa reflexiva entre capítulos; cambia el ritmo. | Tipografía con serifa centrada; cada línea entra con fundido y subida de 6 px, con un escalonado de ~0,8–1 s; se sostiene; fundido a negro y párpados (efecto 9). | Canvas 2D | ✅ |
| 13 | **Interfaz dentro de la escena** (alarma, reloj inteligente, hoja de cálculo) | Celular 0:31–0:59 (botón SNOOZE); reloj 2:42 (temporizador de 1:00), 3:56–3:57 (1:00 → 0:59) y 3:08–3:18 (km); portátil 3:25–3:32,6 (el título cambia «10K» → «8K» → «1 MIN EVERY DAY», las celdas cambian de color); la cara iluminada por la pantalla 3:28 | Cuenta el cambio de plan con objetos reales y números legibles. | Componentes de interfaz dibujados (rectángulos redondeados, `numero()` para los contadores, cursor que escribe carácter a carácter). La luz de la pantalla sobre la cara es la luz emisiva del rig. | Canvas 2D / DOM | ✅ |
| 14 | **Luz nocturna motivada** (halo de farola, charco de luz, niebla, ventanas cálidas) | 2:44–2:52; 3:06–3:10; 3:56–4:06 | Da atmósfera y profundidad, y guía la mirada al personaje. | Halo con gradiente radial en modo `lighter`; charco elíptico en el suelo; niebla con gradiente por capa de profundidad; ventanas emisivas. En 3D: `UnrealBloomPass` o el bloom de pmndrs y `scene.fog`. **Ya existe** en `stick.js` (`halo`, `haz`, `tramado`), pero no en el kit de la skill. | Canvas 2D; Three.js + postprocessing | ✅ (llevar `halo`/`haz` al kit) |
| 15 | **Lluvia + un solo acento de color** (impermeable amarillo en la noche desaturada) | 3:56–4:06 (el corredor se acerca y sale de cuadro en 4:04,8) | Muestra la adversidad (lluvia) y la constancia (el acento lo hace protagonista). | Partículas deterministas: `y = (y0 + v·t) mod H` con semilla `mulberry32`, en trazos con alfa, más brillantes dentro del cono de luz (multiplicar por la máscara del haz) y salpicaduras en el suelo. El acento es la única fuente de saturación del plano. | Canvas 2D | ✅ |
| 16 | **Paso del tiempo con estaciones** (hojas que caen, árboles naranja, lluvia, verde) | Hojas 0:27, 0:38, 0:57, 1:18; otoño 3:13–3:15; lluvia 3:56; verde 4:14 | Marca semanas y meses sin rótulos. | Paleta y utilería por tramo; partículas de hojas con caída sinusoidal sembrada. | Canvas 2D | ✅ |
| 17 | **Guion de color** (gris → saturado → gris) | Saturación media: 7–12 % en la tienda y la casa (0:06–2:26), con picos de 18–19 % en los planos azules del celular · 23–29 % en las carreras (2:36–3:16) · 38–45 % en la colina (4:16–4:26) · 8–12 % en la tienda final (4:36–4:46) | Arco emocional: inercia gris → esfuerzo → recompensa a todo color. | Paletas por acto (fichas de color) y, si hace falta, una gradación global con `ctx.filter = saturate()`. **Se puede medir** con la misma curva de saturación que usé aquí (añadirla a `ritmo.py`). | Canvas 2D; FFmpeg `eq`/`lut3d` para gradación final | ✅ |
| 18 | **Puesta en escena en profundidad** (el personaje se acerca o se aleja de cámara) | 0:04–0:08 (Greg camina del primer plano al mostrador y se hace pequeño); 4:03–4:05 (el corredor viene hacia cámara y sale) | Da volumen a planos fijos y una entrada o salida con energía. | Escala por profundidad `s = f/z` y pies sobre el plano del suelo (horizonte fijo); se ordenan las capas por `z`. | Canvas 2D (el rig ya escala) | ✅ |
| 19 | **Plano cenital** | 3:04,6 (salta de la cama visto desde arriba) | Rompe la rutina visual del montaje; da energía. | Pose del personaje vista desde arriba (cabeza y hombros en escorzo). Requiere poses nuevas del rig. | Canvas 2D | 🟡 |
| 20 | **Revelación final en paisaje a color** (plano general y alejamiento con inclinación) | 4:14–4:16,8 (colina con el camino serpenteante; cámara quieta, escala 1,00 medida); 4:18–4:22 (cima, pasto cercano desenfocado, valle con pueblo); 4:22,2–4:24,6 (alejamiento e inclinación medidos: escala 0,99, dy −5 px) | Recompensa visual del arco: amplitud, color y horizonte. | Capas: cielo, nubes (deriva), pueblo lejano, colina, pasto cercano desenfocado; `paralaje()` con una cámara que se aleja e inclina. | Canvas 2D (`paralaje`) | ✅ |
| 21 | **Viñeta y desenfoque suave en los detalles del celular** | 0:40, 0:43, 0:56 | Intimidad y hora temprana; centra la mirada en la pantalla. | Gradiente radial oscuro y utilería desenfocada (efecto 3). | Canvas 2D | ✅ |
| 22 | **Corte seco como norma y negro entre capítulos** | 96 cortes. Negros en 0:00–0:04,2, 0:28,4–0:30, 2:30,4–2:32,2, 2:56–3:02,6, 3:37–3:43,6 y el final 4:49–4:59 | Contención: la emoción la cargan la imagen y el ritmo, no las transiciones. | `corte` (por defecto en `montaje()`) y fundidos a negro en los cambios de capítulo. | Canvas 2D | ✅ |

**Lo que NO se observó** (para no copiarlo por error):
- no hay parallax 2D de muchas capas como recurso principal: los exteriores son perspectiva 3D;
- no hay cámara en mano ni temblor;
- no hay barridos, zooms a través ni destellos.

## Herramientas gratuitas: comparación para hacerlas por código y con agentes

| Herramienta | Licencia | Sirve para | ¿Determinista con `seek(t)`? | Encaje con `/motion-studio` |
|---|---|---|---|---|
| **Canvas 2D** (lo actual) | — | Siluetas, interfaz, texto, capas con blur, partículas, máscaras y transiciones | Sí (ya está demostrado) | Es la base: cubre 18 de los 22 efectos |
| **Three.js** | MIT | Exteriores 3D estilizados, cámara en curva, niebla | Sí, si la cámara y la animación salen de `t` y se renderiza bajo demanda | La skill ya lo admite (`comprobarPuntos3D`); falta un módulo de composición 2D + 3D |
| **pmndrs/postprocessing** | zlib | Bloom, profundidad de campo física, viñeta y ruido en WebGL | Sí, sin efectos con historial temporal (TAA, desenfoque de movimiento acumulado) | Medio: solo junto con Three.js |
| **PixiJS + pixi-filters** | MIT | Filtros 2D por GPU (blur, bloom, desplazamiento) | Sí, con render manual | No hace falta: Canvas 2D ya cubre el blur |
| **opentype.js** | MIT | Contornos de fuentes para texto que se escribe solo | Sí | Alto, para el efecto 10 con tipografías normales |
| **Fuentes de un solo trazo** (Hershey) | Dominio público | Escritura a mano trazo a trazo | Sí | Alto (efecto 10) |
| **Rough.js** | MIT | Trazos de rotulador o boceto con semilla | Sí (con `seed`) | Medio: textura de rotulador |
| **Blender** (bpy, EEVEE, Grease Pencil, Freestyle) | GPL | Fondos 3D prerenderizados, profundidad de campo real, cámaras complejas | Sí (por fotograma) | Bajo-medio: es otro programa; en la skill solo serviría para placas de fondo en imagen |
| **FFmpeg** (`eq`, `lut3d`, `vignette`, `gblur`) | LGPL/GPL | Gradación final, LUT, viñeta en postproducción | Sí | Alto: ya está en el pipeline |
| Natron · OpenToonz · Synfig | GPL / BSD / GPL | Composición nodal y animación 2D tradicional | — | Bajo: se manejan con interfaz gráfica, no los opera bien un agente |
| Motion Canvas · Revideo · Remotion · HyperFrames | Varias | Animación por código | — | **Excluidos:** la regla de la skill prohíbe otros frameworks de video |

## Integración en `/motion-studio`

**Fase 1: implementada el 4 nov 2026**
1. **`kit/profundidad.js`** (efectos 3, 4 y 21):
   - `crearProfundidad().componer()`: capas por `z` con desenfoque relativo al foco, niebla por distancia y cambio de foco animable;
   - `bokeh()` y `bokehSembrado()`;
   - `encuadreHombro()` en `camara.js`.
2. **Transición `parpados`** en `kit/transiciones.js`, con uno o dos parpadeos (efecto 9).
3. **`kit/escritura.js`** (efecto 10):
   - `crearTrazado()` y `escribir()`, con la punta que sigue el trazo;
   - `marcaX()`, `marcaCheck()`, `circuloAMano()` y `subrayado()`;
   - `crearEscritura().revelar()` para texto ya compuesto.
4. **`kit/textos.js`**:
   - `bocadillo()` anclado al hablante (efecto 11);
   - `cita()`, revelada línea a línea (efecto 12);
   - `lecturaMinima()`.
5. **Cámara y montaje** (efectos 5 y 7):
   - `respira()`, un acercamiento del 1–2 % hacia un punto fijo en pantalla;
   - `proyectar()`, para anclar elementos a la cámara;
   - `aceleracion()` en `transiciones.js`.
6. **`kit/particulas.js`** (efectos 15 y 16): `lluvia()` con luz por zona, `salpicaduras()`, `hojas()` y `polvo()`.
7. **`kit/luz.js`** (efecto 14): `halo()`, `haz()`, `charco()`, `nieblaHorizonte()`, `vineta()` y `tramado()`, generalizados desde el proyecto de Ojalá No.
8. **`ritmo.py`** (efecto 17): saturación y luminancia por tramo, y aviso si se declara `curva.color`.

**Fase 2: módulos medianos**
- Modo **silueta** del rig (efecto 1).
- Puesta en escena en profundidad con escala por `z` (efecto 18).
- Componentes de interfaz: alarma, reloj, hoja (efecto 13).
- Poses cenitales (efecto 19).

**Fase 3: alto costo**
- **Exteriores 3D en Three.js** con el personaje 2D compuesto (efecto 2). Hay que:
  - resolver la composición de dos lienzos;
  - mantener el determinismo;
  - medir el rendimiento en la RTX 3050;
  - hacer una prueba de 10 s antes de adoptarlo.

**Herramienta extra recomendada:** un **analizador de referencias** que reutilice el método de este análisis: cortes, duración de plano, cámara medida y curva de saturación. Funcionaría sobre un archivo local o sobre el navegador. Así cada referencia deja datos, no impresiones. Hoy `ritmo.py --referencia` existe, pero necesita el video descargado.
