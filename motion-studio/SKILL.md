---
name: motion-studio
description: >-
  Skill de Motion Studio, independiente del agente, para crear y renderizar un video nuevo (motion graphics, explicativo, promocional, short o video de YouTube) como una función pura del tiempo, `window.seek(t)`, renderizada con `node render.mjs` en Chrome sin interfaz, la GPU elegida por el usuario y FFmpeg (H.264 yuv420p). Úsala SIEMPRE que el usuario pida crear, empezar, montar, animar o renderizar un video nuevo, aunque no diga "Motion Studio"; también para dibujar un video con HTML/canvas/three.js, hoja de contacto, render por GPU o revisión de un video antes de exportarlo. También para EDITAR un video grabado (el usuario hablando a cámara, grabaciones de pantalla de OBS, tomas de recurso): quitar silencios, muletillas y tomas repetidas, montar la línea de tiempo y renderizarla con FFmpeg (modo edición, `references/edicion.md`). NO uses HyperFrames, Remotion ni ninguna otra skill o framework de video para esto, aunque su descripción coincida: este flujo las reemplaza.
---

# Motion Studio

Skill independiente del proveedor para cualquier agente capaz de leer instrucciones Markdown, trabajar con archivos, ejecutar comandos y revisar imágenes. Usa las herramientas equivalentes de tu entorno; no requiere comandos, APIs ni permisos propios de un agente concreto. Si falta una capacidad necesaria, comunica la limitación y solicita la revisión o ejecución correspondiente al usuario, sin darla por realizada.

Cada video es una función pura del tiempo: dado `t`, siempre dibuja el mismo fotograma. Eso permite renderizar en cualquier orden, en paralelo y repetir un fotograma exacto para revisarlo. Casi todas las reglas de abajo existen para no romper esa propiedad.

Ese contrato técnico no define el estilo: un video determinista también puede ser una presentación estática. El objetivo es realizar el lenguaje audiovisual del brief con acciones, evolución visual y montaje, no limitarse a reemplazar láminas con texto. El 2D es válido; ni el 3D ni añadir efectos corrigen por sí solos la falta de dirección.

Asume la dirección creativa y técnica. El usuario no necesita saber de animación: traduce su idea en narrativa, storyboard, actuación, cámara, transiciones y sonido. Lee `references/avisos-creativos.md` y usa avisos nativos de preguntas con opciones cuando estén disponibles: recomienda una alternativa concreta, explica el efecto visible en lenguaje sencillo y reserva las consultas para decisiones que cambien el resultado. Si no existe esa herramienta, usa un mensaje breve con las mismas opciones. No interrogues al usuario sobre técnicas que debes resolver tú.

| Fase | Trabajo que dirige el agente | Evidencia |
| --- | --- | --- |
| Preproducción | Idea, referencia, intención narrativa, dirección artística y storyboard. | Brief y planos revisables con acciones, poses, cámara, transiciones y sonido. |
| Producción | Recursos, animación, muestra representativa y desarrollo de la pieza. | Prueba animada con las dificultades principales resueltas antes de multiplicar planos. |
| Postproducción | Montaje, ritmo, continuidad, mezcla, correcciones y exportación autorizada. | Reproducción revisada y problemas documentados por plano/tiempo. |

Las fases organizan las decisiones y el trabajo dentro de los cuatro pasos siguientes. Reutiliza lo ya aprobado; no añadas consultas por rutina ni entregables que no ayuden a realizar o revisar la pieza.

## Dos modos

| Modo | Cuándo | Cómo |
| --- | --- | --- |
| **Animación** | El video se dibuja: motion graphics, explicativos, personajes, tipografía | Los pasos 0–4 de abajo (`window.seek(t)`, `render.mjs`) |
| **Edición** | El material está grabado: el usuario a cámara, pantallas de OBS, tomas de recurso | `references/edicion.md`: `nuevo.py --edicion`, `analizar.py` → `planificar.py` → `montaje.py` → `editar.py` → `qc.py` |

