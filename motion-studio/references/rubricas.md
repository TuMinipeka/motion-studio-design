# Rúbricas de calidad por funcionalidad

Úsalas en el Paso 3 (revisión) y antes de entregar. Cada funcionalidad se puntúa del 1 al 10 **con evidencia**: tiempo o plano, medición o imagen revisada. Si algo no se pudo observar, se marca "pendiente". Si no corresponde al brief, "no aplica". Nunca se rellena con una nota estimada.

## Escala común

| Nota | Significado | Se puede entregar |
|---|---|---|
| 9–10 | Profesional. Ningún defecto visible en reproducción; supera lo pedido. | Sí |
| 7–8 | Sólido. Defectos menores que un espectador casual no nota. | Sí, con los pendientes declarados |
| 5–6 | Funcional. Defectos visibles o audibles, pero el mensaje llega. | Solo como versión de revisión |
| 3–4 | Deficiente. Rompe la lectura, el ritmo o el sonido. | No |
| 1–2 | Roto. No cumple el contrato técnico o el encargo. | No |

**Reglas de aprobación:**
1. **Objetivo:** 8 o más en cada funcionalidad aplicable. Se itera hasta 3 rondas. Si un defecto persiste, se presenta como pendiente: nunca se sube la nota para poder avanzar.
2. **Comprobación bloqueante:** si falla una comprobación marcada **(bloqueante)**, esa funcionalidad no pasa de 4 hasta corregirla.
3. **Nota global:** es la media de las funcionalidades aplicables. No puede superar en más de 1 punto a la peor de ellas: un audio roto no se compensa con buena animación.
4. **Comprobaciones automáticas:** pasarlas demuestra que se cumple el mínimo técnico, no la calidad artística. La nota artística sale de ver y escuchar la reproducción.

## Mapa de comprobaciones automáticas

| Comando | Qué cubre | Código de salida |
|---|---|---|
| `python scripts/preparar.py --comprobar` | Entorno: Python, numpy y Pillow, Node, FFmpeg, Playwright, fuentes, GPU | 1 si falta algo |
| `node auditar.mjs` | Contrato estático: relojes, aleatorios, `fillText` directo, `ctx.reset()` | 1 si hay un ERROR |
| `node render.mjs --determinismo [--t=...]` | Mismo `t`, mismo fotograma, en cualquier orden | 1 si hay diferencias |
| `node render.mjs --ritmo` / `python ritmo.py video.mp4` | Movimiento, tramos muertos, cortes y curva de energía por tramos | 1 si falla. Exige diagnóstico, no fija la nota artística |
| `python audio/musica.py` | −14 LUFS y cuadrícula de pulsos sobre los golpes reales | Avisa en consola |
| `python verificar.py [video.mp4]` | Exportación: códec, píxeles, resolución, fps, duración, sonoridad, true peak, etiquetas de color, fotogramas negros o congelados | 1 si falla una comprobación bloqueante |

---

## 1. Preparación del entorno

| Aspecto | Detalle |
|---|---|
| **Aprobación (10)** | `preparar.py --comprobar` termina con código 0. El renderizador WebGL es la GPU elegida, no SwiftShader. Las fuentes cargan sin descargas. |
| **Medible** | Cada herramienta en OK; `estado.json` actualizado; línea `WebGL:` del render con el nombre esperado. |
| **Errores frecuentes** | Python sin `python` en el PATH (Windows); Playwright instalado pero sin Chromium; FFmpeg sin libx264 o ebur128; portátil con dos GPU que usa la integrada. |
| **Detección** | `preparar.py --comprobar` **(bloqueante)**; aviso de `render.mjs` si `gpu.coincidir` no aparece. |
| **Corrección** | `python scripts/preparar.py` (usuario); `--sistema` con permiso para Node y FFmpeg; `references/gpu.md` para la GPU. No sustituyas una herramienta que falte por otra vía. |
| **Prueba automática** | Sí: `preparar.py --comprobar`. |

## 2. Preproducción: brief, storyboard y curva de energía

