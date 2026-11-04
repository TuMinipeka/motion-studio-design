# Revisión audiovisual de 3.mp4

2026-11-03. Se revisa un corto narrativo 2D/2.5D, «Tu mamá se levanta a las 4:50». No se evalúa como una pieza de motion graphics de ritmo publicitario.

## Evidencia y alcance

- Archivo: 150 s, 9000 fotogramas, 1920 × 1080 a 60 fps, H.264 yuv420p, BT.709, AAC estéreo de 48 kHz.
- SHA-256: `f6217ae0211db0c4b1e4aeffa336611f0dfb47cce72c36b14f497af9560f0cba`. Coincide exactamente con la exportación del proyecto localizado; no es una asociación inferida solo por el nombre.
- Se observaron 30 imágenes distribuidas cada 5 s, secuencias muestreadas cada 0,25 s en 62–68 y 103–109 s y fotogramas de la prueba. Se leyeron storyboard, brief, revisión, eventos y código de personajes y planos.
- Se decodificó el original completo: 9000 fotogramas, sin errores de decodificación reportados. Medición completa EBU R128: −14,0 LUFS, LRA 11,0 LU, pico real −1,3 dBFS.
- No hubo escucha subjetiva ni reproducción continua perceptiva. Las notas visuales son provisionales y no puntúan fluidez a velocidad normal. La voz, interpretación musical y sincronía percibida quedan pendientes. Las correlaciones de audio solo acreditan conservación/alineación de la señal.
- El storyboard localizado es una tabla v1; no documenta todavía las fichas por plano recién incorporadas al repositorio. El brief registra una ruta instalada, pero no la huella exacta de la skill al producir el video. No se atribuyen todos sus defectos a la última versión de la skill.

## Evaluación del original

| Aspecto | Nota /10 | Evidencia y oportunidad |
| --- | --- | --- |
| Actuación y poses | 6 provisional | Hay duda, cansancio y sonrisas, pero muchas acciones se resuelven con articulaciones frontales y poses mantenidas. El asiento y la caminata necesitan comprobar peso y apoyo en reproducción. |
| Transiciones | 7 provisional | Los detalles de cocina, puerta y rimas del reloj y el paradero enlazan el relato. Algunas tarjetas interrumpen la continuidad. No se verificó todo el montaje en reproducción. |
| Composición y cámara | 6 provisional | Buen uso del vacío en el paradero. En P19 el general prolonga la distancia cuando el gesto importante ya es la cara cansada; otros planos oscuros requieren revisar el foco a tamaño pequeño. |
| Iluminación | 7 provisional | Cálido = cuidado; azul = móvil. El cambio al cálido sobre Nico sostiene el giro. La lectura de manos y siluetas se debilita en algunos planos oscuros; conviene luz localizada, no levantar toda la exposición. |
| Narrativa y ritmo | 7 provisional | Contraste de rutinas, progresión y respuesta final claros en el storyboard. Conviene ajustar el remate y distinguir pausas emocionales de tiempos de cierre sin información nueva. No se midió retención de espectadores. |
| Efectos visuales | 7 provisional | Vapor, polvo y luz ayudan a la atmósfera. Los destellos en la cabeza compiten con los ojos en torno a 45–50 s. El halo no debe ocultar el estado del personaje. |
| Sonido técnico | 8 | Nivel y pico adecuados en la medición. No se califica interpretación, inteligibilidad ni mezcla artística sin escucha. |
| Render técnico | 9 | Formato, color, número de fotogramas y decodificación completa correctos. No equivale a ausencia de todo artefacto visual ni a 9/10 artístico. |
| Fluidez, música/voz y sincronía percibida | Pendiente | Requieren reproducción y escucha. |

## Diagnóstico de la skill y cambios

