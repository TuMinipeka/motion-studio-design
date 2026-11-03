# Revisión de un episodio real y correcciones de la skill

Fecha: 2026-11-03. Material: `ojala-no-ep01_v2.mp4`, 481,1 s, 1920 × 1080 a 60 fps, H.264 yuv420p, AAC estéreo de 48 kHz. Es un corto narrativo 2D; no se evalúa como un anuncio de tipografía cinética.

## Alcance y evidencia

Se inspeccionaron tres hojas de muestreo del episodio, dos secuencias de 6 s con muestras cada 0,25 s (alrededor de 3:43 y 4:05), el fotograma inicial, planos.json, montaje.json, código de escenas, BRIEF y REVISION del proyecto. Las hojas globales orientan la selección: el filtro fps selecciona imágenes por intervalos y sus etiquetas no certifican el tiempo exacto del fotograma. Los tiempos precisos siguientes vienen de extracciones con seek explícito y del storyboard.

No hubo reproducción audiovisual continua ni escucha subjetiva mediante una herramienta perceptiva. Por eso las notas visuales son provisionales; fluidez a velocidad normal, interpretación de las voces, inteligibilidad y sincronía percibida quedan pendientes de revisión humana. No se inventan cifras de retención, ni una nota global 9/10.

## Evaluación del original

| Aspecto | Nota /10 | Evidencia y límite |
| --- | --- | --- |
| Actuación y poses | 6 provisional | Hay caras y gestos reconocibles, pero se repite la vista frontal y las poses mantenidas. En plano 73 se programaba giro de cabeza sinusoidal; no equivale a intención. No puntúa fluidez. |
| Transiciones | 7 provisional | Puerta que oculta cambio de lugar, cortes a detalle, cambio de foco y contraplano aportan variedad. No se comprobó todo el montaje reproducido. |
| Composición y cámara | 6 provisional | Buen contraste figura/fondo en varios escenarios; el texto de la libreta se recorta al acercarse en 3:44,5–3:47,38. La función cobertura usa aumento lineal de 11 % por segundo más deriva de 22 px/s. |
| Iluminación | 7 provisional | Diferencia cálida/fría y capas de profundidad legibles. Bordes luminosos y viñetas recurrentes pueden uniformar el acabado. No falta luz en todos los planos. |
| Narrativa y ritmo | 6 provisional | Hay conflicto, progresión, revelaciones y cierre; las notas de producción reconocen largos intervalos sin voz. Su eficacia depende de que la acción sostenga esos tiempos. La duración por sí sola no demuestra pérdida de retención. |
| Efectos visuales | 7 provisional | Ondas, reflejos y lluvia relacionados con el poder. Evitar que el efecto se convierta en sustituto de actuación. |
| Render técnico | 8 | Resolución y fps verificados; muestreo sin roturas visibles. No se verificó decodificación íntegra de los ocho minutos. 60 fps/CRF 12 no certifican arte. |
| Sonido técnico | 8 | EBU R128 sobre todo el archivo: −14,1 LUFS, LRA 7,7 LU, pico real −1,1 dBFS. No determina calidad de voces o mezcla perceptiva. |
| Fluidez, sonido artístico y sincronización percibida | Pendiente | Requieren reproducción/escucha, no una nota inferida de LUFS, código o imágenes. |

## Causas y cambios aplicados

1. **Cámara que intenta aprobar una métrica.** REVISION registra aumentos de cobertura y empuje digital para superar ritmo. La guía ordenaba cambiar de escala cada 2–4 s y limitaba la nota a 6 si fallaba la métrica. Se reemplaza esa equivalencia por diagnóstico del tramo: acción, consecuencia, duración y lectura. La cámara tiene principio, destino y máximo; se verifican extremos y cruces de plano. No se rebajan los umbrales para hacer pasar este video.
2. **Reglas de animación demasiado universales.** El kit decía que toda acción debía rebotar y toda pose mantenerse viva. Ahora anticipación, sobrepaso y movimiento secundario dependen del peso y la intención; una mirada o contacto sostenido no necesitan rebote. Las pausas expresivas y cámara fija son válidas.
3. **Muestra muda aunque haya mezcla.** `render.mjs --prueba` ahora incorpora `audio/final.wav` si existe: `atrim` desde el primer fotograma capturado y `asetpts` desde cero. Conserva el volumen, codifica AAC 320k, limita duración y rellena cola corta con silencio para conservar el intervalo visual. No sintetiza ni aprueba audio. `--sin-audio` conserva una prueba explícitamente muda; sin mezcla, avisa que la sincronización queda pendiente.
4. **Muestra poco representativa.** Se aclara que una transición vistosa no valida actuación y diálogo. Se revisa también desarrollo al revisar el acto, reutilizando las revisiones existentes, sin otra aprobación rutinaria. El ejemplo del kit pasa a ser consulta opcional; no obliga a renderizarlo antes de cada encargo.