Las reglas comunes valen en ambos:
- autorizaciones;
- comprobación de herramientas (Paso 0);
- rúbricas con evidencia;
- `verificar.py` y `ritmo.py`;
- no dar por verificado lo que no se observó.

En el modo edición, los puntos de control son tres:
1. el corte en papel (`GUION-MONTAJE.md`) antes del primer render;
2. la muestra;
3. el primer completo.

Algunas partes del modo edición están pendientes: subtítulos, B-roll, gráficos con transparencia, música, color y
zooms animados. Si el usuario las pide, díselo antes de empezar (lista en `references/edicion.md` → "Estado").

## Paso 0: herramientas

Esta skill trabaja con herramientas concretas y el resultado depende de usarlas todas:
- `render.mjs` (Chrome sin interfaz + GPU + FFmpeg) para fotogramas, pruebas y exportaciones.
- `auditar.mjs` y `--determinismo` para el contrato.
- `--ritmo`/`ritmo.py` para el ritmo.
- `sheet.py` para las hojas de contacto.
- `audio/musica.py` para música, voz y −14 LUFS.
- `verificar.py` para comprobar la exportación antes de entregarla.
- Las fuentes instaladas para la tipografía.

Qué necesita cada una (sistemas, hardware, versiones, comandos de verificación y alternativas si falta algo) está en `references/requisitos.md`. Si el usuario pide algo que la skill no hace todavía (subtítulos desde una voz, capas con transparencia), díselo antes de empezar: consulta la sección de funcionalidades no disponibles. Para editar grabaciones reales, sigue `references/edicion.md` y sus límites actuales.

Al empezar cualquier video, comprueba que están listas. Desde la carpeta de esta skill:

```bash
python scripts/preparar.py --comprobar   # rápido; código 1 si falta algo
```

- **Si falta algo de nivel usuario** (Playwright, Chromium, fuentes, numpy, Pillow), ejecuta `python scripts/preparar.py` sin opciones. Se instala en las herramientas compartidas (`~/.motion-studio`, o `MOTION_STUDIO_HOME`), que usan todos los proyectos.
- **Si faltan Node.js o FFmpeg,** son programas del sistema: pide permiso al usuario antes de `python scripts/preparar.py --sistema` (winget, brew o apt), o dale el comando que indica el script.
- **No sustituyas una herramienta que falta** por otra vía, como capturas manuales, otro framework o una revisión "a ojo" en lugar de `--ritmo`. Si no se puede instalar, dilo y detente en ese paso.

`nuevo.py` ejecuta esta preparación al crear cada proyecto.

**Fuentes disponibles** (en `/node_modules/@fontsource/<nombre>/files/`, sin instalar nada más):
- **Interfaz y texto:** `inter`, `space-grotesk`, `montserrat`.
- **Titulares:** `bebas-neue`, `anton`, `archivo-black`.
- **Editorial:** `dm-serif-display`, `playfair-display`.
- **Rotulador:** `permanent-marker`.
- **Píxel:** `press-start-2p`, `silkscreen`.
- **Monoespaciada:** `jetbrains-mono`.

Elige del brief una para títulos y otra para la interfaz. Si la marca exige otra, instálala en el proyecto con `npm i @fontsource/<nombre>`.

## Antes de empezar

