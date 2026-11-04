# Registro de mejoras

Las entradas describen cambios del repositorio, no versiones publicadas ni garantías de calidad audiovisual.

## Sin versión publicada — 2026-11-03

### Revisión de nevera_redes.mp4: divulgación 3D y visibilidad del mecanismo

- **Problema observado:** un Short 3D low-poly con tipografía retro y acabado nítido perdía los extremos de sus flujos en el encuadre vertical; personajes y rótulos competían con la explicación. La guía no distinguía suficientemente este lenguaje del corto ilustrado o el pixel art y desaconsejaba los diagramas en el desarrollo.
- **Cambio:** `references/estilos.md` concreta lenguaje, acabado e identidad en el brief existente. Para divulgación prioriza causa, recorrido y resultado; protege elementos críticos frente a recortes/oclusiones, reduce competencia de interfaz y distingue números ilustrativos de mediciones. Se actualizan entrada, dirección, preproducción, rúbricas y README, sin otro cuestionario ni aprobación rutinaria.
- **Código:** `comprobarPuntos3D()` añade al kit un diagnóstico opcional de puntos del mundo para cámaras Three.js, con margen y profundidad; no requiere Three.js en proyectos 2D. No detecta oclusión, volumen completo, textos o calidad artística.
- **Validación real:** copia aislada del proyecto identificado por SHA-256; muestra de 3,5 s/105 fotogramas en 1080p30 con RTX 3050, mezcla y CRF 12/slow; cuatro instantes deterministas y decodificación correcta. En cinco instantes, 2/4 → 4/4 puntos críticos dentro del margen tras abrir cámara y acortar recorridos. Pruebas de perspectiva/ortográfica, recorte, márgenes e inmutabilidad; sintaxis, auditoría y validador de la skill.
- **Resultado y límites:** mejora provisional de claridad del plano de 6 a 8/10, sin acreditar 9/10 global, retención, fluidez percibida o mejora de velocidad. La muestra no lleva etiquetas de color y no sustituye la validación del final. Quedan pendientes escucha, salto/aterrizaje, precisión del guion y enlaces con los planos vecinos. Original y proyecto conservados.
- [Análisis por estilo, notas, comparación y feedback](docs/analysis/2026-11-03-nevera-review.md).

### Revisión de 3.mp4: foco narrativo, encuadre por zona y muestras en dos etapas

- **Problema observado:** en un corto lento y oscuro, una reacción importante quedaba en un encuadre amplio; al acercarse, sus capas rasterizadas necesitaban más detalle. Persistían reglas rígidas de cámara, rebotes, paleta y densidad sonora incompatibles con adaptar el estilo.
- **Cambio:** `encuadreZona()` en el kit ajusta una región declarada en ambos ejes con margen. Preproducción, dirección y rúbricas priorizan lectura del foco, cobertura emocional y pausas motivadas; se documenta la densidad de capas para el acercamiento máximo, sin aumentar globalmente resolución o fps.
- **Render:** `--prueba` separa la codificación de imagen y la unión del audio, copiando el video sin recomprimirlo. Conserva el perfil final, los tiempos alineados y los casos sin mezcla. La espera del intento inicial no se atribuye con certeza a un interbloqueo ni se afirma una mejora de velocidad.
- **Validación:** 27 casos de encuadre y 7 entradas inválidas; muestra aislada de 4 s/240 fotogramas en 1080p60 con cinco instantes deterministas; cuatro casos de regresión de audio. Sintaxis, auditoría, enlaces y estructura de la skill correctos.
- **Resultado y límites:** el rostro ocupa un 45,2 % más de altura geométrica y mejora su lectura en las imágenes revisadas. La toma requiere densidad extra y tuvo un coste alto, sin benchmark comparativo. No se acredita 9/10 global, fluidez perceptiva ni calidad sonora artística. El original se conserva.
- [Análisis, notas, comparación y límites](docs/analysis/2026-11-03-video-3-review.md).

### Ficha breve por plano en el storyboard