El brief registra una skill instalada en `.claude/skills`, además de un rig antiguo copiado del piloto y retirado del kit actual. Esto explica una ruta de herencia de decisiones; no prueba que el rig sea la única causa. El brief también registra un contrato posterior hacia stickman: no se impone ese rediseño durante esta prueba ni se mezcla el estilo de otros canales.

## Comparación controlada

Copia aislada del proyecto; no se cambia el original. Intervalo **219,9–227,4 s**, plano 70, duración 7,5 s. Se conservan personajes, textos, instantes de escritura, duración, voz y música. El antes es un recorte del MP4 v2. El después se renderiza desde la copia con zoom acotado de 1,08 a 1,18, centrado y sin deriva de cámara en ese detalle. Esta es una aplicación manual de la guía; actualizar la skill no recompone automáticamente proyectos existentes.

| Criterio del fragmento | Antes | Después |
| --- | --- | --- |
| Composición/lectura, valoración provisional | 5/10: acercamiento hasta ~2,09 y primera frase cortada al final | 8/10: las tres frases quedan completas en los instantes revisados |
| Calidad de exportación | 1080p60 | 1080p60, CRF 12 slow, H.264 yuv420p, 450 fotogramas |
| Duración | 7,5 s | 7,5 s en video y audio; ambas pistas empiezan en cero |
| Audio de la prueba nativa | El renderizador anterior lo omitía | Mezcla del mismo intervalo, sin normalización extra |
| Actuación, transiciones y narrativa global | Sin cambio en este ensayo | No se atribuye mejora: el plano elegido prueba lectura y cámara |

No se declara conseguido 9/10. El ensayo demuestra corrección de encuadre y capacidad de revisar audio antes del completo; no acredita fluidez, retención o actuación profesional en todo el episodio.

## Validación realizada

- Sintaxis de render.mjs; auditoría de plantilla: cinco archivos, cero errores/avisos; validador estructural: Skill is valid; git diff --check.
- En el proyecto de prueba: determinismo exacto en 219,9; 223,6; 224,5 y 227,38 s, repetidos y orden inverso, RTX 3050.
- FFprobe y decodificación completa del después: 450 fotogramas, 7,5 s, 1080p60 H.264 yuv420p y AAC de 7,5 s. Se inspeccionaron imágenes del archivo de trabajo; queda pendiente reproducir la comparación con escucha.
- Fixture de audio independiente: intervalo solicitado 0,21–0,71 s a 12 fps produce seis fotogramas desde 0,25 s. Correlación de audio decodificado con la fuente en ese inicio: 0,99675 (comparación interior, excluyendo bordes AAC). Casos con mezcla, --sin-audio y sin archivo de mezcla completan correctamente; los dos últimos no tienen pista sonora.
- No se reexportó el episodio completo, no se consumieron APIs de voz ni se instalaron herramientas globales. Archivos de revisión fuera de Git: `C:/Users/danie/Documents/skill-review-ojala/` (antes.mp4, despues.mp4, comparacion.mp4 y comparacion.jpg).

## Fuentes de criterio y técnica

- [Figma: Principles in motion](https://www.figma.com/blog/principles-in-motion/), consultado el 2026-11-03: intención, pausas, asentamiento y coordinación de sonido e imagen. Es criterio profesional, no evidencia de que este episodio alcance una nota.
- [FFmpeg: atrim y asetpts](https://ffmpeg.org/ffmpeg-filters.html#atrim), consultado el 2026-11-03: recortar audio no reinicia sus timestamps; se hace explícitamente después. Implementación comprobada con la instalación local de FFmpeg.