1. **Aclara la idea y el lenguaje antes de producir.** Lee `references/preproduccion.md` y `references/direccion-movimiento.md`. Revisa el contexto disponible y separa hechos, preferencias y supuestos. Define público, objetivo, mensaje principal, canal, duración, formato, tono, marca y audio. Si hay referencia, observa su acción, actuación, espacio y montaje: no basta con adoptar su tema o colores. Distingue infografía, tipografía cinética, demo de interfaz y corto narrativo con personajes. Pregunta solo por decisiones importantes que falten; si no hay referencias, propón una dirección concreta. Presenta un guion con acciones y estados antes/después, además de texto, composición, sonido y tiempos. No inventes funciones, métricas ni llamadas a la acción del producto.
2. **Pregunta antes de cualquier render.** Presenta la versión del brief, las decisiones pendientes y el alcance de la primera prueba. Pide aprobación explícita del brief/guion y autorización para crear el proyecto, capturar fotogramas y generar una prueba animada corta. Sin autorización para el modo correspondiente, no ejecutes `--frames`, `--prueba`, `--sheet`, `--determinismo`, grabaciones de navegador o exportaciones equivalentes; sin aprobación del brief no crees el proyecto. Una petición inicial de video, el silencio o tu propia evaluación no sustituyen esta aprobación. Si la misma versión ya está aprobada con ese alcance, no la vuelvas a pedir.
3. **No uses HyperFrames, Remotion ni ninguna otra skill o framework de video.** Todo se hace con HTML/JS propio y `render.mjs`. Así el usuario controla cada fotograma y el resultado es reproducible.
4. **La GPU la elige el usuario.** Si hay varias (p. ej. integrada y dedicada), confirma cuál quiere antes de capturar fotogramas. Chrome sin interfaz tiende a quedarse con la integrada, y el render por CPU (SwiftShader) es mucho más lento; por eso el valor por defecto es alto rendimiento y se avisa si no se obtuvo la GPU esperada. Detalle y solución de problemas en `references/gpu.md`.

## Paso 1: crear el proyecto

Localiza la carpeta instalada que contiene este `SKILL.md`. Resuelve `scripts/`, `assets/` y `references/` respecto a esa carpeta, independientemente del agente y de su ruta de instalación. Desde la carpeta de esta skill:

```bash
python scripts/nuevo.py <carpeta-del-video> [--nombre NOMBRE] [--gpu "RTX 3050"] [--duracion 75] [--fps 60] [--vertical] [--sin-preparar]
```

Copia `assets/plantilla/` a la carpeta del video, detecta las GPU y escribe la elegida en `motion.config.json`, junto con la duración, los fps y la orientación del brief (`--vertical` = 1080×1920). Si hay varias GPU y no pasaste `--gpu`, elige la dedicada y lo avisa: confírmalo con el usuario. Después ejecuta `preparar.py`: instala lo que falte a nivel de usuario y comprueba Node, FFmpeg y la GPU real (con `--sin-preparar` solo comprueba).

Guarda en `BRIEF.md` la dirección aprobada, sus fuentes, decisiones y alcance autorizado, con las palabras del usuario que lo confirman; en `STORYBOARD.md`, el guion por planos descrito en `references/preproduccion.md`, con su curva de energía (gancho, re-ganchos, pausas y clímax), cuyos tiempos van también a `motion.config.json` → `curva`. Cada plano usa la ficha breve de esa guía: intención, cámara y composición, iluminación, acción, sonido y enlace, con identificador y tiempos. Reutiliza las definiciones comunes por escena y completa los storyboards existentes sin duplicarlos. Antes de crear el proyecto, presenta ambos en conversación para revisarlos. Ajusta resolución, duración y fps de `motion.config.json` al brief antes de la primera captura; los valores de la plantilla son ejemplos.

La plantilla es una demostración técnica de continuidad de un objeto; reemplázala por el lenguaje acordado. Canvas 2D, SVG, DOM o Three.js son opciones según el brief, no identidades visuales predeterminadas. Registra también en `BRIEF.md` la ruta de la skill cargada para poder detectar instalaciones antiguas.

Qué contiene el proyecto:

