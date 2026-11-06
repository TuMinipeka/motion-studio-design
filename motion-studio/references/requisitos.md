# Requisitos técnicos por funcionalidad

Indica qué necesita cada parte de la skill, cómo se instala, cómo se comprueba y qué hacer si falta algo.

**Validado:** solo **Windows 11 + Direct3D 11 + NVIDIA RTX 3050 Laptop (6 GB)**, con AMD Ryzen 7 7445HS (6 núcleos, 12 hilos) y 16 GB de RAM.

**No validado:** macOS y Linux tienen instalador y rutas previstas, pero el render no se ha probado en ellos. Tómalos como "debería funcionar", no como garantía.

## Resumen del equipo

| Recurso | Mínimo | Recomendado | Notas |
|---|---|---|---|
| Sistema | Windows 10/11, macOS 13+ o Linux x86-64 con glibc reciente | Windows 11 | Solo Windows está validado |
| Arquitectura | x86-64 o ARM64 (Apple Silicon) | x86-64 | Playwright publica Chromium para las tres plataformas; ARM64 en Windows no se ha probado |
| CPU | 4 núcleos | 6–8 núcleos | Cada worker de `render.mjs` es un proceso de Chrome; la codificación x264 `slow` usa todos los núcleos |
| RAM | 8 GB, con `workers` 2–3 | 16 GB, con `workers` 6 | Con 16 GB y 6 workers funcionó. El consumo por worker no está medido: si el sistema se queda sin memoria, baja `workers` |
| GPU | WebGL 2 (vale la integrada) | Dedicada con 4 GB o más | Sin GPU funciona por CPU (SwiftShader), pero mucho más lento |
| Disco | 2 GB libres más el proyecto | 10 GB o más en SSD | ~720 MB de navegadores de Playwright, ~35 MB de herramientas compartidas; ~140 MB por minuto de 1080p60 en calidad final; las vistas de revisión son pequeñas |
| Red | Solo para instalar | — | El render no necesita conexión |

**Rendimiento medido:**
- **Plantilla de 6 s en 1080×1920 a 60 fps** (360 fotogramas, CRF 12 `slow`, 6 workers, RTX 3050): **21 s**, unos 17 fotogramas por segundo, incluido el arranque.
- Una escena con más carga dibuja más despacio. Proyecta el tiempo con `--prueba` antes de un render largo.
- Como orientación, un video sencillo de 10 min en 1080p60 tardaría unos 35 min, y en 30 fps, la mitad.

## Software común

| Herramienta | Versión | Lo usa | Instalación | Verificación |
|---|---|---|---|---|
| Python | 3.9+ (probado con 3.14) | `preparar.py`, `nuevo.py`, `ritmo.py`, `sheet.py`, `musica.py`, `verificar.py` | python.org, `winget install Python.Python.3.12`, `brew install python` o `apt install python3` | `python --version` (o `py -3` en Windows) |
| numpy | Reciente | `ritmo.py`, `musica.py` | `preparar.py`, que usa `pip install --user` | `python -c "import numpy"` |
| Pillow | Reciente | `sheet.py` | `preparar.py` | `python -c "import PIL"` |
| Node.js | 18+ para el render; **22.20+** para la CLI `skills` (instalación con `npx skills`) | `render.mjs`, `auditar.mjs` | `preparar.py --sistema` (winget, brew o apt) | `node --version` |
| FFmpeg y FFprobe | Compilación con **libx264** y el filtro **ebur128** (probado con 9.0.1 full build) | Codificación, sonoridad, `ritmo.py`, `verificar.py` | `preparar.py --sistema`: `Gyan.FFmpeg`, `brew install ffmpeg` o `apt install ffmpeg` | `ffmpeg -hide_banner -encoders` (busca libx264) y `-filters` (busca ebur128) |
| Playwright y Chromium | Probado con 1.64 | `render.mjs` | `preparar.py`, en `~/.motion-studio` (`MOTION_STUDIO_HOME`) | `preparar.py --comprobar` |
| Fuentes @fontsource | 12 familias | Tipografía | `preparar.py` | `preparar.py --comprobar` |