- **Problema:** la lista de preproducción ya pedía acción, cámara y sonido, pero no ofrecía una ficha reutilizable ni exigía concretar la iluminación por plano.
- **Cambio:** `preproduccion.md` integra seis campos (intención, cámara y composición, iluminación, acción, sonido y enlace), identificador, escena, tiempos y papel narrativo. Incluye plantilla y dos planos conectados. Las definiciones comunes se heredan por identificador dentro del storyboard o brief; se completan los storyboards existentes sin otro documento obligatorio ni nuevas aprobaciones.
- **Adaptación:** permite cámara fija, gráficos planos sin sombras y piezas silenciosas; no impone iluminación volumétrica ni una estética. Los pendientes se declaran y se resuelven antes de presentar el plano como listo para animar.
- **Validación:** revisión editorial de los dos planos (6 s en total, continuidad de mano, cuaderno, luz y audio), enlaces locales, formato y estructura de la skill. Se actualizan README, entrada de la skill y rúbrica de preproducción para usar la misma ficha.
- **Límites:** esta entrega define el formato y su revisión editorial; no añade puntuación por escena ni un validador automático de storyboards. No se renderizó un video ni se acredita calidad audiovisual con el ejemplo escrito.

### Coherencia de la guía al publicar

- Se corrige una frase antigua del Paso 0 que aún enumeraba la edición de grabaciones como no disponible. Ahora remite al modo edición y conserva sus límites documentados.

### Modo edición de videos grabados (fases 1–3 de la propuesta)

**Problema.** La skill solo podía dibujar videos. Editar una grabación (el usuario hablando a cámara, pantallas de OBS) era imposible: no había ingesta, transcripción, línea de tiempo de clips ni render de video real. La propuesta aprobada (análisis → planificación → edición → render → evaluación → iteración) se implementa por fases. Esta entrega cubre las fases 1–3.

**Qué se añade:**
- **`preparar.py --perfil`:** guarda el perfil del equipo en `estado.json`.
  - Prueba de verdad cada codificador H.264 (NVENC, AMF, QSV, VideoToolbox, x264).
  - Mide GPU y VRAM, RAM, disco y núcleos.
  - Comprueba Whisper: CUDA solo si carga y transcribe.
  - Fija el nivel efectivo (núcleo, completo o avanzado).
- **`preparar.py --edicion [--modelo] [--whisper-gpu]`:** instala el nivel completo (faster-whisper y el modelo).
- **`nuevo.py --edicion`:** proyecto con `fuentes/` y las herramientas de `assets/edicion/`, más `verificar.py` y `ritmo.py` de la plantilla.
- **`analizar.py`:**
  - ingesta;
  - salida propuesta desde la cámara (nada fijo);
  - copias a fps constante con el codificador del perfil;
  - sincronía por correlación de ataques de audio;
  - transcripción por palabra;
  - bordes de frase corregidos con la energía (Whisper adelanta los tiempos);
  - sonidos sin palabra (muletillas que Whisper omite);
  - palabras sin voz (alucinaciones);
  - tomas repetidas con la elegida y el motivo;
  - luz por segundo y escenas de pantalla.
- **`planificar.py`:** el corte en papel (`GUION-MONTAJE.md` y `analisis/guion.json`). Quita tomas descartadas, muletillas, alucinaciones y pausas largas, con márgenes medidos sobre la voz real y zoom alterno en los jump cuts.
- **`montaje.py`:** la línea de tiempo como fuente de verdad.
  - Operaciones: `validar`, `info [--palabras]`, `cortar`, `quitar --palabras|--desde/--hasta`, `layout completo|pantalla|pantalla+pip` (pantalla sincronizada por el desfase), `zoom`, `transicion`, `diff` y `deshacer`.
  - Se guardan versiones y se valida antes de guardar.
  - Los bordes se ajustan a fotograma y a pausas entre palabras, y no se crean clips de menos de 0,2 s.
- **`editar.py`:**
  - render por segmentos con caché por hash;
  - revisión con el codificador por hardware y final con x264 (configurable en `salida`);
  - voz con muestras exactas y microfundidos solo donde la voz salta;
  - `loudnorm` en dos pasadas;
  - salida BT.709 en `yuv420p`.
- **`qc.py`:**
  - **Bloqueante:** montaje válido; cortes dentro de palabras o con la voz sonando; palabras del guion perdidas; duración; clics; WER de la retranscripción; determinismo de un segmento; `verificar.py` en el final.
  - **Aviso:** lo quitado que vuelve, jump cuts sin cambio y silencios largos.