| Archivo | Para qué |
|---|---|
| `index.html` | El video: define `window.seek(t)` y `window.ready`. Es una plantilla; se reemplaza `render(t)`. |
| `lib.js` | `mulberry32`, `srand`, catálogo `ease`, `claves()` (pose a pose), `resorte()`, `mezclar()`, `ruidoSuave()` y `crearTexto(ctx)` (texto determinista). |
| `kit/` | Cámara con encuadres, temblor y paralaje (`camara.js`); transiciones y montaje (`transiciones.js`); `ejemplo.html` completo. Guía en `references/kit.md`. No incluye personajes: se diseñan para cada pieza. |
| `render.mjs` | `--frames`, `--prueba=inicio,fin` (máximo 10 s, mezcla de `audio/final.wav` si existe; `--sin-audio` para una prueba muda), `--sheet`, `--determinismo`, `--ritmo`, `--borrador`, `--final`. Lee `motion.config.json`. |
| `auditar.mjs` | Auditor estático del contrato: busca `setTimeout`, `requestAnimationFrame`, `Math.random`, transiciones CSS, relojes reales, `fillText` directo y contextos 2D sin `ctx.reset()`. Ignora los scripts auxiliares `_*.mjs`. |
| `motion.config.json` | Resolución, fps, duración, GPU, calidad de codificación y salida. |
| `beats.json` | Cuadrícula de pulsos de la música; la escribe `audio/musica.py`. |
| `audio/musica.py` | Sintetiza música y efectos sobre la cuadrícula, mide los pulsos de una pista del usuario (`--pista`), mezcla una narración con ducking (`--voz`), deja `audio/final.wav` a −14 LUFS y verifica que la cuadrícula cae sobre los golpes reales. |
| `sheet.py` | Arma la hoja de contacto con los fotogramas por pulso. |
| `verificar.py` | Comprueba la exportación: códec, píxeles, resolución, fps, duración, fotogramas, sonoridad, true peak, etiquetas de color y tramos negros o congelados. Código 1 si falla una comprobación bloqueante; informe en `review/verificacion.json`. |
| `ritmo.py` | Mide el ritmo de un video (movimiento por segundo, tramos muertos, cortes, duración de plano y curva de energía por tramos frente a la apertura) y falla si se sale de `motion.config.json` → `ritmo` o si la energía decae fuera de las pausas declaradas en `curva`. Con `--referencia ... --calibrar` toma los umbrales de videos de referencia. |

Requisitos del equipo: los prepara `scripts/preparar.py` (Paso 0). `render.mjs` usa el Playwright del proyecto si lo hay y, si no, el de las herramientas compartidas. Sirve `/node_modules/...` desde el proyecto o, si el archivo no está allí, desde esas herramientas (así llegan las fuentes). Los scripts de diagnóstico que escribas van dentro del proyecto con un nombre que empiece por `_`. Para usar Playwright desde ellos, cárgalo con `createRequire(path.join(os.homedir(), '.motion-studio', 'package.json'))('playwright')` como hace `render.mjs`.

## Paso 2: construir el video

### Contrato de renderizado
- Cada fotograma lo dibuja `window.seek(t)` y nada más. No leas relojes, no guardes estado entre fotogramas.
- Nada de transiciones CSS, `setTimeout` ni `requestAnimationFrame` durante el renderizado: el render salta de un `t` a otro y esas cosas dependen del tiempo real.
- Si necesitas ruido, usa solo ruido con semilla determinista (`mulberry32`, ya en `lib.js`). Nunca valores aleatorios sin semilla.
- En canvas 2D, empieza `render(t)` con `ctx.reset()`: transformación, `lineCap`, `textAlign`, `font` y demás estado del contexto persisten entre llamadas a `seek` y hacen que un fotograma dependa del anterior.
- Dibuja todo texto con `texto()`/`numero()` de `crearTexto(ctx)` (en `lib.js`), nunca con `fillText` directo. Chrome cachea los glifos según lo que ya dibujó, y el mismo texto bajo escala o rotación puede variar un nivel de color según el orden de los `t`. Los contadores van con `numero()`, que compone carácter a carácter. Redondea las posiciones de texto que se desplazan.
- Se renderiza con `node render.mjs` y se codifica en H.264, `yuv420p`. Calidad: **CRF 16 en borradores** (`--borrador`) y **CRF 12 con preset slow en el render final** (`--final`); ambos valores se pueden cambiar en `motion.config.json`.

