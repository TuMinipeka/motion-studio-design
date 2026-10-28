# GPU en Motion Studio

`render.mjs` abre Chrome sin interfaz (Playwright) y le pide dibujar cada fotograma. Qué GPU lo hace se decide en `motion.config.json`:

```json
"gpu": { "modo": "alto-rendimiento", "angle": "d3d11", "coincidir": "NVIDIA", "nombre": "NVIDIA GeForce RTX 3050" }
```

| Campo | Qué hace |
|---|---|
| `modo` | `alto-rendimiento` pide la GPU dedicada (`--force_high_performance_gpu`); `bajo-consumo` pide la integrada (`--force_low_power_gpu`); `auto` deja elegir a Chrome; `cpu` usa SwiftShader (respaldo, mucho más lento). |
| `angle` | Backend gráfico de Chrome. En Windows, `d3d11` (probado). En otros sistemas Chrome usa `metal` (macOS) o `vulkan`/`gl` (Linux): **no probados** en esta skill. |
| `coincidir` | Texto (regex, sin distinguir mayúsculas) que debe aparecer en el renderizador WebGL, p. ej. `NVIDIA`, `Radeon`, `Arc`. Si no aparece, `render.mjs` avisa. Vacío = no comprobar. |
| `nombre` | Solo informativo. |

Se puede cambiar por ejecución: `node render.mjs --final --gpu=cpu`.

## Cómo comprobar qué GPU se usó

Al arrancar, `render.mjs` imprime una línea como:

```
WebGL: ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 6GB Laptop GPU ... Direct3D11 ...)  (modo alto-rendimiento)
```

Si dice `SwiftShader`, se está renderizando por CPU.

## Qué GPU hay en el equipo

`python scripts/nuevo.py --listar-gpus` (Windows). También: Administrador de tareas → Rendimiento, o `Get-CimInstance Win32_VideoController | Select Name`.

## Problemas frecuentes

- **Avisa de otra GPU o de SwiftShader.** Cierra otros programas que usen la GPU, actualiza el controlador y confirma que Chrome/Chromium tiene permiso de "alto rendimiento" en Configuración de Windows → Sistema → Pantalla → Gráficos. Prueba `--gpu=auto`.
- **Portátil con dos GPU.** Sin `--force_high_performance_gpu` Chrome suele elegir la integrada; con él, la dedicada. Es la razón del valor por defecto.
- **Se queda sin memoria de vídeo.** Baja `workers` (cada uno abre su propio navegador y proceso de GPU). El valor por defecto es 6; con una GPU de 6 GB funcionó bien.