- **`verificar.py`:** sin `motion.config.json`, toma la salida y la duración de `montaje.json`.
- **Pruebas:** `tests/edicion/sintetico.py` (material con respuestas conocidas) y `tests/edicion/probar.py` (de principio a fin, fallos provocados y regresión del modo animación).
- **Documentación:**
  - `references/edicion.md`;
  - rúbricas §15–19 en `rubricas.md`;
  - la sección 9 de `requisitos.md`;
  - "Dos modos" en `SKILL.md`, cuya descripción incluye ahora la edición de grabaciones;
  - el README.

**Validación** (Windows 11, RTX 3050, Ryzen 7 7445HS):
- **`probar.py`: 22/22.**
  - Desfase medido 1,370 s frente a 1,37 s esperados.
  - Las 2 tomas repetidas agrupadas y resueltas a favor de la versión completa.
  - Las 5 frases que se conservan, enteras.
  - Las 2 tomas descartadas y la muletilla, fuera.
  - Render final 1080×1920 con `qc.py --retranscribir --determinismo` OK (WER 0 %) y `verificar.py` OK, incluidos BT.709 y −1,0 dBTP.
  - Los tres fallos provocados (corte dentro de una palabra, palabra perdida, clic) se detectan.
  - La plantilla de animación pasa `auditar.mjs`, `--determinismo`, `--final` y `verificar.py`.
- **Tiempos con 33 s de material:**
  - transcripción en CPU: 18–23 s con large-v3-turbo;
  - render de revisión: unos 5 s;
  - render final: 10–16 s.
- **Nivel núcleo** (sin transcripción): funciona; deja avisos de silencios de unos 0,6–0,7 s.
- **Errores encontrados y corregidos durante la validación:**
  - Whisper daba finales 0,1–0,3 s antes que la voz real, lo que recortaba sílabas.
  - Un cambio de layout sobre voz continua llevaba microfundido, lo que dejaba un hueco a mitad de palabra.
  - `quitar` no eliminaba una palabra más corta de 0,2 s.
  - La API de PyAV instalada con Python 3.14 rompía la lectura de archivos de faster-whisper; ahora se le pasa el audio ya decodificado.

**Límites:**
- **Solo material sintético** (voz de Windows, sin ruido real ni muletillas naturales). Falta la grabación real del usuario para validar la elección de tomas, las muletillas y la sincronía móvil–OBS.
- **Whisper en GPU sin probar:** no se instalaron las bibliotecas CUDA.
- **macOS y Linux sin validar.**
- **Pendiente (fases 4–6):** subtítulos, B-roll, pantalla dividida, zooms animados, gráficos con transparencia, música, limpieza de voz, color, curva de retención sobre la línea de tiempo y modo autónomo.

### Rúbricas de calidad, requisitos por funcionalidad y verificación de la exportación

**Problema:**
- La revisión puntuaba siete aspectos generales sin criterios por funcionalidad. Las auditorías mostraron notas propias infladas y defectos técnicos que nadie detectaba: color sin etiquetar y true peak de −0,2 y +1,7 dBTP.
- Los requisitos estaban repartidos entre el README y `preparar.py`, sin hardware mínimo, sin cifras de rendimiento y sin una lista de lo que la skill no hace.

**Qué se añade:**
- **`references/rubricas.md`:** escala común (1–10 con bandas de entrega) y 14 funcionalidades. Para cada una: criterios medibles, errores frecuentes, cómo se detectan, cómo se corrigen y qué comprobación automática la cubre.
  - Funcionalidades: entorno, preproducción, animación, cámara, transiciones y montaje, motion graphics, texto y subtítulos, audio, sincronización, determinismo, ritmo, render, exportación y proceso de revisión.
  - Reglas: una comprobación bloqueante que falle limita esa funcionalidad a 4, y la nota global no supera en más de 1 punto a la peor.
  - Los fallos de `ritmo.py` exigen diagnóstico, pero no fijan la nota artística, como en la revisión del episodio Ojalá No.
- **`references/requisitos.md`:** sistemas (solo Windows validado), hardware mínimo y recomendado, software y versiones, instalación, comandos de verificación, limitaciones y alternativas para cada funcionalidad. Incluye una tabla de lo que **no** está disponible (edición de grabaciones reales, subtítulos desde voz, capas con transparencia, etiquetas de color y limitador de pico), para avisar al usuario antes de empezar.
- **`verificar.py` (plantilla):**
  - **Falla (código 1)** si el códec no es H.264 o los píxeles no son `yuv420p`; si resolución, fps, duración o número de fotogramas no coinciden con la config; si hay fps variable; si falta el audio o no está a −14 ±1 LUFS cuando hay `audio/final.wav`; si audio y video duran distinto; o si hay negro casi puro de 1 s o más sin declarar.
  - **Avisa** del color sin etiquetas BT.709, del true peak por encima de −1 dBTP y de la imagen congelada 4 s o más fuera de las pausas declaradas.
  - Fuera del proyecto, no compara con la config.
  - El informe queda en `review/verificacion.json`.