1. **Foco antes que movimiento.** Las rúbricas aún imponían cambiar escala cada 2–4 s, un tamaño universal del sujeto, rebote en llegadas y densidad/estéreo intensos. Esas reglas chocaban con la guía que permite pausas y podían llevar a rellenar un corto lento con cámara. Se sustituyen por intención, legibilidad y evidencia. También se retiran límites universales de duración de rótulos y diagramas en preproducción; siguen las mediciones de ritmo como diagnóstico.
2. **Encuadre reproducible de un detalle.** `encuadreZona(zona, W, H, margen)` se añade a `kit/camara.js`. Ajusta una región de acción por ambos ejes, con margen configurable y entradas validadas. No detecta rostros, oclusiones ni decide cuándo cortar. La garantía solo vale para la zona declarada y la cámara sin rotación; no para posteriores giros, sacudidas o interpolaciones.
3. **Capas a la densidad necesaria.** La guía pide dimensionar las capas rasterizadas para el aumento máximo de la toma. En la copia de prueba se dibuja el personaje a densidad 2,1 solo después del corte. Ese ajuste se hizo en el rig propio del proyecto; no se añade ese rig al kit ni se obliga a aumentar globalmente resolución o fps.
4. **Muestra en dos etapas.** `--prueba` codifica imagen y después une la mezcla copiando el video. Se conserva el intervalo alineado al primer fotograma y el perfil final. Hubo una espera prolongada en el intento anterior y se interrumpió; no se diagnosticó su causa con certeza. La nueva ruta terminó, pero eso no demuestra que toda espera fuese un interbloqueo ni una mejora medida de velocidad.
5. **Prueba difícil desde el storyboard.** Se precisa que una emoción en penumbra debe leerse a tamaño de entrega, y que una muestra luminosa o de títulos no valida ese caso. Se reutilizan fichas y revisiones actuales, sin nuevas aprobaciones rutinarias.

## Comparación antes/después

Mismo intervalo **64,5–68,5 s**, 4 s, 1080p60, 240 fotogramas, CRF 12 slow, RTX 3050. Se preservan actuación, duración y mezcla. El original se conserva.

- **Antes:** un acercamiento progresivo dentro del plano general.
- **Después:** conserva el general durante 0,5 s y corta a la reacción al dejar el bolso. Usa la zona del rostro y torso; aumenta moderadamente el relleno del personaje y la densidad de sus capas para evitar ampliar una textura pequeña.
- La altura geométrica del rostro al final pasa de unos 349 a 507 px: **+45,2 %**. Es una proyección del rig y las cámaras, no una detección automática del rostro ni una medida de retención.
- Legibilidad de la reacción: **6 → 8/10 provisional** en las imágenes revisadas. No se atribuye mejora a la actuación, al guion o a la fluidez, que no fueron cambiados ni verificados perceptivamente.
- Audio antes/después: correlación interior **0,99995** tras decodificar a mono 48 kHz. No demuestra calidad de mezcla artística.
- La toma corregida tiene mayor coste por sus capas: aproximadamente **195 s** en esta ejecución, con otros procesos presentes. No hay un benchmark controlado antes/después. No se demuestra mejora de rendimiento ni se cumple una garantía global de 9/10 sin coste adicional. La guía reserva densidad extra a los planos que lo necesitan.

Archivos de revisión externos a Git: `C:/Users/danie/Documents/skill-review-3/`: `antes.mp4`, `despues.mp4`, `comparacion.mp4`, `comparacion.jpg`, `medidas.txt` y `feedback-video.md`. El proyecto aislado contiene la aplicación de las mejoras; actualizar la skill no reanima automáticamente un video existente.

## Validación

- `node tests/animacion/encuadre-zona.test.mjs`: 27 encuadres horizontales, verticales y cuadrados, con tres márgenes y zonas anchas/altas; sus esquinas permanecen dentro del cuadro y se aprovecha al menos un eje. Siete entradas inválidas rechazadas.
- Determinismo exacto de la muestra en 64,5; 64,983333; 65; 66 y 67,8 s, repetidos y en orden inverso.
- FFprobe y decodificación completa del después: H.264 yuv420p, 1920×1080 a 60 fps, 240 fotogramas, video y AAC de 4 s desde cero. Se inspeccionó el fotograma codificado a 67,8 s.
- Cuatro casos de regresión del modo muestra: mezcla, mezcla corta con cola de silencio, modo mudo explícito y ausencia de mezcla. El intervalo fraccional 0,21–0,71 a 12 fps produce seis fotogramas desde 0,25 s; correlación con audio de origen en ese inicio: 0,99675.
- Sintaxis JavaScript, auditoría de plantilla (cinco archivos, cero errores/avisos), validador de la skill, enlaces locales y `git diff --check`.
- No se volvió a exportar el corto completo ni se usaron servicios de pago. Quedan pendientes la escucha, la revisión continua del movimiento y las pruebas de otros sistemas/GPU.

## Criterio consultado

[Figma — Principles in motion](https://www.figma.com/blog/principles-in-motion/), consultado el 2026-11-03: intención, pausas, asentamiento y relación entre imagen y sonido. Se usa como apoyo de dirección; la evidencia del diagnóstico procede del video y del código, no de una promesa de calidad de esa fuente.
