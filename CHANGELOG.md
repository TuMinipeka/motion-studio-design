# Registro de mejoras

Las entradas describen cambios del repositorio, no versiones publicadas ni garantías de calidad audiovisual.

## Sin versión publicada — 2026-11-03

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