- **`SKILL.md`:** el Paso 0 remite a los requisitos y a la lista de lo no disponible; el Paso 3 puntúa con las rúbricas; el Paso 4 sustituye la comprobación manual con `ffprobe` por `verificar.py`. El README enlaza ambos documentos.

**Validación:**
- **Render medido de la plantilla:** 6 s en 1080p60 con CRF 12 `slow` y 6 workers en la RTX 3050 tardó 21 s (unos 17 fotogramas por segundo, con el arranque incluido).
- **`verificar.py` sobre:**
  - **la plantilla:** OK, con aviso de color;
  - **el video stickman:** OK, con avisos de color y de pico de −0,2 dBTP;
  - **`manana.mp4`:** OK, con aviso de pico de +1,7 dBTP.
- **Casos de fallo provocados:**
  - 2 s de negro en mitad del video;
  - `audio/final.wav` presente sin pista de audio;
  - sonoridad de −47,9 LUFS;
  - recodificación a 30 fps (detectó fps, duración y fotogramas).
- **Ajuste durante la prueba:** con el umbral inicial (`pix_th` 0,06 y 0,25 s), el fondo azul marino de la plantilla y un fundido a negro de 0,4 s del video stickman se marcaban como negro. Se fijó en `pix_th` 0,02 y 1 s.

**Límites:**
- Las rúbricas no son una prueba automática de calidad artística; la nota sigue saliendo de ver y escuchar.
- macOS y Linux siguen sin validar. El consumo de RAM por worker no está medido.
- Los avisos de color y pico se mantienen hasta que se apruebe la mejora "perfil de publicación".

### Revisión del episodio Ojalá No: encuadre y muestras con audio

- El resultado real mostraba texto recortado por acercamientos y correcciones de ritmo mediante cámara continua. Se priorizan acción y lectura, cámara con límites y curvas según intención; se retiran las obligaciones de rebote, deriva permanente y puntuación artística condicionada al detector de ritmo.
- `--prueba` incorpora el intervalo de `audio/final.wav` si existe, alineado al primer fotograma capturado, con AAC y el perfil final de video. `--sin-audio` mantiene la prueba muda; si falta mezcla se informa del pendiente. No añade normalización por fragmento ni modifica la autorización del completo.
- Se evita renderizar obligatoriamente el ejemplo del kit y se pide que la muestra represente las dificultades reales, usando las revisiones existentes.
- Validación: muestra aislada de 7,5 s/450 fotogramas 1080p60 en RTX 3050, cuatro instantes deterministas, decodificación y metadatos correctos. Fixture fraccional a 12 fps: audio alineado (correlación 0,99675), casos mudo y sin mezcla correctos. Sintaxis, auditoría y validador estructural correctos.
- [Análisis, notas provisionales y comparación](docs/analysis/2026-11-03-ojala-review.md). Se verifica una mejora de lectura, no una nota global 9/10 ni retención; reproducción/escucha perceptiva pendiente. El proyecto original se conserva.

### Comprobaciones adicionales al preparar el commit

- Sintaxis Python/JavaScript, configuración JSON, enlaces locales y validación estructural de la skill correctos. La auditoría de la plantilla revisó cinco archivos sin errores ni avisos.
- El ejemplo del kit pasó seis instantes repetidos y en orden inverso, incluidos 1,15 y 1,16 s, en una copia técnica vertical de 1080 × 1920 a 12 fps usando CPU.
- Un video sintético de 24 s, con 8 s de movimiento y 16 s de imagen fija, activó la detección de caída de energía. Al declarar esa pausa, dejó de fallar por ese motivo; los demás umbrales se ajustaron en la prueba para aislar ese comportamiento.
- Estas comprobaciones no repiten las auditorías artísticas o de videos anteriores descritas abajo, ni acreditan la calidad de un encargo nuevo completo.

### Curva de energía: re-ganchos planificados en el storyboard y medidos por tramos