### Estilo visual
- **Parte del kit para el movimiento, la cámara y el montaje.** Lee `references/kit.md`; consulta o captura `kit/ejemplo.html` solo si necesitas comprobar una técnica, dentro del alcance autorizado. Úsalo para:
  - **movimiento:** `claves()` con anticipación → acción → rebote (`saleBack`, `resorte()`) → pose mantenida con vida (`ruidoSuave()`);
  - **cámara:** `encuadre()` desde el sujeto, con origen y destino acotados al foco narrativo; `temblor()` o `paralaje()` cuando la acción los justifique;
  - **enlaces:** `crearTransiciones().montaje()`.
- **Los personajes se diseñan para cada pieza**, no salen de una plantilla. Sigue los principios de la sección "Personajes" de `references/kit.md`:
  - dibuja solo lo que el plano necesita;
  - evita caminar de frente;
  - que el cuerpo entero participe del gesto;
  - movimientos escalonados y en arco;
  - la emoción, en primeros planos de la cara.

  Mover el personaje solo desplazándolo, animar un brazo con el resto congelado o una cámara que solo hace zoom queda por debajo del nivel de la skill. Prueba el gesto principal con `--prueba` antes de extenderlo a toda la pieza.
- Convierte el storyboard en acciones con intención narrativa. Aplica los criterios de cámara, poses y montaje de `references/direccion-movimiento.md`; elige técnicas según la referencia y el objetivo. El usuario elige la experiencia creativa, mientras el agente resuelve cómo realizarla.
- Lee `references/motion-graphics.md` al definir la dirección visual. Usa tipografía, formas, diagramas, datos o interfaces en movimiento para explicar el mensaje. Define un foco principal por escena y qué relación debe comunicar cada animación; no confundas cantidad de efectos con claridad.
- Evita la receta de titular, panel, etiquetas y fundido repetida en cada escena. No uses gradientes, brillos, partículas o movimientos de cámara como relleno; pueden servir cuando la dirección aprobada los justifique. Una lista de efectos prohibidos no sustituye la puesta en escena: diseña la acción principal y su consecuencia.
- En una escena narrativa, el personaje debe actuar e interactuar con su entorno, con poses y cambios legibles; no funcionar como un icono pequeño junto a párrafos. En una pieza gráfica, el objeto, diagrama o composición debe evolucionar con el mensaje. No conviertas una referencia narrativa en un dashboard sin acordar esa adaptación.
- Una tipografía para los títulos y otra para la interfaz. Un único color de acento, salvo que las especificaciones del proyecto indiquen lo contrario. Carga las fuentes con `FontFace` y espera `document.fonts.ready` antes de poner `window.ready = true`.
- Usa cambios cada 2 a 4 segundos como punto de partida, no como cuota de efectos: deja tiempo para leer, entender cifras y reconocer el producto. Si una escena necesita más tiempo, simplifica el contenido o extiende la pausa. La música acompaña esa comprensión.

### Sonido
- Respeta el audio acordado en el brief. Si se incluye música y efectos (SFX), se sintetizan por código, a menos que el usuario proporcione una pista. Si se pidió una pieza silenciosa, no añadas audio.
- Los impactos sonoros se sincronizan con la cuadrícula de tiempos musicales **medida** (`beats.json`), no con la supuesta. Los cambios visuales se anclan a esos mismos pulsos.
- Usa `audio/musica.py`. Ajusta `BPM`, `ACORDES` y `GOLPES` al storyboard y ejecútalo: escribe `beats.json`, deja `audio/final.wav` a −14 LUFS y comprueba con detección de golpes que la cuadrícula cae sobre el audio. Con una pista del usuario, `python audio/musica.py --pista tema.mp3` mide sus pulsos. Escúchala o contrasta el tempo informado; si sale al doble o a la mitad, repite con `--bpm` aproximado. Guarda los eventos (en pulsos) en un único archivo, p. ej. `eventos.json`, que lean tanto `index.html` como el script de audio: así el sonido y la imagen no se desincronizan al editar.
- Cuando haya audio, la sonoridad final es de **−14 LUFS**. Entrega la mezcla como `audio/final.wav`: `render.mjs` la une al video y avisa si su medición se aleja de −14.

