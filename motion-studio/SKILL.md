---
name: motion-studio
description: >-
  Flujo de Motion Studio para crear y renderizar un video nuevo (motion graphics, explicativo, promocional, short o video de YouTube) como una función pura del tiempo, `window.seek(t)`, renderizada con `node render.mjs` en Chrome sin interfaz, la GPU elegida por el usuario y FFmpeg (H.264 yuv420p). Úsala SIEMPRE que el usuario pida crear, empezar, montar, animar o renderizar un video nuevo, aunque no diga "Motion Studio"; también para dibujar un video con HTML/canvas/three.js, hoja de contacto, render por GPU o revisión de un video antes de exportarlo. NO uses HyperFrames, Remotion ni ninguna otra skill o framework de video para esto, aunque su descripción coincida: este flujo las reemplaza.
---

# Motion Studio

Cada video es una función pura del tiempo: dado `t`, siempre dibuja el mismo fotograma. Eso permite renderizar en cualquier orden, en paralelo y repetir un fotograma exacto para revisarlo. Casi todas las reglas de abajo existen para no romper esa propiedad.

## Antes de empezar

1. **El guion se estructura y se aprueba antes de cualquier render.** Escribe el guion por escenas (qué se dice, qué se ve, cuánto dura) y espera la aprobación del usuario. Si no hay guion aprobado, no crees el proyecto ni renderices nada.
2. **No uses HyperFrames, Remotion ni ninguna otra skill o framework de video.** Todo se hace con HTML/JS propio y `render.mjs`. Así el usuario controla cada fotograma y el resultado es reproducible.
3. **La GPU la elige el usuario.** Si hay varias (p. ej. integrada y dedicada), confirma cuál quiere. Chrome sin interfaz tiende a quedarse con la integrada, y el render por CPU (SwiftShader) es mucho más lento; por eso el valor por defecto es alto rendimiento y se avisa si no se obtuvo la GPU esperada. Detalle y solución de problemas en `references/gpu.md`.

## Paso 1: crear el proyecto

Desde la carpeta de esta skill:

```bash
python scripts/nuevo.py <carpeta-del-video> [--nombre NOMBRE] [--gpu "RTX 3050"]
```

Copia `assets/plantilla/` a la carpeta del video, detecta las GPU y escribe la elegida en `motion.config.json`. Si hay varias y no pasaste `--gpu`, elige la dedicada y lo avisa: confírmalo con el usuario. Avisa también de lo que falte (`node`, `ffmpeg`, Playwright, Pillow).

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
- Prohibido el material visual genérico: títulos centrados sobre degradados, elementos que aparecen solo con fundidos, etiquetas en las esquinas, bordes alrededor de los fotogramas, efectos de brillo en componentes de interfaz y partículas genéricas. Lo genérico es lo que hace que un video se vea hecho en serie.
- Una tipografía para los títulos y otra para la interfaz. Un único color de acento, salvo que las especificaciones del proyecto indiquen lo contrario. Carga las fuentes con `FontFace` y espera `document.fonts.ready` antes de poner `window.ready = true`.
- Cada 2 a 4 segundos debe ocurrir algo nuevo en pantalla.

### Sonido
- La música de fondo y los efectos (SFX) se sintetizan por código, a menos que el usuario proporcione una pista de audio.
- Los impactos sonoros se sincronizan con la cuadrícula de tiempos musicales **medida** (`beats.json`), no con la supuesta. Los cambios visuales se anclan a esos mismos pulsos.
- La sonoridad final es de **−14 LUFS**. Entrega la mezcla como `audio/final.wav`: `render.mjs` la une al video y avisa si su medición se aleja de −14.

## Paso 3: ciclo de revisión antes de mostrar cualquier resultado

No muestres nada al usuario hasta terminar este ciclo.

**Antes de la hoja de contacto, comprueba el contrato con dos herramientas automáticas.** Una hoja de contacto bonita no demuestra que el video sea una función pura de `t`; estas dos sí:

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
   - Capacidad de captar la atención durante los primeros 2 segundos.
   - Legibilidad en pantallas de teléfonos móviles.
   - Calidad y fluidez de las animaciones.
   - Variedad visual.
   - Fidelidad a la identidad de marca.
   - Sincronización entre sonido y animación.
3. Corrige los 3 problemas más graves y vuelve al paso 1. Repite hasta que **todos** los criterios tengan al menos 8/10. Anota cada ronda (puntajes y qué corregiste) en `REVISION.md` del proyecto.
4. Solo entonces haz el renderizado completo.

## Paso 4: renderizado completo

```bash
node render.mjs --borrador   # crf 16, para revisar el video completo -> exportaciones/<nombre>_borrador.mp4
node render.mjs --final      # crf 12 + slow                          -> exportaciones/<nombre>.mp4
```

- Al arrancar imprime el renderizador WebGL real. Comprueba que sea la GPU esperada; si avisa de SwiftShader o de otra GPU, detente y arréglalo (`references/gpu.md`) en vez de esperar un render lento.
- Renderiza por segmentos de 5 s: si se interrumpe, al relanzar solo rehace los que faltan.
- Verifica el archivo final con `ffprobe` (códec h264, `yuv420p`, resolución y fps de `motion.config.json`) antes de entregarlo.

## Ejemplos

`assets/ejemplos/lectura-xeon/` trae las herramientas que usó el proyecto XEON para medir el tiempo de lectura de los textos. Están ligadas a ese proyecto (su escenario 3D y sus textos) y **no forman parte del flujo por defecto**: úsalas solo como referencia si el usuario pide medir la lectura.
