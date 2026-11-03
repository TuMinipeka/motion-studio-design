# Modo edición: videos grabados

Sirve para editar material real: el usuario hablando a cámara, grabaciones de pantalla y tomas de recurso. El agente
controla el montaje con herramientas y mediciones. El usuario aprueba en tres puntos de control.

**Fuente de verdad:** `montaje.json`.
- El agente lo cambia con `montaje.py`, nunca editando el video ni reescribiendo el JSON a mano.
- `editar.py` lo convierte en video con FFmpeg, por segmentos y con caché.
- `qc.py` comprueba lo medible.

Las reglas generales de la skill siguen valiendo: autorizaciones por fase, rúbricas con evidencia y nada de dar por
verificado lo que no se observó.

## Estado

**Disponible (fases 1–3):** perfil del equipo, análisis del material, corte en papel, línea de tiempo, render y control
de calidad.

**Disponibles con limitaciones:**
- **Layouts:** completo, pantalla, y pantalla con la cámara (en una esquina en horizontal, o la pantalla arriba y la
  cámara abajo en vertical).
- **Zoom:** solo el alterno de los jump cuts.
- **Transiciones:** corte y entrada desde negro.

**Pendiente (fases 4–6), sin implementar:**
- zooms animados;
- pantalla dividida y B-roll;
- gráficos de Motion Studio con canal alfa;
- subtítulos;
- música y efectos;
- color;
- curva de retención sobre la línea de tiempo;
- modo autónomo;
- nivel avanzado.

Si el usuario pide algo pendiente, díselo antes de empezar y ofrece lo disponible.

## Flujo

| Etapa | Comando | Salida | Punto de control |
|---|---|---|---|
| 0 Preparación | `python scripts/preparar.py --perfil` (y `--edicion` para el nivel completo) | `~/.motion-studio/estado.json` → `perfil` | — |
| — Proyecto | `python scripts/nuevo.py <carpeta> --edicion [--nombre N] [--fps N] [--vertical]` | carpeta con `fuentes/` y las herramientas | Brief aprobado (como en animación) |
| 1 Análisis | `python analizar.py [--idioma es]` | `analisis/*`, `montaje.json` → `salida`, `fuentes`, `voz` | Confirmar la salida propuesta |
| 2 Planificación | `python planificar.py` | `GUION-MONTAJE.md`, `analisis/guion.json`, clips | **1. El usuario aprueba el corte en papel** |
| 3 Edición | `python montaje.py …` | `montaje.json` (con versiones) | — |
| 4 Render | `python editar.py` (revisión) / `python editar.py --final` | `exportaciones/` y `review/cortes.json` | **2. Muestra · 3. Primer completo** |
| 5 Evaluación | `python qc.py [--retranscribir] [--determinismo]`, `python ritmo.py`, `python verificar.py` | `review/qc.json` | — |
| 6 Iteración | Notas → operaciones de `montaje.py` → `editar.py` (solo lo cambiado) → `qc.py` | — | Máximo 3 rondas; después, los pendientes al usuario |

**Material:**
- **Cámara:** `fuentes/camara/`. La primera con audio es la voz.
- **Pantalla:** `fuentes/pantalla/` (OBS).
- **Tomas de recurso:** `fuentes/broll/`.
- **Micrófono aparte:** `fuentes/audio/`. Si existe, pasa a ser la voz.
- **Originales:** no se modifican nunca.
- **Vocabulario:** un `vocabulario.txt` en el proyecto con nombres propios y términos técnicos mejora la transcripción.

## 0. Adaptarse al equipo

`preparar.py --perfil` prueba de verdad cada codificador H.264 (NVENC, AMF, QSV, VideoToolbox y x264) y mide la RAM, el
disco y la VRAM. Después decide:

| Decisión | Criterio |
|---|---|
| Codificador de revisión y de las copias normalizadas | El primero por hardware que funcione; si no, `libx264` |
| Segmentos en paralelo | 2 con codificador por hardware; núcleos/4 con x264 |
| Modelo de Whisper y dispositivo | El que esté instalado; en CUDA solo si carga y transcribe de verdad |

