# Método make-short integrado en Motion Studio

6 de noviembre de 2026. Trabajo de investigación, reproducción en Claude y desarrollo. Las pruebas son muestras técnicas de seis segundos; no son episodios del canal ni autorizan publicación. Se conservó el árbol local previo de `main`, incluidos los cambios de técnicas, encuadre y SDR que ya estaban sin commit.

## Fuentes y alcance de observación

- [Tutorial completo de NoCodeHack](https://www.youtube.com/watch?v=gH__ujN5Joo), publicado el 4 de noviembre de 2026: archivo descargado, 648,71 s decodificados, transcripción local completa de 98 segmentos, hoja de 33 imágenes cada 20 s y capturas de momentos concretos. Esto permite reconstruir el contenido de todos los capítulos; no se afirma escucha ni visionado perceptivo continuo.
- [Repositorio make-short](https://github.com/nocodehack/make-short/tree/5a17d351343c2b5422d3ebda244c349c98ea9397), commit fijado `5a17d351343c2b5422d3ebda244c349c98ea9397`, licencia MIT. Se inspeccionaron entrada, instalación, checklist, referencias, ejemplo, generador, materiales, personajes, validación y mezcla. La copia se mantiene solo como material de investigación en `review/make-short-research/upstream`; no se instaló otra skill de producción.
- Documentación primaria de [GPU de Blender 5.2](https://docs.blender.org/api/5.2/gpu.html) y [consulta del dispositivo real](https://docs.blender.org/api/5.2/gpu.platform.html). Se contrastó además con `blender.exe --help` y la API instalada.

Las tres referencias mostradas en el tutorial se localizaron en el canal de su autor declarado, Ricks Clips. El ferrocarril está además identificado por ID en `references/beats-brief.md` del repositorio; barco y carrera se identificaron por coincidencia de planos con las imágenes del tutorial.

| Referencia | Fuente del canal | Publicación observada | Copia analizada |
| --- | --- | --- | --- |
| Why Sailors Carried Storm Oil | [Mz72MuPgnGY](https://www.youtube.com/shorts/Mz72MuPgnGY) | 30 oct 2026 | 64,594 s; 360×640 |
| Why Perfect Railroads Don't Work | [7xS87iActkU](https://www.youtube.com/shorts/7xS87iActkU) | 1 nov 2026 | 65,174 s; 608×1080 |
| How a Mirror Rigged a Horse Race | [5WMQhPObNqQ](https://www.youtube.com/shorts/5WMQhPObNqQ) | 29 oct 2026 | 64,094 s; 360×640 |

Se consiguieron los tres videos con audio y metadatos desde sus URLs del canal. No se redistribuyen ni se presume permiso de publicación de sus imágenes. Sus SHA-256 y FFprobe están en `review/make-short-research/medidas/*/referencia.json`; 65/65/64 muestras y cuatro hojas por archivo. La fuente declarada no demuestra que sea la primera publicación mundial ni concede una licencia.

Las mediciones nuevas son a **1 fps antes de reducir las capturas**. No reproducen la medición de todos los fotogramas del autor ni permiten certificar los píxeles originales de sus captions. Los 32/53/48 planos y 5/7/7 lugares del tutorial son cifras mostradas por el autor, no un conteo independiente realizado aquí.

## Cómo produce el efecto 2.5D

Claude escribe Python para Blender. El generador construye geometría, personajes, decorados, materiales, cámaras, poses y acciones. EEVEE dibuja cada instante; FFmpeg y Node realizan mezcla y captions en la ruta del tutorial.

Aunque el tutorial los llama personajes 2D, `v3/lib/chars.py` construye volúmenes con primitivas: cabezas y torsos de poca profundidad, rasgos sobre la cara, extremidades finas y un rig de objetos. El aspecto gráfico viene del sombreado por bandas, contorno de casco invertido, caras claras y formas simplificadas. Los decorados tienen perspectiva, texturas, iluminación, sombras y profundidad de campo. El efecto no procede de un generador de video por difusión ni de interpolar dos imágenes. La actuación usa poses y expresiones escalonadas, anticipación y reacción; cambiar de cámara no sustituye esos gestos.

Estructura relevante del repositorio: `v3/scene.py` integra; `lib/look.py`, `chars.py` y `sets.py` resuelven acabado/personajes/mundo; `shots.json` y `acting.json` describen el tiempo; `beats/*.json` puede sustituir rangos; `gate.py` mide stills; `voice/` obtiene tiempos, mezcla e incrusta ASS; `critic/` contiene la rúbrica. `engine/` y `template/` son una ruta 2D anterior, no necesaria para esta integración.

Dependencias de la ruta demostrada: Claude Code con acceso local, Blender 5.x, Python, Node y FFmpeg; los lanzadores asumen Windows/Git Bash. La voz puede ser una grabación o ElevenLabs; el posteo opcional usa Blotato. No se usaron aquí voz de pago, compra de créditos ni publicación.

## Reconstrucción: demostrado e inferido

| Tiempo del tutorial | Paso respaldado por imagen/transcripción/código | Qué no se puede asumir |
| --- | --- | --- |
| 00:44–02:23 | Referencias → tabla de imagen/montaje → historia de paradoja, intentos, explicación y remate; fuentes y chistes separados | Esa estructura no es obligatoria para cualquier canal ni esas métricas prueban retención |
| 02:23–03:22 | Voz antes de animación, duración medida y tiempos por palabra; se relata corrección de deriva y una toma más larga que el guion | No se reprodujo su voz clonada ni se validó su alineación original |
| 03:22–05:12 | Contrato de archivos/interfaces, trabajos de aspecto/personajes/mundo/planos | La ejecución filmada se detiene tras aproximadamente un minuto; la escena mostrada procede de otra construcción de unas 3,5 h según el autor. No es una ejecución continua desde cero |
| 05:12–07:06 | Checkpoint técnico, inspección visual, crítico independiente y correcciones verificadas por tiempo | Las notas 4,2→7,9 son juicios registrados por el autor. No garantizan el resultado de este equipo |
| 07:06–08:31 | Se muestra otro Short de 15 s sobre hardtack creado invocando la skill y se reconocen defectos | No se reconstruyeron sus recursos/voz exactos: no vienen completos en el repositorio |
| 08:31–09:44 | Archivos por gag, correcciones por rango y lecciones; se muestran tiempo/coste del autor | No son un benchmark de nuestro pipeline ni precios/límites actuales verificados |
| 09:44–10:49 | Revisión de envío y publicación privada opcional por Blotato | No se ejecutó ni se incorporó publicación automática |

El encadenamiento reproducible es referencia → guion con fuentes → voz medida → storyboard y datos ejecutables → escena/actuación → stills con medición y lectura → muestra → revisión/correcciones → exportación verificada. La organización concreta del adaptador para Motion Studio es implementación de esta tarea, no algo demostrado por el video.

## Reproducción real en Claude «2D CANAL»

Se abrió la sesión existente **2D CANAL**, se le entregó el brief técnico de seis segundos y se observó el envío y el inicio de su trabajo. Claude ejecutó la prueba aislada del ejemplo de la lata. Sus comandos, dispositivo y resultados están en `review/make-short-research/claude-test/PRUEBA-CLAUDE.md`, con logs y PNG originales.

- Blender **5.2.3 LTS**, Node **24.20.0**, Python **3.14.8**, FFmpeg **9.0.1**. GPU observada: **NVIDIA RTX 3050 Laptop 6 GB** por OpenGL, no inferida solo desde la lista de hardware.
- Tres stills nativos y **180 PNG RGBA de 1080×1920**, f0–179 a 30 fps. Dos procesos; 12 muestras TAA. Los PNG ocupan unos 483 MB y se vincularon al proyecto de composición mediante enlaces duros, sin duplicarlos.
- Tiempo registrado por Claude: **330 s** para el gate y **607 s** para los 180 dibujos. La construcción/compilación inicial consumió varios minutos por proceso. Son tiempos de esta prueba, no una previsión universal.
- Se conservó la salida original, incluidos sus problemas. El validador imprime `FAIL` y devuelve **0**; rechaza `cut` aunque el generador lo admite, fija el final a 1815 y contiene supuestos de personajes/lugares. `gate.py` dio 2/3 PASS; el still s04 falla SAT. No se trató exit 0 ni el gate como una aprobación visual.
- La hoja del fragmento muestra pasto tapando piernas, un inicio marrón del dissolve y un barrido. El still de gate de s04 muestra una lata casi recortada, pero corresponde a **f204/6,8 s**, fuera del fragmento de seis segundos. En f172–179, la lata todavía cabe y se ve pequeña. Se distingue esa evidencia para no atribuir el defecto a un instante equivocado.

El montaje de prueba añade una mezcla local de música/efectos para verificar la exportación con audio. **No es la narración ni la mezcla del tutorial**, ni se acredita sincronía de esos efectos con los gags del ejemplo original.

## Funcionalidades integradas

Se amplió la skill existente, conservando `nuevo.py`, el contrato de tiempo, kit, edición de grabaciones, render y controles. No se incorporó el motor completo del tutorial ni su identidad de personajes como plantilla obligatoria.

- `scripts/referencia.py`: procedencia declarada, SHA-256, metadatos, muestras/estadísticas y hojas temporizadas en una pasada de decodificación.
- `assets/plantilla/produccion.py`: plan opcional de planos/impactos, importación de tiempos por palabra, ASR local opcional con FFmpeg→array, validación de rangos/cobertura y generación de `sincro.json`, SRT y hojas por plano.
- `kit/sincro.js` y `audio/musica.py --sincro`: mismo reloj para actuar, dibujar captions y colocar efectos. La nueva mezcla se normaliza en dos pasadas; la primera prueba detectó un pico demasiado alto, corregido antes de entregar.
- `scripts/recursos25d.py` y runner: generador del proyecto con `seek(t)`, GPU real exigida, PNG nativos, fuente/versión/cadencia en la huella, reanudación, comprobación de tamaño y repetición inversa de muestras. `--solo` selecciona trabajo sin recortar el manifiesto; `--forzar` permite regenerarlo. No se reutilizan dibujos de otra huella global.
- `kit/secuencia.js`: carga por tiempo con caché de ImageBitmap acotada y cierre de recursos expulsados. No precarga un episodio completo. `render.mjs` espera `seek` asíncrono.
- `cache.mjs` y render: fuentes/configuración/página/perfil identifican segmentos. Audio se vuelve a unir sin invalidar imagen. Se manejan salida temprana y error de FFmpeg durante la alimentación, evitando dar por válido un segmento fallido.
- `assets/ejemplos/25d/`: escena original sencilla de lata, martillo y reacción para verificar un recorrido reutilizable. La revisión detectó un corte planificado un fotograma antes del dibujo disponible; se corrigió a f100. El primer plano final se documenta como reacción del rostro después de mostrar la lata en P02.

La revisión independiente encontró y motivó correcciones reales: salida temprana de FFmpeg, ámbito de rangos, comparación de PNG con tuplas de floats de alto coste, metadatos volátiles e imágenes de diagnóstico dentro de la caché visual. Se movieron informes/comprobaciones a `review` y la comparación de canales a Pillow. Otra prueba reveló que Blender escribía fecha/coste de render en los PNG aunque sus píxeles fueran iguales; se desactivaron esos campos variables. No se afirma un porcentaje de ahorro de RAM sin medición.

Uso mantenido en [references/25d.md](../../motion-studio/references/25d.md), con enlaces desde entrada, requisitos y README. La instalación de Claude se actualizó conservando respaldo de archivos sustituidos; su comprobación de contenido cubre 52 archivos. Las sesiones abiertas deben releer la guía: no se presume recarga automática de instrucciones.

## Resultados audiovisuales y validación

Rutas dentro de `C:/Users/danie/Documents/skill/review/make-short-research/`:

| Entrega | Imagen | Audio final | Evidencia |
| --- | --- | --- | --- |
| `reproduccion/exportaciones/prueba-claude-lata.mp4` | 6 s, 180 f, 1080×1920/30; recursos hechos por Claude con Blender | −14,1 LUFS; −1,3 dBTP | `reproduccion/review/verificacion.json`, hojas por plano y logs de Claude |
| `integrada/exportaciones/prueba-25d-integrada.mp4` | 6 s, 180 f de entrega; 72 dibujos a 12/s; escena original del adaptador | −14,1 LUFS; −1,3 dBTP | `integrada/review/verificacion.json`, `review/produccion` y generador |

Ambos MP4 pasan H.264/yuv420p, fps constantes, resolución, duración, conteo, SDR BT.709, ausencia de negro/congelación prolongada y duración/nivel de audio. Se inspeccionaron las hojas; no se asigna una nota de calidad global. `ritmo.py` pasa con avisos: mezcla mono en ambos, y el detector de la reproducción no reconoce sus cortes con barridos (informa un plano de 6 s). El JSON de cuatro planos y las imágenes muestran que ese conteo automático no representa el montaje real.

Pruebas realizadas:

- Generador inicial de la escena original: **72 PNG FHD en 110,76 s**, con tres instantes repetidos en orden inverso sin diferencias de canales. Reanudar sin cambios generó cero PNG. Tras las correcciones del adaptador se usó además una regresión pequeña para comprobar rangos, caché y rechazos sin rehacer toda la escena.
- Reproductor con ImageBitmap: cuatro instantes por proyecto, repetidos e inversos, idénticos. Se habían comprobado además ocho/seis instantes con el lector anterior. Esto no acredita el determinismo del generador upstream de Claude, que no se sometió a una prueba de orden inverso.
- Transcripción real: seis segundos del tutorial → **17 palabras** con tiempos; importación y SRT correctos, impacto de «Today» cuantizado a f62 a 30 fps. No se afirma exactitud perceptiva de esas marcas ASR ni se añadió esa voz al ejemplo de la lata.
- `tests/animacion/produccion_test.py`: seis casos de cobertura, impactos, formatos de voz, fps distintos de 30 y límites de captions/voz.
- `tests/animacion/secuencia-cache.test.mjs`: tiempo fuera de orden, recurso ausente, expulsión/cierre, consulta de sincronía y cambios de fuentes/perfil.
- `tests/animacion/render_cache.py`: exportación real, reutilización, invalidación por código y encoder fallido que termina con error; caché anterior conservada.
- `tests/animacion/recursos25d.py`: Blender real con tres dibujos pequeños; regeneración de uno conserva alcance, PNG y manifiesto, la primera comprobación no invalida la imagen, y GPU/dimensiones incorrectas fallan sin sustituir el manifiesto válido.
- Regresiones anteriores de encuadre (27 casos y siete entradas inválidas), 18 comprobaciones del kit y carta SDR real por muestra/borrador/final: correctas. La carta conservó error RGB máximo observado de 1/255.
- Validador de skill, auditoría de plantilla (14 archivos, cero errores/avisos), sintaxis y `git diff --check`: correctos.
- Reanudación medida de la exportación FHD integrada: **dos segmentos reutilizados, cero capturas nuevas, 3,43 s totales**, incluida comprobación de GPU y mux. El primer render de esa versión necesitó 184 s. Es reutilización de un mismo proyecto, no una comparación artística ni un benchmark entre sistemas.

## Límites pendientes

No se realizó escucha subjetiva ni reproducción continua perceptiva de las entregas. Las métricas y las hojas no sustituyen esa revisión. Tampoco se validó un Short narrado completo de 15–60 s, retención, el nivel artístico de las referencias, otros equipos/sistemas o una producción larga. La voz de pago y publicación quedan fuera de estas pruebas.

El adaptador no incluye un rig universal, autoaislamiento de personajes, reconstrucción automática de escenas desde un video ni un generador de gags. El SRT no se incrusta automáticamente. Las marcas ASR requieren revisión. Las huellas cubren fuentes locales declaradas; no aseguran reproducibilidad de recursos de red, dependencias externas omitidas o fuentes de imagen modificadas fuera del proyecto.

La integración implementa y prueba el recorrido técnico, con archivos audiovisuales revisables y fallos reconocidos. No convierte sus resultados en una garantía de calidad audiovisual ni da por terminada la revisión humana del contenido.