### Narración
- Si la referencia o el brief llevan voz, decide con el usuario de dónde sale: una grabación suya, una voz de una herramienta de texto a voz disponible en tu entorno o, si no hay ninguna, texto en pantalla. Declara la limitación; no la sustituyas en silencio.
- Con voz, el guion manda: fija los tiempos de cada frase a partir del audio de la voz (duración real, no estimada) y ancla subtítulos y acciones a ellos. Mézclala con `python audio/musica.py --voz audio/voz.wav`, que baja la música mientras se habla.
- Sin voz, los textos en pantalla hacen de narración: frases cortas, dentro de la zona segura inferior, a un tamaño legible en móvil y con tiempo suficiente para leerlas.

## Paso 3: ciclo de revisión antes de mostrar cualquier resultado

No presentes una captura sin revisar como resultado definitivo. Tras la autorización de fotogramas, empieza por unas pocas imágenes de escenas clave para comprobar composición y tipografía antes de animar todo. Puedes mostrarlas como pruebas de estilo y pedir correcciones; una imagen estática no demuestra fluidez ni sincronización. Continúa la revisión dentro del alcance autorizado.

**Antes de extender el estilo a toda la pieza, prueba movimiento real en calidad alta.** Con autorización para ello, usa `node render.mjs --prueba=2,6` sobre un intervalo representativo ajustado a la duración del proyecto. La muestra usa resolución, fps y el perfil `codificacion.final` del proyecto, igual que `--final`, e incluye el intervalo correspondiente de `audio/final.wav` si existe. Si falta la mezcla o usas `--sin-audio`, declara pendiente la sincronización; una prueba muda no aprueba el sonido. Sigue `references/direccion-movimiento.md`: reproduce y muestra la prueba y valida acción, enlace entre planos y acabado. Ofrece «Aprobar y generar el video completo en esta calidad»; aceptar esa opción autoriza continuar con `--final` y evita una segunda aprobación idéntica. Si solo se autorizaron imágenes, pide ampliar el alcance a la muestra. No afirmes que el movimiento quedó validado con imágenes fijas.

**Antes de la hoja de contacto, comprueba el contrato con dos herramientas automáticas.** La auditoría estática y la comparación de fotogramas detectan ciertas violaciones; no demuestran por sí solas la corrección de todos los instantes ni la calidad audiovisual:

```bash
node auditar.mjs                # revisa el código: ERROR si rompe una regla del contrato, AVISO si hay un reloj real
node render.mjs --determinismo  # renderiza los mismos t repetidos y en orden inverso y compara cada fotograma
```

Corrige todo ERROR y toda diferencia antes de seguir. Un AVISO se revisa: si el reloj o la animación no afecta al fotograma, se puede dejar, pero hay que saber por qué. Los 10 instantes por defecto están repartidos por igual; añade con `--t=...` al menos uno por escena y los instantes con texto que cambia (contadores, títulos con escala).

Si `--determinismo` falla, guarda ambas capturas en `review/determinismo/` y dice cuántos píxeles difieren, el Δ máximo y la zona:
- **Δ de 1–2 niveles en bordes de texto:** es la caché de glifos. Dibuja ese texto con `crearTexto` en lugar de `fillText`.
- **Δ grande en formas o colores:** hay estado que se arrastra entre fotogramas (un acumulador, una caché que cambia, un contexto 2D sin `ctx.reset()`) o algo que depende del orden de los `t` o del reloj.

Abre las dos imágenes de la zona antes de cambiar código.