| Nota | Criterio |
|---|---|
| 9–10 | Se puede completar la frase "Para [público], este video mostrará [mensaje] mediante [evidencia]…". Cada plano tiene la ficha de `preproduccion.md`: intención, cámara y composición, iluminación, acción, sonido y enlace, con tiempos y papel en la curva. La curva tiene gancho, re-ganchos ligados al contenido, pausas declaradas y clímax. La suma de tiempos cuadra. |
| 7–8 | Todo lo anterior con algún plano poco concreto ("aparece el gráfico"). |
| 5–6 | Guion de texto sin acciones ni cámara, o sin curva. |
| ≤4 | Sin aprobación del usuario, o afirmaciones sin fuente. |

- **Errores frecuentes:** láminas en lugar de acciones; gancho sin re-ganchos; duración que no cabe en el canal; cifras inventadas.
- **Detección:** lista de `preproduccion.md` §3–4; `motion.config.json` → `curva` vacío en piezas de más de 20 s (lo avisa `ritmo.py`).
- **Corrección:** reescribir los planos como estado inicial → acción → consecuencia; añadir re-ganchos cada 8–12 s (menos de 60 s) o cada 15–25 s (piezas más largas).
- **Prueba automática:** parcial. Solo el aviso de curva vacía; lo demás es revisión del agente y aprobación del usuario.

## 3. Animación y movimiento

| Nota | Criterio |
|---|---|
| 9–10 | Anticipación, acción, asentamiento y pose con vida en las acciones principales. Arcos, movimientos escalonados y peso. Ninguna parte se mueve sola con el resto congelado. La muestra `--prueba` resuelve la dificultad principal. |
| 7–8 | Buen timing con algún movimiento lineal o rígido secundario. |
| 5–6 | Interpolación lineal o deslizamientos; personajes que se desplazan sin caminar; brazos sueltos. |
| ≤4 | Láminas con fundidos; elementos que solo aparecen y desaparecen. |

- **Errores frecuentes:**
  - curvas lineales;
  - caminar de frente deslizando;
  - micromovimiento (respiración) como único movimiento;
  - personaje demasiado pequeño en el plano.
- **Detección:**
  - `--ritmo`: micromovimiento y tramos muertos. Un fallo exige diagnóstico con evidencia, pero no fija la nota de animación: un plano quieto puede ser una decisión;
  - revisión de `--prueba` a velocidad normal;
  - hoja de contacto.
- **Corrección:**
  - `claves()` con `saleBack` o `resorte()` en las llegadas;
  - el cuerpo entero participa del gesto;
  - acercar el plano;
  - ver `references/kit.md`, sección "Personajes".
- **Prueba automática:** parcial (`ritmo.py`). La calidad de la actuación es revisión humana o del agente sobre la reproducción.

## 4. Cámara y puesta en escena

| Nota | Criterio |
|---|---|
| 9–10 | El encuadre responde a la acción. La escala o el ángulo cambian cada 2–4 s salvo pausa intencionada. Temblor en los impactos y paralaje con motivo. El sujeto principal ocupa al menos un 25 % del alto en vertical. |
| 7–8 | Buena gramática con algún plano largo sin motivo. |
| 5–6 | Una sola escala; zoom lento como único recurso. |
| ≤4 | Sujeto cortado sin intención o ilegible en un móvil. |

- **Errores frecuentes:** cabeza que sale del cuadro en un salto; el mismo zoom en todos los planos; sujeto diminuto en planos generales largos.
- **Detección:**
  - duración media de plano en `ritmo.py` (aviso);
  - hoja de contacto, comprobando los bordes del cuadro;
  - `--frames` en los picos de acción.
- **Corrección:** `encuadre()` calculado desde el sujeto; seguir la altura del salto; cortar en la acción.
- **Prueba automática:** parcial (cortes por minuto y plano medio).

## 5. Transiciones y montaje (edición)

| Nota | Criterio |
|---|---|
| 9–10 | Cada enlace tiene motivo: continuidad de acción, forma o dirección. Ningún fotograma vacío o a medias en el centro de una transición. Gramática coherente durante toda la pieza. |
| 7–8 | Enlaces correctos con alguna transición intercambiable. |
| 5–6 | Fundido o barrido genérico en todas las escenas. |
| ≤4 | Saltos que rompen la orientación, o fotogramas en negro. |

