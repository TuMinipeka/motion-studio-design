# Revisión de video.mp4: comedia de personajes 2.5D por capas

5 de noviembre de 2026. El archivo es una prueba del episodio 1 de DANZO, con modelos 3D, contornos y caras de acabado gráfico. Se evalúa como comedia de personajes; se conserva su identidad, sin aplicar el estilo del corto dramático ni el de divulgación low-poly.

## Evidencia y alcance

- Archivo recibido: `C:/Users/danie/Downloads/video.mp4`. SHA-256 `3e7b11fa9f853436132f49f75342be16fb3afb4322c457ea8f1de1a7556733f5`, idéntico a `productividad/canal-3d/episodios/ep01/animacion/prueba_animada_v2.mp4`.
- 25,833 s, 620 fotogramas, 1280×720 a 24 fps, H.264 High/yuv420p y AAC estéreo de 48 kHz. El audio dura unos 20 ms menos: no demuestra un desfase perceptible. No hay etiquetas de color BT.709.
- El código genera personajes y cámara 3D a 12 dibujos/s; el montaje entrega 24 fps, con repetición de dibujos y algunos gráficos actualizados a 24. No son 24 poses distintas por segundo.
- Se revisaron imágenes cada segundo, fotogramas del gag y de la comparación; se leyeron notas, guion, datos de planos, rig, cámara, boca y montaje. Se decodificaron los 620 fotogramas sin errores reportados.
- Medición completa: **−12,7 LUFS, LRA 6,1 LU y pico real −2,5 dBFS**. El nivel está 1,3 LU por encima del objetivo −14; no hay evidencia de saturación por ese pico. No hubo escucha subjetiva ni reproducción continua perceptiva: fluidez, actuación vocal y sincronía percibida quedan pendientes.
- La prueba une un fragmento de carrera con otro de la sopa; no es el episodio completo. Sus 17 planos equivalen a unos 37 cortes/min, sin que esa cifra pruebe retención o buena puesta en escena.

## Calificaciones del original

Notas editoriales provisionales sobre lo observado, sin una nota global de aprobación.

| Aspecto | /10 | Evidencia y oportunidad |
| --- | --- | --- |
| Animación y actuación | 6 provisional | Hay visemas, miradas, gestos, reacciones y carrera; supera el animatic fijo. Parte del gesto sigue amplitud de voz y oscilaciones genéricas. La carrera necesita revisar apoyo y desplazamiento a velocidad normal; no se midió deslizamiento de pies. |
| Transiciones y variedad de planos | 7 provisional | Hay seguimiento, detalle, plano/contraplano y reacción. Algunos acercamientos persiguen intensidad y dificultan reconocer el gesto. Conviene conservar orientación y tiempo de lectura antes de añadir cortes. |
| Composición y cámara | 5 provisional | En C08 el acercamiento coincide con el crecimiento del pelo, recorta boca/manos y pierde una referencia estable de tamaño. Otros primeros planos también se cierran mucho. |
| Iluminación, color y profundidad | 7 provisional | Paleta violeta/amarillo, contornos y perspectiva coherentes. La planitud es parte del acabado, no un defecto por sí misma. Cuando sea necesario para leer apoyo, una sombra de contacto localizada puede ayudar sin imponer realismo. |
| Narrativa y ritmo planificado | 7 provisional | Mentira → crecimiento → reacción → lámpara sostiene el gag en el guion. El montaje debe dejar ver esa consecuencia. No se penaliza como relato incompleto lo que se entregó como prueba de dos fragmentos. No hay datos de retención. |
| Efectos y grafismo | 6 provisional | El afro, la lámpara y el contador tienen función. El rótulo central compite con el pelo; en el segundo gag pueden coincidir el rótulo central y el del contador. No necesitan más partículas. |
| Sonido técnico | 7 | Sonoridad ligeramente fuera del margen −14 ±1; pico con margen. La ausencia de música está declarada en la prueba y no es un fallo por sí misma. Interpretación, efectos y mezcla artística pendientes de escucha. |
| Render técnico | 8 | Resolución y fps propios de esta muestra, con decodificación correcta. Faltan etiquetas de color y no se ejecuta la ruta de exportación de la skill. Subir resolución no corrige actuación o cámara. |
| Fluidez y sincronización percibida | Pendiente | Las imágenes, el guion y los datos de boca no sustituyen reproducción y escucha. |

## Diagnóstico y mejoras de la skill

1. **Lectura del gag desde la ficha.** `estilos.md` y dirección de movimiento precisan qué debe verse durante el cambio, comprobando poses extremas, cámara, recorte y grafismo juntos. Una referencia estable puede distinguir crecimiento de acercamiento. No se impone cámara quieta a todos los gags.
2. **Cadencia explícita por recurso.** Se diferencia cadencia de dibujos de fps de entrega. Si una cámara rápida a 12 salta, se replantea o se muestrea solo ese plano con más frecuencia cuando lo requiera. No se fuerza 60 fps ni el doble de render global.
3. **Generador y reproductor son pruebas distintas.** El generador original arrastra `prev_habla`/`boca_suave` y consume ruido por llamada; reiniciar una semilla no lo vuelve independiente del orden. La guía pide datos temporales, transformaciones restablecidas y comprobación independiente del generador. En la copia se usa la amplitud ya precalculada, fase fija de respiración y reinicio completo de la pose.
4. **Salida SDR coherente.** `render.mjs` fija conversión RGB→YUV con matriz BT.709 y rango limitado, propiedades de color de los fotogramas y etiquetas del codificador, tanto en muestras como en completos. No basta añadir etiquetas a una conversión de otra matriz. No se añade gestión HDR/ICC.
5. **Caché de color separada.** Los segmentos nuevos usan `review/segments-<modo>-bt709-tv`. No se borran los anteriores ni se reutilizan como si hubieran pasado por la conversión nueva.