**Niveles:**
- **Núcleo:** solo FFmpeg. Cortes por silencios.
- **Completo:** con `preparar.py --edicion`, que instala faster-whisper y el modelo large-v3-turbo (~1,6 GB). Corta por
  palabras, tomas repetidas y muletillas.
- **CUDA para Whisper:** es opcional. `--whisper-gpu` instala las bibliotecas (unos 1,5 GB); pide permiso antes. En CPU,
  large-v3-turbo transcribe unos 33 s de voz en 18–23 s en un Ryzen 7 7445HS.

**Ni la resolución ni los fps ni la duración son fijos.** `analizar.py` propone la salida a partir de la cámara (su
orientación real y sus fps nominales). El usuario la confirma o la cambia en `montaje.json` → `salida`. En el render
final, `salida.codificador`, `crf`, `preset` o `parametros` cambian la codificación; por defecto se usa `libx264`,
`slow` y CRF 18.

## 1. Análisis

`analizar.py` hace siete pasos:
1. **Ingesta.**
2. **Salida propuesta.**
3. **Copias a fps constante.** Las grabaciones de móvil son VFR y desincronizan en videos largos. Se genera un
   fotograma clave por segundo para cortar rápido y exacto.
4. **Sincronía.** Correlación de los ataques del audio con la voz, con resolución de 2 ms y su confianza. Por debajo de
   1,5 de confianza, se revisa a mano.
5. **Transcripción.** Palabra por palabra, con su confianza.
6. **Frases, silencios y tomas.**
7. **Luz por segundo y cambios de escena** en las pantallas.

**Lo que hay que saber de Whisper:**
- **Sus tiempos van adelantados:** el final de una frase llega antes que la última sílaba. Por eso el análisis mueve los
  bordes de cada frase a donde empieza y termina la voz de verdad, medido con la energía. El tiempo original queda en
  `deWhisper`/`aWhisper`.
- **Suele omitir "eh" y "em".** Los tramos con voz que no cubre ninguna palabra quedan en `sinPalabra`: los pegados a
  una palabra son su cola; los sueltos, muletillas probables.
- **Inventa palabras en los silencios** (el "Gracias." final). Una palabra con confianza menor de 0,6 y sin voz debajo
  se marca `sinVoz` y no se usa.
- **Tomas repetidas:** frases cercanas (menos de 45 s) con el mismo arranque (3–4 palabras) o con el texto casi igual.
  - Se elige por un puntaje: 45 % completitud, 25 % confianza, 15 % final completo y 15 % ser la última.
  - Si hay un empate técnico (±0,05), gana la última.
  - El agente revisa la elección en el corte en papel, y el usuario la aprueba.

## 2. Planificación: el corte en papel

`planificar.py` quita:
- las tomas que no ganaron;
- las frases que solo son muletillas;
- las muletillas del principio y del final de cada frase;
- las palabras sin voz;
- las pausas de más de `--pausa`.

**Cómo se arma la línea de tiempo:**
- Cada clip va de la voz real menos 60 ms a la voz real más 120 ms, sin invadir lo que dice la frase vecina.
- Los jump cuts alternan el zoom 1 / `--zoom-salto` (1,12 por defecto) para que el salto no se note.
- No pisa un montaje editado salvo con `--rehacer`.

**Antes de renderizar nada, presenta `GUION-MONTAJE.md` al usuario:**
- **Qué contiene:** el texto, lo tachado con su motivo y una sección "Para revisar" (palabras dudosas y sonidos sueltos).
- **Por qué este momento:** es el punto de control más barato. Corregir aquí cuesta una operación; después, un render.
- **Pregunta sugerida:** «¿Apruebas este corte (tomas, muletillas y silencios quitados) y autorizas la primera versión
  de revisión?».

## 3. Edición: operaciones de `montaje.py`