- **Errores frecuentes:**
  - whip con un fotograma vacío;
  - transición distinta en cada corte para "lucirse";
  - corte antes o después del gesto en vez de en su mitad.
- **Detección:**
  - `--frames` en el centro de cada transición;
  - `verificar.py`, que detecta negros (`blackdetect`) **(bloqueante si no es intencionado)**;
  - `--determinismo` con `--t` en los centros.
- **Corrección:** `crearTransiciones().montaje()` del kit; corte directo cuando no haya un motivo mejor.
- **Prueba automática:** parcial.
- **Alcance:** esta sección es el montaje de **planos generados**. El montaje de grabaciones reales tiene sus propias rúbricas (§15–19, modo edición).

## 6. Motion graphics y tipografía

| Nota | Criterio |
|---|---|
| 9–10 | Un foco por escena. El diagrama u objeto **evoluciona con el mensaje**. Dos tipografías como máximo, un color de acento y jerarquía clara. El texto principal mide al menos 48 px de alto en 1080×1920 (36 px en 1920×1080). |
| 7–8 | Claro, con alguna escena que explica con texto lo que podría mostrar. |
| 5–6 | La receta "titular + panel + etiquetas + fundido" repetida. |
| ≤4 | Párrafos en pantalla; texto ilegible en un móvil. |

- **Errores frecuentes:**
  - diagramas fijos de más de 4 s;
  - láminas de título de más de 1,5 s;
  - fondos vacíos entre secciones;
  - texto con `fillText` directo, que no es determinista.
- **Detección:**
  - `auditar.mjs` para el texto directo **(bloqueante)**;
  - `ritmo.py` para los tramos quietos;
  - hoja de contacto al 50 % de tamaño para la legibilidad.
- **Corrección:** `crearTexto(ctx)`; convertir el diagrama en una acción que lo transforma; ver `references/motion-graphics.md`.
- **Prueba automática:** parcial.

## 7. Texto en pantalla y subtítulos

| Nota | Criterio |
|---|---|
| 9–10 | Frases de 7 palabras o menos por línea y 2 líneas como máximo. En pantalla al menos 1,2 s, o unos 3 caracteres cada 0,1 s. Dentro de la zona segura. Sincronizados con la voz si la hay (±100 ms). |
| 7–8 | Legibles, con algún bloque demasiado largo. |
| 5–6 | Texto rápido o tapado por la interfaz de la plataforma. |
| ≤4 | Ilegible, o fuera de sincronía de forma notoria. |

**Zonas seguras para vertical 1080×1920:** reserva unos 250 px arriba y unos 400 px abajo, y unos 120 px a la derecha, donde van los botones de TikTok y Reels.

- **Errores frecuentes:**
  - texto bajo los botones de la plataforma;
  - tiempos estimados en lugar de medidos sobre la voz;
  - contadores que tiemblan (usa `numero()`).
- **Detección:**
  - hoja de contacto con la zona segura marcada;
  - con voz, comparar el inicio de cada frase con la duración real del audio.
- **Corrección:** mover el texto al tercio central; partir las frases; anclar los tiempos al audio de la voz.
- **Prueba automática:** no hay generador ni verificador de subtítulos. El texto en pantalla se revisa sobre la hoja de contacto. Los subtítulos por palabra a partir de una transcripción están planificados para la edición de video real.

## 8. Audio: música, efectos y voz

| Nota | Criterio |
|---|---|
| 9–10 | −14 LUFS ±1 integrado; true peak ≤ −1 dBTP. La densidad de golpes sigue la curva de energía. El estéreo se abre en los momentos clave. La voz es inteligible, con la música al menos 8 dB por debajo mientras se habla. |
| 7–8 | Nivel correcto con algún tramo plano o un pico alto. |
| 5–6 | Música continua sin relación con la imagen; estéreo estrecho y estático. |
| ≤4 | Saturación, silencios no intencionados o voz tapada. |

- **Errores frecuentes:**
  - pico por encima de −1 dBTP;
  - densidad sonora que cae tras el gancho;
  - mezcla mono;
  - golpes desplazados respecto al pulso.