**Problema.** En la auditoría de un video stickman de 121 s hecho por Claude con la skill (6,5/10), los primeros 15 s eran fuertes, pero el resto decaía:
- El movimiento mediano cayó de 4,5 a 1,1–1,4 en 30–45 s, 60–75 s y 75–90 s, con un 53–60 % de tiempo casi quieto.
- Los golpes de sonido bajaron un 45 % tras el gancho y el estéreo se quedó estrecho y sin cambios (0,14–0,24).
- Aun así, `ritmo.py` lo aprobaba, porque la media global de la pieza escondía esos tramos.
- Nada en la skill pedía planificar re-ganchos ni repartir los recursos de la apertura.

**Qué se añade:**
- **Preproducción** (`references/preproduccion.md`): sección "Curva de energía y re-ganchos".
  - La curva se diseña al estructurar el guion: gancho, re-ganchos (cada 8–12 s en piezas de menos de 60 s, cada 15–25 s en las largas), pausas con motivo, clímax de acto y cierre.
  - Cada re-gancho nace del contenido. Los recursos de la apertura se catalogan y se reparten por los clímax.
  - Las láminas de título duran 1,5 s como máximo; ningún diagrama fijo pasa de 4 s; el sonido sigue la curva.
  - Cada plano del storyboard indica su papel en la curva. Los tiempos se copian a `motion.config.json` → `curva`.
- **`ritmo.py`:** tabla por tramos (15 s, o una cuarta parte en piezas de menos de 60 s) comparada con la apertura.
  - Falla si un tramo cae por debajo de `caidaMin` (0,5) del movimiento de la apertura con al menos `caidaQuieto` (30 %) de tiempo quieto, o si dos tramos seguidos pasan de `tramoQuietoMax` (50 %) de tiempo quieto.
  - Las pausas declaradas en `curva.pausas` no cuentan como caída ni como tramo muerto.
  - Avisa si un re-gancho planificado no tiene corte ni movimiento fuerte, si pasa demasiado tiempo entre re-ganchos (25 s; 12 s en piezas de menos de 60 s) o si un proyecto de más de 20 s no tiene curva.
  - Con sonido, avisa si los golpes por segundo bajan del 60 % de la apertura, si el nivel cae más de 4 dB o si el estéreo no pasa de 0,3.
  - `--calibrar` deriva también `caidaMin` y `tramoQuietoMax` de las referencias.
  - La curva planificada solo se aplica a videos del propio proyecto, no a referencias externas.
- **`SKILL.md`** (Paso 1 y Paso 3) y **`references/direccion-movimiento.md`**: construir siguiendo la curva, nueva señal de deriva hacia una presentación y declaración de pausas.

**Validación:**
- El video stickman pasa a fallar en 30–45 s, 60–75 s y 75–90 s, con avisos de densidad sonora y estéreo.
- Con una curva de prueba en una copia del proyecto:
  - una pausa declarada en 75–90 s deja de contar;
  - los huecos de más de 25 s sin re-gancho se avisan;
  - dos re-ganchos puestos en momentos quietos (36 s y 80 s) se detectan como "no se ve".
- Nueve shorts propios anteriores (`studio-8bit`, `motion-idea`):
  - cuatro pasan;
  - tres fallan por caídas con un 44–60 % de tiempo quieto (dos de ellos ya fallaban por tramos muertos);
  - uno falla solo por micromovimiento global, como antes;
  - uno falla por una caída nueva, `ojos-de-perro` (12–24 s, 46 %, 50 % quieto).
  - El cierre calmado pero en movimiento de `tunel-a-traves-de-la-tierra` (43 %, 10 % quieto) ya no falla gracias a la condición de tiempo quieto.

**Límites:**
- Los umbrales son una primera calibración sobre pocos videos; conviene recalibrarlos con referencias del estilo buscado.
- La detección de golpes sonoros es heurística: por eso el sonido solo avisa.
- La regla de re-ganchos no se ha probado todavía en un encargo nuevo de principio a fin.

## Sin versión publicada — 2026-11-02

### Muestra aprobada y completo con la misma calidad alta

