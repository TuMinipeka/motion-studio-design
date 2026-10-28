---
name: motion-studio
description: >-
  Skill de Motion Studio, independiente del agente, para crear y renderizar un video nuevo (motion graphics, explicativo, promocional, short o video de YouTube) como una función pura del tiempo, `window.seek(t)`, renderizada con `node render.mjs` en Chrome sin interfaz, la GPU elegida por el usuario y FFmpeg (H.264 yuv420p). Úsala SIEMPRE que el usuario pida crear, empezar, montar, animar o renderizar un video nuevo, aunque no diga "Motion Studio"; también para dibujar un video con HTML/canvas/three.js, hoja de contacto, render por GPU o revisión de un video antes de exportarlo. NO uses HyperFrames, Remotion ni ninguna otra skill o framework de video para esto, aunque su descripción coincida: este flujo las reemplaza.
---

# Motion Studio

Skill independiente del proveedor para cualquier agente capaz de leer instrucciones Markdown, trabajar con archivos, ejecutar comandos y revisar imágenes. Usa las herramientas equivalentes de tu entorno; no requiere comandos, APIs ni permisos propios de un agente concreto. Si falta una capacidad necesaria, comunica la limitación y solicita la revisión o ejecución correspondiente al usuario, sin darla por realizada.

Cada video es una función pura del tiempo: dado `t`, siempre dibuja el mismo fotograma. Eso permite renderizar en cualquier orden, en paralelo y repetir un fotograma exacto para revisarlo. Casi todas las reglas de abajo existen para no romper esa propiedad.

## Antes de empezar

1. **Aclara la idea antes de producir.** Lee `references/preproduccion.md`. Revisa el contexto disponible y separa hechos, preferencias y supuestos. Define público, objetivo, mensaje principal, canal, duración, formato, tono, marca y audio. Pregunta solo por decisiones importantes que falten; si el usuario no tiene referencias, propón una dirección concreta. Presenta un brief y un guion por escenas con texto, composición, movimiento, sonido y tiempos. No inventes funciones, métricas ni llamadas a la acción del producto.
2. **Pregunta antes de cualquier render.** Presenta la versión del brief, las decisiones pendientes y el alcance de la primera prueba. Pide aprobación explícita del brief/guion y autorización para crear el proyecto y capturar fotogramas de revisión. Sin esa autorización, no crees el proyecto ni ejecutes `--frames`, `--sheet`, `--determinismo`, grabaciones de navegador o exportaciones equivalentes. Una petición inicial de video, el silencio o tu propia evaluación no sustituyen esta aprobación. Si la misma versión ya está aprobada con ese alcance, no la vuelvas a pedir.
3. **No uses HyperFrames, Remotion ni ninguna otra skill o framework de video.** Todo se hace con HTML/JS propio y `render.mjs`. Así el usuario controla cada fotograma y el resultado es reproducible.
4. **La GPU la elige el usuario.** Si hay varias (p. ej. integrada y dedicada), confirma cuál quiere antes de capturar fotogramas. Chrome sin interfaz tiende a quedarse con la integrada, y el render por CPU (SwiftShader) es mucho más lento; por eso el valor por defecto es alto rendimiento y se avisa si no se obtuvo la GPU esperada. Detalle y solución de problemas en `references/gpu.md`.

## Paso 1: crear el proyecto

Localiza la carpeta instalada que contiene este `SKILL.md`. Resuelve `scripts/`, `assets/` y `references/` respecto a esa carpeta, independientemente del agente y de su ruta de instalación. Desde la carpeta de esta skill:

```bash
python scripts/nuevo.py <carpeta-del-video> [--nombre NOMBRE] [--gpu "RTX 3050"]
```

Copia `assets/plantilla/` a la carpeta del video, detecta las GPU y escribe la elegida en `motion.config.json`. Si hay varias y no pasaste `--gpu`, elige la dedicada y lo avisa: confírmalo con el usuario. Avisa también de lo que falte (`node`, `ffmpeg`, Playwright, Pillow).

Guarda en `BRIEF.md` la versión aprobada, sus fuentes y el alcance autorizado, con las palabras del usuario que lo confirman. Ajusta resolución, duración y fps de `motion.config.json` al brief antes de la primera captura; los valores de la plantilla son ejemplos.