**Mide el ritmo antes de puntuar la animación.** Una hoja de contacto muestra cada fotograma bien compuesto, pero no deja ver que 20 segundos seguidos son casi iguales. Con autorización para capturar fotogramas:

```bash
node render.mjs --ritmo     # vista del video entero a 10 fps -> review/ritmo/vista.mp4, y la analiza con ritmo.py
```

`ritmo.py` informa del movimiento mediano por segundo, el porcentaje de tiempo con solo micromovimiento (respiración, deriva lenta), la racha muerta más larga, los cortes por minuto y la duración media de plano. Dibuja además una línea de tiempo y falla si se superan los umbrales de `motion.config.json` → `ritmo`.
- **La energía se mide por tramos, no en promedio.** `ritmo.py` divide la pieza en tramos de 15 s (una cuarta parte en piezas de menos de 60 s) y los compara con la apertura. Falla si un tramo cae por debajo de la mitad del movimiento de la apertura con al menos un 30 % de tiempo quieto, o si dos tramos seguidos pasan del 50 % de tiempo quieto. Avisa si un re-gancho de `motion.config.json` → `curva` no se ve en el video o si hay demasiado tiempo entre dos. Con sonido, avisa también si los golpes sonoros o el nivel caen tras la apertura, o si el estéreo es estrecho y no cambia. Esa curva se planifica en el storyboard (`references/preproduccion.md`, "Curva de energía y re-ganchos"); aquí solo se comprueba.
- **Los umbrales vienen del estilo buscado.** Si el usuario da videos de referencia, calíbralos con `python ritmo.py --referencia a.mp4 b.mp4 --calibrar`. Así el umbral es el peor caso de esas referencias, no un número inventado.
- **Si falla, no se arregla con efectos.** No añadas grano, partículas ni zooms lentos: cuentan como movimiento sin aportar nada. En cada tramo señalado, revisa primero la acción y su consecuencia. Corrige actuación, duración o cobertura según el relato; una cámara fija puede ser correcta. Comprueba que el foco y el texto necesario permanecen dentro del cuadro durante todo el movimiento, incluido su máximo acercamiento.
- **Un tramo quieto puede ser una decisión.** Si es intencionado (una pausa dramática, un silencio), decláralo en `motion.config.json` → `curva` → `pausas` como `[inicio, fin, "motivo"]` y anótalo en `REVISION.md`. Si la energía decae sin estar planificado, vuelve al storyboard y pon un re-gancho ligado al contenido; no lo tapes con efectos.

1. Renderiza un fotograma por cada pulso musical y reúnelos en una hoja de contacto:
   ```bash
   node render.mjs --sheet
   python sheet.py            # -> review/sheets/sheet_XX.jpg
   ```
   Abre las hojas con la herramienta de lectura de imágenes y examínalas de verdad; no puntúes de memoria.
2. Evalúa cada aspecto del 1 al 10 con las rúbricas de `references/rubricas.md`. Allí está cada funcionalidad con su escala, sus condiciones de aprobación, los errores frecuentes y la comprobación automática que la cubre. Una comprobación bloqueante que falle limita esa funcionalidad a 4, y la nota global no puede superar en más de 1 punto a la peor. Aspectos:
   - Claridad del mensaje principal para el público del brief.
   - Capacidad de la apertura para atraer y orientar según el público y canal del brief.
   - Legibilidad en pantallas de teléfonos móviles.
   - Calidad de la acción, continuidad y fluidez, observadas en reproducción. Un fallo de `--ritmo` exige diagnóstico y evidencia; su resultado no fija la nota artística ni demuestra calidad al pasar.
   - Puesta en escena: encuadres, cámara, poses y transiciones que aporten al relato.
   - Fidelidad a la identidad de marca.
   - Sincronización entre sonido y animación.