**Comprobación general:**
```bash
python scripts/preparar.py --comprobar   # código 0 si todo está listo; escribe ~/.motion-studio/estado.json
```

## Por funcionalidad

### 1. Preparación del entorno (`preparar.py`, `install.ps1` / `install.sh`)

| | |
|---|---|
| **Sistemas** | Windows (validado), macOS y Linux (instalador escrito, sin validar) |
| **Hardware** | El del resumen |
| **Dependencias** | Python 3.9+ para ejecutarlo; Node y FFmpeg pueden faltar al principio (`--sistema` los instala con permiso) |
| **Comandos** | `python scripts/preparar.py` · `--comprobar` · `--sistema` · instaladores con `-SinHerramientas` o `MOTION_SIN_HERRAMIENTAS=1` |
| **Limitaciones** | `--sistema` usa winget, brew o apt-get; otros gestores (dnf, pacman) no están contemplados. En Linux requiere sudo. |
| **Alternativas** | Instalar Node y FFmpeg a mano y repetir `preparar.py`. Sin permisos de administrador: un FFmpeg estático en el PATH del usuario. |

### 2. Creación de proyecto (`nuevo.py`)

| | |
|---|---|
| **Sistemas** | Los tres. La detección de GPU (`--listar-gpus`) solo funciona en Windows. |
| **Dependencias** | Python 3.9+ |
| **Comandos** | `python scripts/nuevo.py <carpeta> [--duracion S] [--fps N] [--vertical] [--gpu "nombre"] [--sin-preparar]` |
| **Limitaciones** | En macOS y Linux no detecta la GPU: hay que configurar `gpu.*` a mano en `motion.config.json`. |
| **Alternativas** | Copiar `assets/plantilla/` y editar `motion.config.json`. |

### 3. Animación, cámara, transiciones y motion graphics (`index.html`, `lib.js`, `kit/`)

| | |
|---|---|
| **Sistemas** | Los tres: es HTML, Canvas, SVG o WebGL dentro de Chromium |
| **Hardware** | Canvas 2D funciona incluso por CPU. Three.js o WebGL intenso necesitan una GPU real, con 2 GB de VRAM como mínimo y 4 GB o más recomendados. |
| **Dependencias** | Chromium de Playwright; Three.js solo si el brief lo usa (`npm i three` en el proyecto) |
| **Verificación** | `node auditar.mjs` · `node render.mjs --frames=1,3` · `--determinismo` |
| **Limitaciones** | Nada de relojes, `requestAnimationFrame`, `setTimeout`, transiciones CSS ni `Math.random`. El texto siempre con `crearTexto`. |
| **Alternativas** | Sin GPU: diseños 2D y `--gpu=cpu`. |

### 4. Renderizado (`render.mjs`)

| | |
|---|---|
| **Sistemas** | Windows con ANGLE `d3d11` (validado). macOS: `metal`; Linux: `vulkan` o `gl` (sin validar; ver `references/gpu.md`). |
| **Hardware** | Ver el resumen. Los `workers` (6 por defecto) multiplican la RAM y la VRAM. |
| **Dependencias** | Node 18+, Playwright y Chromium, FFmpeg con libx264 |
| **Configuración** | `motion.config.json`: `video`, `gpu` (`modo`, `angle`, `coincidir`), `workers`, `codificacion` |
| **Comandos** | `--frames` · `--prueba=a,b` · `--sheet` · `--determinismo` · `--ritmo` · `--borrador` · `--final` · `--pagina=` · `--workers=N` · `--gpu=modo` |
| **Verificación** | Línea `WebGL:` al arrancar; `python verificar.py` al terminar |
| **Limitaciones** | Captura fotograma a fotograma (no en tiempo real). Sin canal alfa: no puede generar capas transparentes para superponer a otro video. |
| **Alternativas** | Poca memoria: `--workers=2`. Sin GPU: `--gpu=cpu` (lento). Si el render se interrumpe, al relanzarlo solo rehace los segmentos que faltan. |