- **Detección:**
  - `verificar.py` (sonoridad **bloqueante**; true peak como aviso);
  - avisos de sonido de `ritmo.py` por tramo;
  - verificación de pulsos de `musica.py`.
- **Corrección:**
  - ajustar `GOLPES` a la curva;
  - panear los efectos según la posición en pantalla;
  - repetir `musica.py`;
  - con voz, `--voz` para el ducking.
- **Prueba automática:** sí en lo técnico (LUFS, pico, pulsos). La calidad musical necesita escucha humana.

## 9. Sincronización imagen-sonido

| Nota | Criterio |
|---|---|
| 9–10 | Impactos visuales y sonoros dentro de ±1 fotograma, anclados a `beats.json` medido. Un único archivo de eventos para imagen y audio. |
| 7–8 | ±2–3 fotogramas en golpes secundarios. |
| 5–6 | Desfase perceptible en los impactos principales. |
| ≤4 | Imagen y sonido van por separado. |

- **Errores frecuentes:**
  - tiempos escritos a mano en dos sitios;
  - tempo supuesto en lugar de medido (doble o mitad);
  - un `--final` de duración distinta al audio.
- **Detección:**
  - `musica.py`, que comprueba la cuadrícula frente a los golpes;
  - `verificar.py`, que compara la duración del audio con la del video **(bloqueante si difieren más de 0,1 s)**;
  - reproducción del completo.
- **Corrección:** `eventos.json` compartido; `--bpm` aproximado si el tempo sale al doble o a la mitad.
- **Prueba automática:** parcial (cuadrícula y duración). El desfase visual fino se revisa en reproducción.

## 10. Determinismo (contrato de render)

| Nota | Criterio |
|---|---|
| 10 | `auditar.mjs` sin errores; `--determinismo` OK en los 10 instantes por defecto y en al menos uno por escena, más los textos que cambian. |
| 1–4 | Cualquier diferencia o ERROR. |

No hay notas intermedias: o se cumple o no.

- **Errores frecuentes:** estado del contexto 2D arrastrado entre fotogramas; caché de glifos (Δ1–2 en bordes de texto); acumuladores; `Math.random`.
- **Detección:** `auditar.mjs` **(bloqueante)**; `--determinismo` **(bloqueante)**, que guarda las diferencias en `review/determinismo/`.
- **Corrección:** `ctx.reset()` al empezar `render(t)`; `crearTexto`; ruido con semilla; abrir las dos imágenes antes de cambiar el código.
- **Prueba automática:** sí.

## 11. Ritmo y retención

| Nota | Criterio |
|---|---|
| 9–10 | `ritmo.py` pasa con umbrales calibrados con referencias. Ningún tramo cae por debajo de la mitad de la apertura fuera de las pausas declaradas. Todos los re-ganchos planificados se ven. El final está a la altura del gancho. |
| 7–8 | Pasa con los umbrales por defecto, con algún aviso justificado. |
| 5–6 | Pasa en global pero con tramos flojos (avisos sin explicación). |
| ≤4 | Falla, y la reproducción confirma tramos muertos o una caída de energía que no se decidió. |

- **Errores frecuentes:**
  - energía solo en el gancho;
  - lecciones con diagramas fijos;
  - efectos de relleno (grano, zoom lento, cámara en deriva continua) para "pasar" la medición.
- **Detección:** `render.mjs --ritmo` y `ritmo.py` sobre el completo.
  - **Un fallo obliga a diagnosticar:** ver los tramos señalados en reproducción y anotar en `REVISION.md` si son un defecto o una decisión.
  - **Si es una decisión** (una pausa de lectura, un silencio), se declara en `curva.pausas` con su motivo.
  - **La métrica no fija la nota sola:** pasarla no demuestra un buen ritmo, y fallarla por un plano quieto deliberado no lo hace malo.
- **Corrección:** volver al storyboard; re-gancho ligado al contenido; reutilizar los recursos de la apertura en el clímax. Nunca rellenar con efectos.
- **Prueba automática:** sí.

## 12. Renderizado

