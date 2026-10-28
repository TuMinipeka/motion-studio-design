# Motion Studio — skill para Claude Code

Skill para **crear y renderizar videos nuevos** como una función pura del tiempo (`window.seek(t)`), sin HyperFrames, Remotion ni ningún otro framework de video. Se renderiza con Chrome sin interfaz (Playwright), **la GPU que tú elijas** y FFmpeg (H.264, `yuv420p`).

Se activa sola cuando le pides a Claude Code crear o renderizar un video nuevo.

## Qué hace

1. **Guion primero:** estructura el guion y espera tu aprobación antes de renderizar nada.
2. **Proyecto listo:** crea la carpeta del video desde una plantilla (`index.html`, `render.mjs`, `auditar.mjs`, `beats.json`, `sheet.py`, `motion.config.json`) y detecta tus GPU.
3. **Reglas de Motion Studio:** contrato de renderizado, estilo visual y sonido (resumen abajo).
4. **Comprobaciones del contrato:** `node auditar.mjs` (busca `setTimeout`, `requestAnimationFrame`, `Math.random`, transiciones CSS y relojes reales) y `node render.mjs --determinismo` (el mismo `t` repetido y en orden inverso debe dar el mismo fotograma).
5. **Ciclo de revisión:** hoja de contacto con un fotograma por pulso, 6 criterios del 1 al 10, corregir los 3 peores y repetir hasta que todos lleguen a 8.
6. **Render:** `--borrador` (CRF 16) y `--final` (CRF 12, preset slow), por segmentos que se reanudan si se interrumpe.

## Ejemplo del resultado

[`ejemplo/XEON_motion_ejemplo.mp4`](ejemplo/XEON_motion_ejemplo.mp4): video de 3 minutos hecho con este flujo (copia ligera: 1080p a 30 fps; el original se renderizó a 60 fps con CRF 12). Detalles en [`ejemplo/README.md`](ejemplo/README.md).

## Requisitos

- [Claude Code](https://claude.com/claude-code)
- Node.js y **FFmpeg / FFprobe** en el PATH
- Playwright con Chromium, en la carpeta del video o en una superior: `npm i playwright` y `npx playwright install chromium`
- Python 3 con Pillow (`pip install pillow`) para la hoja de contacto
- Una GPU con WebGL 2. Probado solo en **Windows 11 con Direct3D 11** y una NVIDIA RTX 3050; otros sistemas no están probados.

## Instalación

Windows (PowerShell):

```powershell
.\install.ps1
```

macOS / Linux:

```bash
./install.sh
```

Copia `motion-studio/` a `~/.claude/skills/` (global). Para instalarla solo en un proyecto: `.\install.ps1 -Destino .claude\skills` (o `./install.sh .claude/skills`). Después abre una sesión nueva de Claude Code.

## Elegir la GPU

Al crear cada video, `scripts/nuevo.py` lista tus GPU y escribe la elegida en `motion.config.json`:

```json
"gpu": { "modo": "alto-rendimiento", "angle": "d3d11", "coincidir": "NVIDIA", "nombre": "NVIDIA GeForce RTX 3050" }
```

Puedes forzar otra con `python scripts/nuevo.py <carpeta> --gpu "Radeon"`, o cambiarla a mano. Si no se obtiene, `render.mjs` avisa en lugar de renderizar en silencio por CPU. Guía completa: [`motion-studio/references/gpu.md`](motion-studio/references/gpu.md).

## Las reglas, en breve

- **Contrato:** cada fotograma lo dibuja `window.seek(t)`; sin transiciones CSS, `setTimeout` ni `requestAnimationFrame`; sin estado entre fotogramas; ruido solo con semilla (`mulberry32`).
- **Estilo:** nada genérico (títulos centrados sobre degradados, fundidos como única entrada, etiquetas en las esquinas, bordes, brillos en la interfaz, partículas genéricas); una tipografía para títulos y otra para la interfaz; un único color de acento; algo nuevo cada 2–4 s.
- **Sonido:** música y SFX sintetizados por código (salvo pista proporcionada), sincronizados con `beats.json` medido, a −14 LUFS.

El texto completo está en [`motion-studio/SKILL.md`](motion-studio/SKILL.md).

## Contenido del repositorio

```
motion-studio/          la skill (SKILL.md, scripts/, assets/plantilla/, references/)
ejemplo/                video de referencia hecho con el flujo
install.ps1 / install.sh
```

## Licencia

[MIT](LICENSE).
