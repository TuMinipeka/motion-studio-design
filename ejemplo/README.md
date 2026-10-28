# Ejemplo: video hecho con el flujo

`XEON_motion_ejemplo.mp4` es el video promocional de XEON (asistente comercial por WhatsApp para ferreterías), de 3 minutos, hecho con este flujo: cada fotograma es una función de `t`, y el audio está sintetizado por código y sincronizado con una cuadrícula de pulsos medida.

Es una **copia ligera de la revisión v2** (1080p, 30 fps, H.264, CRF 25) para que el repositorio pese poco. Procede del archivo `xeon-reviewv2.mp4` proporcionado por el autor, de 3 minutos a 1080p60. El audio AAC se conserva sin recodificar.

## Vista previa del README

[`../docs/assets/xeon-preview.gif`](../docs/assets/xeon-preview.gif) es un resumen animado de esa misma revisión: **16 segundos, 800 × 450, 10 fps, aproximadamente 4 MB**, sin audio y en bucle. Usa fotogramas del resultado real y conserva la velocidad original de cada fragmento.

| Tiempo en la fuente | Fragmento |
| --- | --- |
| 00:30–00:33 | Identidad visual y entrada de escena. |
| 00:46–00:49 | Conversación y pedido en curso. |
| 01:06–01:09 | Consulta de existencias por sede. |
| 01:46–01:49 | Cálculo y presentación de la cotización. |
| 02:49–02:53 | Cierre de marca. |

La previsualización se inserta como una imagen Markdown que enlaza al MP4. GitHub admite [imágenes GIF](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files); la reproducción de animaciones respeta las [preferencias de accesibilidad del visitante](https://docs.github.com/en/account-and-profile/how-tos/account-settings/managing-accessibility-settings). También se incluye una [vista estática](../docs/assets/xeon-preview.jpg).

Lo que ves es el resultado esperado de seguir la skill, no una plantilla: el proyecto de XEON es específico de ese producto.