| Nota | Criterio |
|---|---|
| 9–10 | En la GPU elegida. Segmentos reanudables. Ningún fotograma duplicado ni ausente. Muestra `--prueba` con el mismo perfil que el final. |
| 7–8 | Correcto pero lento por una configuración mejorable (workers, GPU). |
| 5–6 | Por CPU (SwiftShader) sin haberlo decidido. |
| ≤4 | Falla o produce fotogramas corruptos. |

- **Errores frecuentes:**
  - SwiftShader por la GPU integrada;
  - falta de memoria de video con demasiados workers;
  - render interrumpido que vuelve a empezar de cero.
- **Detección:**
  - línea `WebGL:` y aviso de `gpu.coincidir`;
  - `verificar.py`, que compara el número de fotogramas con el esperado **(bloqueante)**.
- **Corrección:** `references/gpu.md`; bajar `workers`; volver a lanzar, porque solo rehace los segmentos que faltan.
- **Prueba automática:** sí (GPU y número de fotogramas).

## 13. Exportación y entrega

| Nota | Criterio |
|---|---|
| 10 | Todo lo siguiente se cumple, y además: el formato y la duración encajan con el canal, y hay etiquetas de color BT.709 y true peak ≤ −1 dBTP. |
| 7–8 | Pasan las comprobaciones bloqueantes; avisos de etiquetas de color o de pico. |
| ≤4 | Falla una comprobación bloqueante. |

Comprobaciones bloqueantes:
- H.264 en `yuv420p`;
- resolución, fps y duración iguales a `motion.config.json`;
- fps constante;
- audio presente y a −14 ±1 LUFS si existe `audio/final.wav`;
- sin fotogramas negros ni congelados que no se hayan declarado.

- **Errores frecuentes:**
  - color sin etiquetar (los reproductores pueden interpretarlo como BT.601 y cambiar el tono);
  - pico por encima de −1 dBTP;
  - 16:9 entregado a Shorts o Reels.
- **Detección:** `python verificar.py` **(bloqueante)**.
- **Corrección:** ajustar `motion.config.json` al canal; repetir la mezcla con margen de pico.
- **Prueba automática:** sí.
- **Límite conocido:** `render.mjs` todavía no escribe etiquetas BT.709 ni limita el pico. `verificar.py` lo avisa sin bloquear. Corregirlo es la mejora "perfil de publicación", pendiente de aprobación.

## 14. Revisión e iteración (proceso)

| Nota | Criterio |
|---|---|
| 9–10 | `REVISION.md` registra, en cada ronda, la evidencia (tiempo o plano, problema y corrección) y la nota por funcionalidad. Las notas no suben sin una corrección que lo justifique. Los pendientes se declaran. Como máximo 3 rondas antes de consultar. |
| 5–6 | Notas sin evidencia, o una autoevaluación optimista sin reproducción. |
| ≤4 | Se entrega sin revisar, o se afirma haber verificado algo que no se observó. |

**Procedimiento de cada ronda:**
1. Ejecutar las comprobaciones automáticas aplicables (tabla de arriba).
2. Revisar la hoja de contacto y la reproducción.
3. Puntuar cada funcionalidad con su evidencia.
4. Corregir los 3 problemas más graves.
5. Volver a medir solo lo afectado.
6. Registrar todo en `REVISION.md`.

**Error frecuente:** inflar la propia nota. Contraste: una funcionalidad con una comprobación bloqueante fallida no puede pasar de 4, y la nota global queda limitada por la peor funcionalidad.

---

# Modo edición (videos grabados)

Las mismas reglas de escala, aprobación y evidencia. Las comprobaciones son de `qc.py` (ver `references/edicion.md` §5).

## 15. Análisis del material

| Nota | Criterio |
|---|---|
| 9–10 | Todas las fuentes normalizadas a fps constante. Sincronía con confianza ≥ 1,5 y error ≤ 1 fotograma. Transcripción con confianza media ≥ 0,85. Tomas repetidas agrupadas como las agruparía una persona. |
| 7–8 | Algún término técnico mal transcrito, corregible con `vocabulario.txt`. |
| 5–6 | Sincronía de confianza baja sin revisar, o tomas sin agrupar. |
| ≤4 | Una fuente sin procesar, un desfase sin detectar, o fps variable sin convertir. |