El proyecto de origen usa Blender/Python y FFmpeg directo, aunque su plan proponía composición y controles de Motion Studio. Por eso no se atribuyen sus defectos a una huella concreta de la skill ni se presenta ese montaje como una ejecución de `render.mjs`. La skill conserva su motor; la prueba compone los recursos autorizados mediante HTML/`seek(t)`.

## Prueba antes/después

Intervalo del archivo recibido: **14,541667–17,291667 s**, planos C07–C09, **2,75 s / 66 fotogramas / 720p24**. Se preserva el audio del intervalo y la cadencia de dibujos. El original y su proyecto no se modifican.

- **Antes:** C07 establece el diálogo; C08 avanza con fuerza mientras crece el afro; C09 corta a la lámpara.
- **Después:** solo se regenera C08 con una cámara estable más abierta, cara/manos/pelo visibles y el rótulo desplazado hacia la derecha. C07 y C09 reutilizan las capas originales. Se corrigen entradas temporales y reinicio del rig en la copia, y se exporta con `render.mjs`, CRF 12/slow y color explícito.
- En la prueba aislada del generador, dibujo k=6 de C08, la caja 3D proyectada de la cabeza baja hasta **y=−0,282** con la cámara original (coordenadas desde abajo; fuera del cuadro). En el corregido, su límite inferior está en **y=0,231**; la cabeza queda dentro del margen del 5 % en sus 10 dibujos. También se revisa la imagen codificada: boca y manos permanecen visibles. Son cajas geométricas de diagnóstico, no una detección de rostro sobre el MP4, medición de comprensión o garantía de oclusiones.
- **Lectura del gag en las imágenes: 5 → 8/10 provisional.** No se acredita mejora global de actuación, fluidez o sonido, ni calidad 9/10 del episodio.
- El material de revisión está en `C:/Users/danie/Documents/skill-review-video-2026-11-05/`: `antes.mp4`, `despues.mp4`, `comparacion.mp4` (antes izquierda/después derecha), proyecto aislado, registros y `feedback-video.md`. No se incorporan los videos ni las voces a Git.

## Validación y límites

- **Color real:** `python tests/animacion/color_sdr.py` exporta una carta sintética de ocho colores por `--prueba`, `--borrador` y `--final`. Comprueba etiquetas BT.709/tv, YUV420p, cuatro fotogramas a 4 fps, negro/blanco limitados y verde con luma 709. Error RGB máximo observado: **1/255** en los tres modos. La prueba detectó primero etiquetas incompletas, resueltas fijando también las propiedades por fotograma.
- **Generador:** en dos instantes repetidos, el original da 16.991 y 223 píxeles distintos en la capa de DANZO. Tras corregir las entradas y restablecer matrices, las poses coinciden en tres instantes repetidos en orden inverso. Dos imágenes coinciden exactamente y una conserva **3 píxeles con diferencia de un nivel** en 1600×900. No se afirma determinismo exacto del rasterizador Blender ni se oculta ese residuo con una tolerancia.
- **Reproductor:** `--determinismo` pasa en 0; 1,375; 1,875 y 2,7 s, repetidos y en orden inverso. Esto acredita el reproductor, no elimina el residuo del generador.
- **MP4:** FFprobe y decodificación confirman 66 fotogramas H.264/yuv420p, 1280×720/24 fps, BT.709/tv, video y audio de 2,75 s desde cero y AAC estéreo de 48 kHz. El audio conserva 132.000 muestras al decodificar; correlación interior antes/después **0,999994**. No prueba sincronía percibida. La muestra mantiene la mezcla original; no se renormaliza un fragmento como si representara el nivel del episodio completo.
- Sintaxis, validador de la skill, auditoría de plantilla (11 archivos, cero errores/avisos), enlaces locales y regresiones de encuadre 2D, puntos 3D y técnicas del kit correctos. Los 53 scripts del proyecto original conservan sus huellas.
- Solo se regeneró el plano crítico y se reutilizaron los adyacentes. No hay benchmark controlado que demuestre igual coste o mayor velocidad; el trabajo de diagnóstico no es una medida de producción.
- Permanecen pendientes escucha, reproducción continua, carrera, continuidad del segundo gag y revisión del episodio completo. No se produce un final completo ni se garantiza retención. Los cambios pendientes de técnicas del 4 de noviembre se conservan aparte.

## Criterios consultados

- [Animation Mentor: staging](https://www.animationmentor.com/blog/staging-the-12-basic-principles-of-animation/): puesta en escena para dirigir atención y comunicar la acción; no prescribe una estética única.
- [Blender, timing](https://archive.blender.org/wiki/2015/index.php/BSoD/Introduction_to_the_Principles_of_Animation/Principles/Timing/): distingue animación en doses de muestreo individual en movimientos rápidos. Referencia conceptual histórica, no documentación de API actual.
- [FFmpeg, scale](https://ffmpeg.org/ffmpeg-filters.html#scale): matriz y rango de salida explícitos. La carta se ejecuta contra el FFmpeg instalado; no se deduce compatibilidad solo de documentación web.
