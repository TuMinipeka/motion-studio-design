# Registro de mejoras

Las entradas describen cambios del repositorio, no versiones publicadas ni garantías de calidad audiovisual.

## Sin versión publicada — 2026-11-02

### Preparación del entorno y configuración de proyectos

- Se añade `motion-studio/scripts/preparar.py` para preparar Playwright, Chromium y fuentes en una carpeta compartida, comprobar Python/NumPy/Pillow, Node.js, FFmpeg/FFprobe y detectar el renderizador WebGL. La ubicación se configura con `MOTION_STUDIO_HOME`.
- Los instaladores pueden ejecutar esa preparación. Permiten omitirla con `-SinHerramientas` en PowerShell o `MOTION_SIN_HERRAMIENTAS=1` en Bash; la instalación de programas del sistema requiere `-Sistema`/`--sistema`.
- `nuevo.py` admite duración, fps y orientación vertical al generar el proyecto; `--sin-preparar` ejecuta solo la comprobación del entorno. Se conserva la protección frente a sobrescribir proyectos existentes.
- Validación: sintaxis Python, PowerShell y Bash; generación aislada con duración de 8 s, 24 fps y orientación vertical; confirmación de que `--sin-preparar` no solicita instalación y rechazo de un destino ya ocupado. La llamada a la preparación se simuló en esta prueba. Pendiente verificar la instalación completa real en Windows/macOS/Linux y los gestores del sistema.

### Dirección creativa y revisión de movimiento ya publicadas

- El commit [b6e1481](https://github.com/TuMinipeka/motion-studio-design/commit/b6e1481aa121f999bf175e96aef1be13385dd4bc) incorporó dirección creativa, storyboard, avisos breves con recomendaciones y análisis del lenguaje de referencia.
- Se añadió `--prueba=inicio,fin` para revisar un fragmento animado y se sustituyó la plantilla de barras por una demostración de continuidad de un sujeto.
- Validación de esa entrega: prueba técnica de 4 segundos y 48 fotogramas, decodificación y determinismo en diez instantes. Falta una evaluación del flujo actualizado ejecutado por Gemini/Argon sobre un encargo real. Detalles en [el análisis del resultado](docs/analysis/2026-11-02-motion-review.md).