- `--prueba` usa el perfil `codificacion.final` del proyecto en lugar de CRF 20/preset `fast`. Conserva resolución y fps; sigue siendo una muestra sin audio de hasta 10 segundos.
- El aviso «Aprobar y generar completo» valida la muestra y autoriza continuar con `--final` en calidad alta. No se pide otra vez la misma aprobación ni se intercala automáticamente `--borrador`; este modo se conserva para quien lo elija expresamente.
- El primer completo sigue sujeto a revisión y correcciones, con el acabado y calidad visual aprobados. La vista diagnóstica `--ritmo` no se presenta como una muestra de calidad final.
- Validación: pruebas técnicas aisladas con los perfiles 12/slow (por defecto) y 17/medium (personalizado). En cada caso, la muestra de 1 s/12 fotogramas y el completo de 2 s/24 fotogramas conservaron 320 × 180 a 12 fps y las mismas opciones x264, verificadas en el flujo codificado; ambos archivos se decodificaron correctamente. Se validaron sintaxis, estructura y enlaces. No se produjo un video del usuario ni se evaluó un resultado artístico nuevo.


### Kit de movimiento: curvas, cámara y transiciones (sin personaje genérico)

**Problema.** La skill no aportaba medios para el movimiento ni el montaje: cada modelo dibujaba desde cero con primitivas de canvas. En la auditoría de 2026-11-02 (4,75/10) sobre dos pruebas de otros modelos (Gemini 4 Argon en `procrastinacion-short`, y `el-contador-invisible`), el resultado fueron figuras de palo, poses interpoladas sin anticipación ni rebote, y una cámara limitada a zoom o corte.

**Qué se añade:**
- **`lib.js`:** catálogo `ease` (incluye `saleBack`, `saleExpo`, `saleElastica` y `escalon`), `resorte()` (oscilador amortiguado analítico, sin estado), `mezclar()` de números, arrays y objetos, `claves()` para animación pose a pose, y `ruidoSuave()` con semilla.
- **`kit/camara.js`:** `encuadre()` (general, conjunto, medio, medioCorto, primerPlano, detalle) calculado desde la base y el alto del sujeto, `temblor()` por impulsos con ruido suave, `camaraEnMano()`, `aplicarCamara()` y `paralaje()` por capas.
- **`kit/transiciones.js`:** corte, whip con estela de movimiento, empuje, barrido, iris, zoom a través, flash y corte por forma, más `montaje()` para encadenar planos. Los lienzos auxiliares se crean una vez y se limpian con `reset()` en cada uso.
- **`kit/ejemplo.html`:** 8 s verticales.
  - Una pelota con anticipación, caída que acelera, aplastamiento en el impacto y rebotes que se asientan.
  - Corte a detalle con temblor y paralaje.
  - Whip a tipografía que cae con resorte, iris y contrapicado con estrellas.
- **`render.mjs --pagina=`:** renderiza otra página del proyecto, como el ejemplo. La plantilla `index.html` carga el kit.
- **Documentación:** `references/kit.md` (timing, gramática de planos, transiciones y una guía para diseñar y animar personajes propios). La sección "Estilo visual" del `SKILL.md` remite a ella.

**Personaje genérico retirado.** Durante este cambio se probó un `kit/personaje.js` (esqueleto de vista frontal con IK, 12 poses, 10 caras y ciclos de caminar) y se eliminó antes del commit.
- **Prueba:** Codex (GPT-6.1 Sol), con un encargo nuevo y sin referencias ("Apagón", 28 s), lo usó.
- **Resultado:** el cuerpo actuó como una marioneta. Caminaba deslizándose de frente, un brazo subía con el resto congelado y no había desplazamiento de peso ni movimiento secundario.
- **Contraste:** los mejores momentos del mismo video (ojos, parpadeo, mirada al cielo, cortes) no dependían del rig.
- **Conclusión:** la plantilla de cuerpo limitaba al modelo en lugar de ayudarle. Se sustituye por principios de actuación y diseño por plano.

**Validación**, en un proyecto vertical de 1080×1920 a 30 fps generado con `nuevo.py`:
- Auditoría sin errores ni avisos.
- `--determinismo` OK en 10 instantes del ejemplo, incluidos el impacto con corte (1,15–1,16 s), el centro del whip y el del iris.
- `--ritmo` del ejemplo: mediana 4,37, micro 14 %, racha 1 s, 37,5 cortes/min.
- Revisión de fotogramas.
- La versión con personaje corrigió dos defectos durante su revisión: el whip dejaba un fotograma vacío en su centro, y una cámara cortaba la cabeza en un salto. La corrección del whip se conserva.

**Límites:**
- El kit no dibuja nada por sí mismo: la calidad de personajes y escenarios sigue dependiendo del modelo y del brief.
- La guía de personajes no se ha probado todavía en un encargo real.
- Las métricas no acreditan calidad artística.