- **Errores frecuentes:** móvil en VFR; rotación ignorada; audio de OBS sin micrófono, que no se puede sincronizar.
- **Detección:** la salida de `analizar.py` (VFR, desfase y confianza); `analisis/frases.json` → `tomas`.
- **Corrección:** grabar en OBS también el micrófono; `vocabulario.txt`; `--forzar` tras cambiar las fuentes.
- **Prueba automática:** parcial. La sincronía y las tomas se validan con material sintético (`tests/edicion/probar.py`).

## 16. Corte en papel y planificación

| Nota | Criterio |
|---|---|
| 9–10 | Conserva todas las ideas, elige la mejor toma de cada grupo y quita muletillas y silencios sin dejar frases cojas. Los motivos de cada quitado son legibles. El usuario lo aprueba sin cambios de fondo. |
| 7–8 | Una o dos tomas discutibles que el usuario corrige en la revisión. |
| 5–6 | Se pierde una idea o queda una toma fallida. |
| ≤4 | Se presenta sin revisar, o se renderiza sin aprobación. |

- **Errores frecuentes:**
  - elegir la toma más larga cuando la buena es la más corta;
  - cortar el remate de un chiste;
  - muletillas a mitad de frase, que no se pueden quitar sin un corte.
- **Detección:** la sección "Para revisar" de `GUION-MONTAJE.md`; la lectura del agente antes de presentarlo.
- **Corrección:** `montaje.py quitar --palabras` y `deshacer`; `planificar.py --rehacer --pausa N`.
- **Prueba automática:** no juzga la elección. Comprueba que lo aprobado llega al render (§17).

## 17. Cortes y línea de tiempo

| Nota | Criterio |
|---|---|
| 9–10 | Cortes invisibles: ninguno dentro de una palabra ni con la voz sonando, sin clics, sin silencios de más de 0,6 s sin motivo. Los jump cuts cambian de zoom o de layout. |
| 7–8 | Algún jump cut sin cambio que pasa desapercibido. |
| 5–6 | Una respiración cortada o un salto visible. |
| ≤4 | Palabras cortadas o perdidas, o clics audibles. |

- **Detección:** `qc.py` **(bloqueante)**: dentro de palabra, voz sonando, palabras perdidas y clics. Aviso: jump cuts y silencios.
- **Corrección:** `montaje.py quitar --palabras` (corta entre palabras); `zoom`/`layout` en el jump cut.
- **Prueba automática:** sí, incluidos los fallos provocados de `probar.py`.

## 18. Composición y layouts

| Nota | Criterio |
|---|---|
| 9–10 | Cada frase con el layout que la sirve. La pantalla está sincronizada con lo que se dice. La cámara nunca tapa información. El encuadre del zoom conserva la cara. |
| 7–8 | Algún layout que dura más de lo que aporta. |
| 5–6 | Pantalla desincronizada o ilegible en un móvil. |
| ≤4 | Fuente equivocada o negro. |

- **Detección:** fotogramas a cada lado de los cortes (`review/cortes.json`); `verificar.py` (negros); `qc.py --determinismo`.
- **Corrección:** `layout` con `--pantalla fuente` (sincronizada) o `fuente@segundo`; `zoom --foco`.
- **Prueba automática:** parcial. Determinismo y negros; la pertinencia del layout se juzga mirando.

## 19. Audio del montaje

| Nota | Criterio |
|---|---|
| 9–10 | −14 ±1 LUFS, ≤ −1 dBTP, nivel de voz uniforme entre tomas, sin ruidos en los cortes. |
| 7–8 | Una toma algo más baja o con más ruido de fondo. |
| ≤4 | Clics, saltos de nivel o voz cortada. |

- **Detección:** `qc.py` (clics) y `verificar.py` (LUFS y pico) **(bloqueante)**; `analisis/frases.json` → `nivelDb` por frase.
- **Prueba automática:** sí en lo técnico. La limpieza de ruido, la música y la mezcla están pendientes (fase 4).
