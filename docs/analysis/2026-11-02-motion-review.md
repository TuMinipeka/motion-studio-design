# Revisión del resultado de Antigravity y ajuste de Motion Studio

Fecha: 2 de noviembre de 2026. Se analizó el archivo `3065bd4e-3834-4410-8d62-2291d1e706f6.mp4`, proporcionado por el usuario: 30 s, 1920 × 1080, 60 fps, H.264 y audio AAC. No se dispuso del código de ese proyecto, del prompt completo ni del registro del agente; las causas de implementación son hipótesis, no fallos atribuibles con certeza al modelo.

## Observaciones del resultado

Se examinaron muestras distribuidas cada dos segundos, una comprobación de baja variación temporal con FFmpeg y los recursos de la skill que podían orientar el resultado.

| Intervalo aproximado | Evidencia visual | Riesgo de realización |
| --- | --- | --- |
| 0–4 s | Titular grande a la izquierda y personaje enmarcado a la derecha; aparecen contador y etiqueta. | La escena se organiza como una lámina informativa; el sujeto ocupa una parte pequeña del plano. |
| 5–8 s | Diagrama de cajas con un punto o estado destacado. | El cambio ocurre en un detalle, mientras la composición permanece casi completa y estable. |
| 8–12 s | Titular sobre un gráfico con pequeños cambios. | La información verbal y el panel dominan la acción. |
| 12–16 s | Comparación en dos columnas con personajes y textos. | La comparación funciona como diapositiva, en lugar de desarrollar la decisión en una secuencia actuada. |
| 18–24 s | Línea, gráfico de barras y contador de días. | Existe progresión, pero se repite el tratamiento de panel explicativo. |
| 26–30 s | Dos tarjetas y cierre tipográfico. | Se vuelve al patrón de sustitución de bloques completos. |

El detector `freezedetect` con umbral −45 dB y duración mínima de 0,8 s señaló intervalos de poca variación global, incluido aproximadamente 7,75–11,7 s. Esta herramienta puede pasar por alto objetos pequeños que sí se mueven; no demuestra ausencia de animación ni decide la calidad artística. Los 60 fps tampoco prueban que la puesta en escena tenga suficiente desarrollo. No se realizó una evaluación subjetiva de la mezcla sonora.

## Contraste con la referencia aportada

El usuario indicó [Day One Films](https://www.youtube.com/@dayonefilmsofficial). Se abrió la pieza [Motivation Will Fail You.](https://www.youtube.com/watch?v=pirPtQL1S88) en YouTube y se inspeccionaron muestras visibles alrededor de 00:41 y 02:38. En ellas, un personaje ocupa el plano, cambia de pose y aparece dentro de un entorno urbano ilustrado; el estado de los días se integra a la escena. La muestra permite identificar un lenguaje narrativo con personajes y escenarios. No constituye un análisis exhaustivo del canal ni de todas sus transiciones, audio o técnicas de producción.

El resultado recibido se acerca a una infografía editorial. Reutilizar el tema de disciplina, un personaje simple y una paleta oscura no conserva por sí solo el lenguaje audiovisual de la referencia. La diferencia observada no justifica imponer 3D a todos los encargos.

## Factores de la skill y correcciones

| Factor verificado | Cambio realizado |
| --- | --- |
| El contrato técnico y el brief no exigían distinguir una infografía de un corto actuado. | Se añade selección del lenguaje, análisis temporal de la referencia y acciones con estado inicial/consecuencia. |
| La plantilla inicial animaba barras independientes por segmentos. | Se sustituye por una demostración técnica de un sujeto que se desplaza, despliega conexiones y cambia de forma. No se prescribe esa estética para los videos finales. |
| Predominaba la evaluación de imágenes fijas, con fluidez pendiente hasta el borrador completo. | Se exige una muestra animada corta antes de multiplicar escenas, con alcance autorizado. |
| La lista de efectos prohibidos era más concreta que las instrucciones de puesta en escena. | Se centra la restricción en la repetición de láminas y el relleno visual; los recursos se justifican por su función. |
| Existían copias locales con distintos hashes. | Se pide registrar la ruta de la skill en el brief. No se da por probado qué copia cargó Antigravity. |

Se preservan `window.seek(t)`, las herramientas de auditoría, los cuatro pasos y las aprobaciones del usuario. Se añade `--prueba=inicio,fin`: genera hasta 10 segundos de la composición en `review/pruebas/`, sin audio, para revisar movimiento sin exportar toda la pieza. Su ejecución sigue necesitando autorización; el programa no verifica el consentimiento ni identifica automáticamente una presentación.

## Investigación utilizada

- [Figma — Principles in motion](https://www.figma.com/blog/principles-in-motion/): sus diseñadores distinguen diseño estático y diseño temporal, con secuencia, ritmo, transformación y transiciones que conectan una pieza.
- [Ordinary Folk — Process](https://www.ordinaryfolk.co/process): el estudio decide lenguaje visual según la historia y trabaja la expresión de cada objeto, además del guion y el audio.

Las pruebas técnicas de la plantilla verifican captura, intervalos, formato y repetibilidad. No equivalen a una evaluación independiente de cómo Gemini/Argon seguirá las instrucciones actualizadas ni garantizan un resultado equivalente al canal de referencia.