3. Corrige los 3 problemas más graves y vuelve al paso 1, buscando al menos 8/10 en los criterios aplicables. Anota en `REVISION.md` evidencia concreta (escena/tiempo, problema y corrección), no solo puntajes. Comprueba también que el guion cumple el brief y que las afirmaciones tienen respaldo. Como pauta, realiza hasta tres rondas; si persisten defectos, presenta los pendientes y acuerda cómo continuar, sin subir notas para poder avanzar. No puntúes sonido o fluidez que no hayas podido observar: márcalos pendientes y planifica su comprobación en el primer video completo de calidad alta. Marca «no aplica» cuando un criterio no corresponda al brief, como sincronización sonora en una pieza silenciosa.
4. **Conecta la aprobación de la muestra con el video completo.** Antes del aviso, muestra la prueba revisada y resume versión, duración, orientación, audio, entrega y pendientes con palabras sencillas. La opción recomendada, cuando la muestra cumple lo acordado, es «Aprobar y generar el video completo en esta calidad»: autoriza realizar la pieza completa con `--final`, conservando el acabado, resolución, fps, recursos y perfil de codificación aprobados. Registra el alcance en `BRIEF.md`. Una vez aceptado, continúa sin pedir de nuevo la misma aprobación. Si el usuario solo expresó que le gusta y aún no autorizó la exportación, usa ese aviso breve para concretarla. Ofrece ajustar la muestra o un borrador reducido solo como alternativa explícita; nunca interpongas este último automáticamente. Confirma únicamente cambios sustanciales de alcance o calidad.

## Paso 4: renderizado completo

Tras aceptar «Aprobar y generar el video completo en esta calidad», desarrolla y revisa la pieza y ejecuta directamente `--final`. El primer video completo es una entrega de revisión en calidad alta: todavía puede recibir correcciones narrativas, visuales o sonoras. Mantén el perfil aprobado; «borrador» como estado de revisión no significa reducir resolución, fps o calidad. `--borrador` queda disponible solo si el usuario pide expresamente esa alternativa. No ocultes defectos pendientes por haber superado las pruebas técnicas.

```bash
node render.mjs --final      # primer completo con la calidad aprobada -> exportaciones/<nombre>.mp4
# Solo si el usuario solicita una copia reducida para revisar:
# node render.mjs --borrador  # perfil borrador, no es un paso obligatorio
```

- Al arrancar imprime el renderizador WebGL real. Comprueba que sea la GPU esperada; si avisa de SwiftShader o de otra GPU, detente y arréglalo (`references/gpu.md`) en vez de esperar un render lento.
- Renderiza por segmentos de 5 s: si se interrumpe, al relanzar solo rehace los que faltan.
- Verifica el archivo final con `python verificar.py` antes de entregarlo.
  - **Falla (código 1)** si el códec no es H.264, los píxeles no son `yuv420p`, la resolución, los fps, la duración o el número de fotogramas no coinciden con `motion.config.json`, los fps son variables, falta el audio o no está a −14 ±1 LUFS, audio y video duran distinto, o hay negro de 1 s o más sin declarar.
  - **Avisa** del color sin etiquetas BT.709, del pico por encima de −1 dBTP y de la imagen congelada 4 s o más.
  - Corrige los fallos antes de entregar y menciona los avisos al usuario.
- Pasa `python ritmo.py exportaciones/<nombre>.mp4` al primer completo en calidad alta: confirma con el video codificado lo que midió `--ritmo`.
- Reproduce el primer completo en calidad alta, o la versión disponible dentro del alcance autorizado, para revisar ritmo, transiciones, lectura y audio cuando tu entorno lo permita. Un conjunto de imágenes y una medición de LUFS no sustituyen esa revisión; declara cualquier comprobación audiovisual pendiente y solicita ayuda del usuario si hace falta.

## Ejemplos

`assets/ejemplos/lectura-xeon/` trae las herramientas que usó el proyecto XEON para medir el tiempo de lectura de los textos. Están ligadas a ese proyecto (su escenario 3D y sus textos) y **no forman parte del flujo por defecto**: úsalas solo como referencia si el usuario pide medir la lectura.