### 5. Audio (`audio/musica.py`)

| | |
|---|---|
| **Sistemas** | Los tres |
| **Hardware** | Cualquiera; usa la CPU |
| **Dependencias** | Python con numpy; FFmpeg con ebur128 (y con un decodificador para el formato de la pista del usuario, como MP3 o AAC) |
| **Comandos** | `python audio/musica.py` · `--pista tema.mp3 [--bpm N]` · `--voz voz.wav` |
| **Verificación** | La consola informa de los LUFS y de la verificación de pulsos; `verificar.py` sobre el video final |
| **Limitaciones** | Síntesis sencilla, sin paneo automático. Con `--sincro`, normaliza en dos pasadas a −14 LUFS y −1,5 dBTP antes de AAC; comprueba el MP4 con `verificar.py`. El modo clásico conserva su normalización anterior. No genera voz: la narración la aporta el usuario o una herramienta de texto a voz de su entorno. |
| **Alternativas** | Pista del usuario con `--pista`; sin audio, texto en pantalla como narración. |

### 6. Revisión: hoja de contacto, ritmo y determinismo (`sheet.py`, `ritmo.py`, `auditar.mjs`)

| | |
|---|---|
| **Sistemas** | Los tres |
| **Dependencias** | Pillow (`sheet.py`); numpy y FFmpeg (`ritmo.py`); Node (`auditar.mjs`) |
| **Comandos** | `node render.mjs --sheet && python sheet.py` · `node render.mjs --ritmo` · `python ritmo.py video.mp4 [--referencia a.mp4 --calibrar]` · `node auditar.mjs` |
| **Limitaciones** | Las métricas son heurísticas: no juzgan actuación ni narrativa. La detección de golpes sonoros es aproximada. |
| **Alternativas** | Ninguna: la skill exige estas herramientas. Si faltan, se instalan o se declara el paso como pendiente. |

### 7. Exportación y control final (`render.mjs --final`, `verificar.py`)

| | |
|---|---|
| **Sistemas** | Los tres |
| **Dependencias** | FFmpeg y FFprobe con libx264 y ebur128 |
| **Comandos** | `node render.mjs --final` → `python verificar.py` (o `python verificar.py ruta.mp4`) |
| **Salida** | H.264 High, `yuv420p`, AAC a 320 kbps (si hay audio), CRF 12 `slow` por defecto |
| **Limitaciones** | Salida SDR BT.709/rango limitado; no convierte HDR ni perfiles ICC. El codificador no limita picos de una mezcla externa: `verificar.py` los avisa. Sin perfiles por plataforma: la orientación y la duración se fijan en el brief. |
| **Alternativas** | Para reproductores antiguos, mantener `yuv420p` y H.264, que ya son los valores por defecto. |

### 8. Funcionalidades no disponibles

| Funcionalidad | Estado | Qué haría falta |
|---|---|---|
| B-roll, pantalla dividida y zooms animados en el modo edición | Pendiente (fase 4) | Nuevas operaciones de `montaje.py` y layouts en `editar.py` |
| Música, efectos, limpieza de voz y color en el modo edición | Pendiente (fase 4) | Cadena de audio y color en `editar.py` |
| Subtítulos incrustados automáticamente en el modo edición | Pendiente (fase 4) | Archivos ASS desde `analisis/palabras.json`. En animación ya hay SRT/marcas y consulta por `t` con `produccion.py`; ver `25d.md` |
| Capas con transparencia | No disponible | Modo `--alfa` en `render.mjs` (PNG con transparencia y ProRes 4444) |
| Color HDR/ICC y limitación de pico de cualquier mezcla externa | No disponible | Gestión de color y cadena de audio específica; SDR BT.709 ya está implementado y `musica.py --sincro` sí normaliza su mezcla |