| Necesidad | Operación |
|---|---|
| Ver la línea de tiempo | `info` (clips con su posición en el video final) · `info --palabras` (índice de cada palabra y si se conserva) |
| Quitar una frase, una muletilla o un chiste | `quitar --palabras 412-419 --motivo "..."` (preferible: usa los tiempos reales) · `quitar --desde T --hasta T` (dentro de un clip; se ajusta a la pausa más cercana) |
| Partir un clip | `cortar --en T` |
| Mostrar la pantalla | `layout --desde T --hasta T pantalla+pip --pantalla pant1` (sincronizada por el desfase medido; `pant1@12.0` para otro momento) · `pantalla` · `completo` |
| Zoom de un clip | `zoom --clip N --escala 1.15 [--foco 0.5,0.35]` |
| Entrada desde negro | `transicion --clip N fundido` |
| Comprobar | `validar` |
| Comparar o volver atrás | `diff [vN]` · `deshacer` |

**Lo que hace cada operación por ti:**
- **Valida** antes de guardar y no guarda un montaje inválido.
- **Guarda** la versión anterior en `versiones/`.
- **Lleva los bordes a fotogramas** y a pausas entre palabras, salvo `--exacto`.
- **No crea clips** de menos de 0,2 s.

**Las notas del usuario se traducen a operaciones.** «En el 3:12 corta antes» o «quita el chiste del minuto 5» se
localizan en `info --palabras` y se aplican con `--palabras`, no a ojo.

## 4. Render

`editar.py` renderiza cada clip como un segmento sin audio. El nombre del segmento es el hash de lo que lo define, así
que cambiar un clip solo rehace ese segmento.

**El audio:**
- La voz se monta con muestras exactas: cada clip dura sus fotogramas entre los fps.
- Hay un microfundido de 12 ms solo donde la voz salta. Un cambio de layout sobre voz continua no lleva fundido.
- Se normaliza a −14 LUFS y −1 dBTP en dos pasadas.

**La imagen:**
- Toda la salida va en `yuv420p`, etiquetada BT.709.
- La revisión usa el lado mayor de 960 px y el codificador por hardware. La final, `salida`.

## 5. Evaluación

| Comprobación (`qc.py`) | Tipo |
|---|---|
| Montaje válido | Bloqueante |
| Ningún corte dentro de una palabra; ningún corte con la voz sonando (energía > umbral + 6 dB en el borde) | Bloqueante |
| Todas las palabras del guion aprobado están; nada de lo quitado vuelve | Bloqueante / aviso |
| Jump cut sin cambio de zoom ni de layout | Aviso |
| Render de la misma duración que el montaje; sin clics en los cortes | Bloqueante |
| Silencios de más de 0,6 s fuera de las pausas declaradas | Aviso |
| `--retranscribir`: WER del render frente al guion (máx. 3 %) | Bloqueante |
| `--determinismo`: un segmento rehecho tiene los mismos fotogramas | Bloqueante |
| `verificar.py` sobre el render final (formato, fotogramas, BT.709, LUFS, pico, negros y congelados) | Bloqueante / aviso |

Después:
1. Mira el render y un fotograma a cada lado de cada corte (instantes en `review/cortes.json` → `clips`), extraídos con FFmpeg.
2. Mide el ritmo con `python ritmo.py exportaciones/<nombre>.mp4`.
3. Puntúa con `references/rubricas.md` §15–19, con evidencia en `REVISION.md`.

`qc.py` no juzga si la toma elegida es la mejor, si un chiste funciona ni si el ritmo engancha: eso sale de ver el video.

## Pruebas del modo

`python tests/edicion/probar.py` (en el repositorio) hace las comprobaciones con material sintético de respuestas
conocidas. Usa voz de Windows o `espeak-ng`, un móvil con fps variable y una pantalla con 1,37 s de desfase.
- **Qué comprueba del pipeline:** la sincronía, las tomas, que cada frase esperada esté entera y que lo descartado no
  esté. También que el render final pasa `qc.py`.
- **Fallos provocados:** un corte dentro de una palabra, una palabra perdida y un clic.
- **Regresión del modo animación.**