### Convención de commits y documentación continua

- Se añaden `CONTRIBUTING.md` y `AGENTS.md` para mantener Conventional Commits, agrupar cambios por propósito y registrar mejoras junto con su código. La historia publicada se conserva.
- El README enlaza el changelog y la guía de contribución. Las entradas separan comportamiento, comprobaciones y límites; no se asigna una versión de lanzamiento inexistente.
- Validación: enlaces locales, bloques Markdown y `git diff --check`. La convención de mensajes se revisa manualmente; no se añadió un hook automático.

### Audio, ritmo y diagnóstico del render

- Se añade `audio/musica.py` a la plantilla: síntesis con semilla, escritura de pulsos en `beats.json`, medición de una pista externa y mezcla opcional de voz con reducción de música. Se busca −14 LUFS mediante medición de FFmpeg.
- Se añade `render.mjs --ritmo`: captura la composición completa a 10 fps y genera una vista de 480 px de ancho. `ritmo.py` estima movimiento, intervalos de baja variación y cortes, con umbrales configurables y calibración por referencias.
- El renderizador puede resolver Playwright y fuentes desde las herramientas compartidas. `crearTexto(ctx)` rasteriza texto en lienzos auxiliares; la plantilla reinicia el contexto entre fotogramas. La auditoría avisa sobre texto directo y contextos sin reinicio, y el diagnóstico de determinismo guarda imágenes con diferencias y sus zonas.
- Se documentan las herramientas y la narración en el README y en la skill.
- Validación: comprobación de sintaxis JavaScript/Python y auditoría estática sin errores ni avisos. La plantilla aislada de 640 × 360 pasó diez instantes de determinismo y produjo una prueba de 4 s/48 fotogramas. Se generaron dos WAV de 6 s idénticos byte a byte, medidos a −14,0 LUFS, y una vista de ritmo de 6 s a 10 fps. El análisis de esa plantilla emitió código 1 por baja variación, conforme a sus umbrales; no se interpreta como fallo del render ni como evaluación artística completa.
- Límites: pendientes las ramas con pista externa, voz/ducking y calibración con múltiples referencias. No se realizó escucha subjetiva. La diferencia de píxeles y la detección de cortes son heurísticas sensibles a tamaño, contraste y composición; no acreditan actuación ni calidad narrativa por sí solas.

### Preparación del entorno y configuración de proyectos

- Se añade `motion-studio/scripts/preparar.py` para preparar Playwright, Chromium y fuentes en una carpeta compartida, comprobar Python/NumPy/Pillow, Node.js, FFmpeg/FFprobe y detectar el renderizador WebGL. La ubicación se configura con `MOTION_STUDIO_HOME`.
- Los instaladores pueden ejecutar esa preparación. Permiten omitirla con `-SinHerramientas` en PowerShell o `MOTION_SIN_HERRAMIENTAS=1` en Bash; la instalación de programas del sistema requiere `-Sistema`/`--sistema`.
- `nuevo.py` admite duración, fps y orientación vertical al generar el proyecto; `--sin-preparar` ejecuta solo la comprobación del entorno. Se conserva la protección frente a sobrescribir proyectos existentes.
- Validación: sintaxis Python, PowerShell y Bash; generación aislada con duración de 8 s, 24 fps y orientación vertical; confirmación de que `--sin-preparar` no solicita instalación y rechazo de un destino ya ocupado. La llamada a la preparación se simuló en esta prueba. Pendiente verificar la instalación completa real en Windows/macOS/Linux y los gestores del sistema.

### Dirección creativa y revisión de movimiento ya publicadas

- El commit [b6e1481](https://github.com/TuMinipeka/motion-studio-design/commit/b6e1481aa121f999bf175e96aef1be13385dd4bc) incorporó dirección creativa, storyboard, avisos breves con recomendaciones y análisis del lenguaje de referencia.
- Se añadió `--prueba=inicio,fin` para revisar un fragmento animado y se sustituyó la plantilla de barras por una demostración de continuidad de un sujeto.
- Validación de esa entrega: prueba técnica de 4 segundos y 48 fotogramas, decodificación y determinismo en diez instantes. Falta una evaluación del flujo actualizado ejecutado por Gemini/Argon sobre un encargo real. Detalles en [el análisis del resultado](docs/analysis/2026-11-02-motion-review.md).