Si el usuario pide algo de esta tabla, díselo antes de empezar y ofrece lo que sí se puede hacer.

### 9. Modo edición (`assets/edicion/`, `references/edicion.md`)

| | |
|---|---|
| **Sistemas** | Windows (validado con material sintético). macOS y Linux: los scripts son Python y FFmpeg multiplataforma, pero sin validar. La prueba sintética necesita voz de Windows o `espeak-ng`. |
| **Hardware** | Mínimo: 4 núcleos, 8 GB de RAM y un disco libre de unas 3 veces el tamaño de las grabaciones (copias normalizadas y caché de segmentos). Recomendado: un codificador H.264 por hardware (NVENC, AMF, QSV o VideoToolbox) y 16 GB. Whisper en GPU necesita NVIDIA y unos 3 GB de VRAM libres para large-v3-turbo en int8 (estimación). |
| **Niveles** | Núcleo: FFmpeg y numpy. Completo: + `faster-whisper` (pip) y un modelo (large-v3-turbo, ~1,6 GB, en `~/.motion-studio/modelos/whisper`). Whisper en GPU: + `nvidia-cublas-cu12` y `nvidia-cudnn-cu12` (~1,5 GB, `--whisper-gpu`; sin probar). |
| **FFmpeg** | Filtros `fps`, `scale`, `crop`, `pad`, `overlay`, `vstack`, `fade`, `loudnorm`, `highpass`, `signalstats`, `scdet` y el demuxer `concat`. Una compilación completa (gyan.dev, Homebrew o la de la distribución) los trae. |
| **Instalación** | `python scripts/preparar.py --edicion [--modelo small] [--whisper-gpu]` |
| **Verificación** | `python scripts/preparar.py --perfil` (codificadores probados de verdad, Whisper y nivel efectivo) · `python tests/edicion/probar.py` (repositorio) |
| **Rendimiento medido** | RTX 3050 / Ryzen 7 7445HS. Material de 33 s: normalizar 5–6 s por fuente con NVENC; transcribir 18–23 s con large-v3-turbo en CPU; revisión de 20 s en 5 s; final 1080×1920 con x264 `slow` en 10–16 s. Con 10 minutos de grabación, la transcripción en CPU rondaría los 6–7 minutos (estimación lineal, sin medir). |
| **Limitaciones** | Whisper adelanta los tiempos y omite muletillas (se corrige con energía, ver `edicion.md`). La elección de tomas es heurística. Sin subtítulos, B-roll, música ni color todavía. |
| **Alternativas** | Sin faster-whisper: nivel núcleo (cortes por silencios). Sin codificador por hardware: `libx264`. Poco disco: borrar `cache/` y `analisis/normalizados/` al terminar (se regeneran). |

### 10. Recursos 2.5D y sincronía en animación (opcionales)

- Referencias y plan de planos: Python, Pillow, FFmpeg/FFprobe; no necesitan Blender ni ASR.
- Transcripción de voz: `faster-whisper` y modelo local; probado large-v3-turbo en CPU/int8. `produccion.py --transcribir` usa FFmpeg para decodificar y evita la incompatibilidad observada de PyAV. No acredita alineación exacta.
- Recursos 3D: Blender **5.2.3 LTS** con EEVEE/OpenGL, probado en Windows/RTX 3050. `recursos25d.py` exige la GPU real, genera PNG y registra huellas; no instala Blender ni cambia preferencias del sistema. Otros sistemas/backends siguen sin probar.
- Reproducción: `kit/secuencia.js` usa `fetch` e `ImageBitmap` de Chromium, con cierre de bitmaps expulsados. El render espera `seek(t)` asíncrono.
- Uso y límites: [25d.md](25d.md). No añade exportación de video con alfa, rig universal, generador de voces ni publicación.