Qué contiene el proyecto:

| Archivo | Para qué |
|---|---|
| `index.html` | El video: define `window.seek(t)` y `window.ready`. Es una plantilla; se reemplaza `render(t)`. |
| `lib.js` | `mulberry32`, `srand`, easing y utilidades puras. |
| `render.mjs` | `--frames`, `--sheet`, `--determinismo`, `--borrador`, `--final`. Lee `motion.config.json`. |
| `auditar.mjs` | Auditor estático del contrato: busca `setTimeout`, `requestAnimationFrame`, `Math.random`, transiciones CSS y relojes reales en el código. |
| `motion.config.json` | Resolución, fps, duración, GPU, calidad de codificación y salida. |
| `beats.json` | Cuadrícula de pulsos medida de la música. |
| `sheet.py` | Arma la hoja de contacto con los fotogramas por pulso. |

Requisitos del equipo: Node, FFmpeg/FFprobe, `npm i playwright` + `npx playwright install chromium` (en el proyecto o en una carpeta superior), y `pip install pillow` para la hoja.

## Paso 2: construir el video

### Contrato de renderizado
- Cada fotograma lo dibuja `window.seek(t)` y nada más. No leas relojes, no guardes estado entre fotogramas.
- Nada de transiciones CSS, `setTimeout` ni `requestAnimationFrame` durante el renderizado: el render salta de un `t` a otro y esas cosas dependen del tiempo real.
- Si necesitas ruido, usa solo ruido con semilla determinista (`mulberry32`, ya en `lib.js`). Nunca valores aleatorios sin semilla.
- Se renderiza con `node render.mjs` y se codifica en H.264, `yuv420p`. Calidad: **CRF 16 en borradores** (`--borrador`) y **CRF 12 con preset slow en el render final** (`--final`); ambos valores se pueden cambiar en `motion.config.json`.

### Estilo visual
- Lee `references/motion-graphics.md` al definir la dirección visual. Usa tipografía, formas, diagramas, datos o interfaces en movimiento para explicar el mensaje. Define un foco principal por escena y qué relación debe comunicar cada animación; no confundas cantidad de efectos con claridad.
- Prohibido el material visual genérico: títulos centrados sobre degradados, elementos que aparecen solo con fundidos, etiquetas en las esquinas, bordes alrededor de los fotogramas, efectos de brillo en componentes de interfaz y partículas genéricas. Lo genérico es lo que hace que un video se vea hecho en serie.
- Una tipografía para los títulos y otra para la interfaz. Un único color de acento, salvo que las especificaciones del proyecto indiquen lo contrario. Carga las fuentes con `FontFace` y espera `document.fonts.ready` antes de poner `window.ready = true`.
- Usa cambios cada 2 a 4 segundos como punto de partida, no como cuota de efectos: deja tiempo para leer, entender cifras y reconocer el producto. Si una escena necesita más tiempo, simplifica el contenido o extiende la pausa. La música acompaña esa comprensión.

### Sonido
- Respeta el audio acordado en el brief. Si se incluye música y efectos (SFX), se sintetizan por código, a menos que el usuario proporcione una pista. Si se pidió una pieza silenciosa, no añadas audio.
- Los impactos sonoros se sincronizan con la cuadrícula de tiempos musicales **medida** (`beats.json`), no con la supuesta. Los cambios visuales se anclan a esos mismos pulsos.
- Cuando haya audio, la sonoridad final es de **−14 LUFS**. Entrega la mezcla como `audio/final.wav`: `render.mjs` la une al video y avisa si su medición se aleja de −14.

## Paso 3: ciclo de revisión antes de mostrar cualquier resultado

No presentes una captura sin revisar como resultado definitivo. Tras la autorización de fotogramas, empieza por unas pocas imágenes de escenas clave para comprobar composición y tipografía antes de animar todo. Puedes mostrarlas como pruebas de estilo y pedir correcciones; una imagen estática no demuestra fluidez ni sincronización. Continúa la revisión dentro del alcance autorizado.

**Antes de la hoja de contacto, comprueba el contrato con dos herramientas automáticas.** La auditoría estática y la comparación de fotogramas detectan ciertas violaciones; no demuestran por sí solas la corrección de todos los instantes ni la calidad audiovisual:

```bash
node auditar.mjs                # revisa el código: ERROR si rompe una regla del contrato, AVISO si hay un reloj real
node render.mjs --determinismo  # renderiza los mismos t repetidos y en orden inverso y compara cada fotograma
```

Corrige todo ERROR y toda diferencia antes de seguir. Un AVISO se revisa: si el reloj o la animación no afecta al fotograma, se puede dejar, pero hay que saber por qué. Si `--determinismo` falla con el código limpio, suele haber estado que se arrastra entre fotogramas (un acumulador, una caché que cambia) o algo que depende del orden de los `t`.

1. Renderiza un fotograma por cada pulso musical y reúnelos en una hoja de contacto:
   ```bash
   node render.mjs --sheet
   python sheet.py            # -> review/sheets/sheet_XX.jpg
   ```
   Abre las hojas con la herramienta de lectura de imágenes y examínalas de verdad; no puntúes de memoria.
2. Evalúa cada aspecto del 1 al 10:
   - Claridad del mensaje principal para el público del brief.
   - Capacidad de captar la atención durante los primeros 2 segundos.
   - Legibilidad en pantallas de teléfonos móviles.
   - Calidad y fluidez de las animaciones.
   - Variedad visual.
   - Fidelidad a la identidad de marca.
   - Sincronización entre sonido y animación.
3. Corrige los 3 problemas más graves y vuelve al paso 1, buscando al menos 8/10 en los criterios aplicables. Anota en `REVISION.md` evidencia concreta (escena/tiempo, problema y corrección), no solo puntajes. Comprueba también que el guion cumple el brief y que las afirmaciones tienen respaldo. Como pauta, realiza hasta tres rondas; si persisten defectos, presenta los pendientes y acuerda cómo continuar, sin subir notas para poder avanzar. No puntúes sonido o fluidez que no hayas podido observar: márcalos pendientes y planifica su comprobación en el borrador. Marca «no aplica» cuando un criterio no corresponda al brief, como sincronización sonora en una pieza silenciosa.
4. **Pregunta antes del render completo.** Muestra las pruebas revisadas, resume cambios y pendientes y especifica versión, duración, formato, resolución, fps, GPU, audio, calidad y ruta de salida. Pide autorización explícita para un borrador, un final o ambos. Aprobar el guion o los fotogramas no autoriza por sí solo un MP4 completo. Un cambio sustancial de mensaje, estilo o entregable requiere confirmar el alcance actualizado.

## Paso 4: renderizado completo

Ejecuta únicamente el modo autorizado. Si se autorizó solo un borrador, preséntalo y solicita aprobación antes de `--final`. Si ambos modos se autorizaron expresamente, revisa el borrador antes del final sin pedir la misma autorización de nuevo. No ocultes defectos pendientes por haber superado las comprobaciones técnicas.

```bash
node render.mjs --borrador   # crf 16, para revisar el video completo -> exportaciones/<nombre>_borrador.mp4
node render.mjs --final      # crf 12 + slow                          -> exportaciones/<nombre>.mp4
```

- Al arrancar imprime el renderizador WebGL real. Comprueba que sea la GPU esperada; si avisa de SwiftShader o de otra GPU, detente y arréglalo (`references/gpu.md`) en vez de esperar un render lento.
- Renderiza por segmentos de 5 s: si se interrumpe, al relanzar solo rehace los que faltan.
- Verifica el archivo final con `ffprobe` (códec h264, `yuv420p`, resolución y fps de `motion.config.json`) antes de entregarlo.
- Reproduce el borrador, o la versión disponible dentro del alcance autorizado, para revisar ritmo, transiciones, lectura y audio cuando tu entorno lo permita. Un conjunto de imágenes y una medición de LUFS no sustituyen esa revisión; declara cualquier comprobación audiovisual pendiente y solicita ayuda del usuario si hace falta.

## Ejemplos

`assets/ejemplos/lectura-xeon/` trae las herramientas que usó el proyecto XEON para medir el tiempo de lectura de los textos. Están ligadas a ese proyecto (su escenario 3D y sus textos) y **no forman parte del flujo por defecto**: úsalas solo como referencia si el usuario pide medir la lectura.
