# Registro de mejoras

Las entradas describen cambios del repositorio, no versiones publicadas ni garantías de calidad audiovisual.

## Sin versión publicada — 2026-11-02

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
