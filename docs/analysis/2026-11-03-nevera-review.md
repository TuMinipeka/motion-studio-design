# Revisión de nevera_redes.mp4: divulgación 3D estilizada

2026-11-03. Este video explica un mecanismo mediante un escenario y personajes 3D low-poly, humor y tipografía retro. Su acabado es **nítido**: la fuente pixelada no implica pixelar todo el render. Se mantiene separado del corto ilustrado dramático de Ojalá No y de piezas de motion graphics sin personajes.

## Evidencia y alcance

- Original: `C:/Users/danie/Downloads/nevera_redes.mp4`, 45,6 s, 1080×1920, 30 fps, 1368 fotogramas, H.264 High/yuv420p, BT.709, AAC estéreo de 48 kHz. SHA-256: `6fcf62323aead124423ee50688e100aef40a54f0d70fb2adf76769bac2534feb`.
- La huella coincide con `productividad/shorts/studio-8bit/videos/09-nevera/motion/exportaciones/nevera_redes.mp4`. Se consultaron brief, storyboard, revisión, eventos, cámara, efectos y rig de ese proyecto. No se acredita qué huella exacta de la skill estaba instalada cuando se produjo.
- Revisión visual: 16 imágenes distribuidas cada 3 s; 16 imágenes del cierre a 8 muestras/s; secuencias del mecanismo a 2 muestras/s, fotogramas de la copia corregida y del MP4 codificado. No equivale a reproducción continua a velocidad normal.
- Decodificación completa del original sin errores reportados. EBU R128: **−14,0 LUFS, LRA 1,1 LU, pico real −1,2 dBFS**. No hubo escucha subjetiva: inteligibilidad, música, efectos y sincronía percibida quedan pendientes. Una LRA pequeña no demuestra una mala mezcla en un Short narrado.
- El original y su proyecto se conservan. La muestra solicitada se realiza en una copia aislada con la RTX 3050 del proyecto, sin servicios de pago ni exportación completa.

## Evaluación del original

Notas editoriales sobre lo observado; no son una aprobación audiovisual completa.

| Aspecto | /10 | Diagnóstico y oportunidad |
| --- | --- | --- |
| Animación y poses | 7 provisional | Hay abanico, jadeo, sorpresa, retirada de mano y celebración. El salto final se genera con `abs(sin(...))`: repite rebotes sin fases explícitas de preparación y amortiguación. Conviene resolver peso y contacto, manteniendo la exageración de este estilo; falta comprobar fluidez en reproducción. |
| Transiciones y variedad de planos | 7 provisional | Frontal, corte del objeto, órbita, compresor y vista trasera aportan variedad real. Al entrar al aire acondicionado, debe primar la orientación interior/exterior sobre otro acercamiento. No se revisaron todos los cortes a velocidad normal. |
| Composición y cámara | 6 provisional | En 33–36,5 s, los extremos nominales de ambos flujos quedan fuera de cuadro y el personaje oculta parte del frío. El primer plano del aparato pierde la relación espacial que explica la voz. |
| Iluminación, profundidad y color | 8 provisional | Luz cálida, sombras y corte de pared separan interior/exterior; colores y contornos sostienen la identidad. Las facetas son deliberadas. No hace falta oscurecer la escena, añadir grano o simular realismo fotográfico. |
| Narrativa y ritmo planificado | 7 provisional | Gancho → mecanismo → calor del motor → solución → remate. Los valores 30/32/33/24 °C parecen resultados concretos, pero no documentan una medición. La frase «no fabrica frío: lo saca» tiene un referente ambiguo. No se midió retención de espectadores. |
| Efectos visuales | 7 provisional | Escáner, partículas y flujos muestran procesos. Su recorrido y sus oclusiones importan más que su cantidad; varios rótulos simultáneos compiten con la demostración. |
| Sonido técnico | 8 | Sonoridad y pico adecuados en la medición; no permite calificar la interpretación o la mezcla artística. |
| Render técnico | 9 | Resolución, fps, color, cantidad de fotogramas y decodificación correctos. No acredita ausencia de cualquier artefacto ni calidad artística 9/10. |
| Movimiento fluido y sincronización percibida | Pendiente | Requieren reproducción y escucha. |

## Diagnóstico de la skill y cambios aplicados

1. **Estilo explícito sin otro formulario.** `references/estilos.md` usa los campos existentes del brief para lenguaje, acabado e identidad. Distingue corto ilustrado, divulgación 3D, motion graphics y pixel art; admite combinaciones. Se enlaza desde la entrada, preproducción, dirección y rúbricas.
2. **Prioridad de explicación espacial.** En divulgación se revisa causa → recorrido → resultado, con sus elementos críticos antes de extender la animación. No se considera listo un plano que pierde un elemento imprescindible. La muestra debe cubrir el mecanismo difícil con su interfaz, no solo personajes o títulos.
3. **Corrección de una instrucción contraproducente.** La dirección decía que el centro «no es una lección con diagramas». Ahora permite que un diagrama muestre el cambio relevante sin añadir actuación innecesaria. Se conservan las reglas existentes de intención, anticipación, contacto y continuidad; el rebote observado indica una aplicación insuficiente de esas reglas, no que faltara otro catálogo de principios.
4. **Control geométrico reutilizable.** `comprobarPuntos3D()` en `kit/camara.js` comprueba puntos del mundo con una cámara Three.js, margen configurable y planos de recorte. Devuelve posición normalizada, `frente` y `dentro`, sin mutar los puntos. Es opcional y se ejecuta al revisar instantes clave, sin una nueva dependencia para proyectos 2D. No detecta oclusión, volumen completo, HUD, comprensión o legibilidad.
5. **Jerarquía y precisión del contenido.** La guía pide revisar subtítulos, rótulos y mecanismo juntos, mantener el significado de los colores y distinguir valores ilustrativos de mediciones. Son decisiones por plano, sin imponer nuevos efectos, fps o aprobaciones.

## Prueba antes/después

Intervalo **33–36,5 s**, 3,5 s, **105 fotogramas a 1080×1920/30 fps**. Misma mezcla y duración, render nítido, supersampling del proyecto y CRF 12/preset slow. Se usa el renderizador de la skill; no se reproduce el límite de bitrate personalizado de la exportación de origen.

| Antes | Después |
| --- | --- |
| Cámara cercana en avance; extremos del frío y calor fuera del cuadro. | Cámara más abierta y estable; recorridos esquemáticos más cortos, conservando los sentidos hacia dentro y hacia fuera. |
| Niño y perro en primer término ocultan parte de la explicación. | Se retiran de este plano explicativo; se conserva su regreso en el cierre. |
| Termómetro y titular compiten con el aparato. | Rótulos emparejados «DENTRO / FRÍO» y «FUERA / CALOR»; subtítulos conservados. |

En los cinco instantes comprobados (33; 34,2; 34,5; 35,5; 36,4666 s), pasan de **2/4 a 4/4 puntos críticos dentro del margen del 5 %**. A 34,5 s, los extremos nominales originales están en x = −0,767 y 1,484; los corregidos, en x = 0,120 y 0,925 (pantalla: 0–1). Los recorridos se acortaron: no es una comparación de la misma geometría ni un efecto atribuible solo a cámara. No se comprobó todo el volumen de cada partícula. La inspección de imágenes confirma que el personaje deja de tapar el flujo; eso no lo decide el auxiliar.

**Claridad visual del plano: 6 → 8/10 provisional.** Mejora la relación interior/exterior. Sigue habiendo espacio vacío y el aparato queda menor; no se acredita 9/10 global ni mejora de fluidez, actuación o sonido. No hay benchmark controlado de rendimiento; conservar fps y resolución evita un aumento global, pero no demuestra igualdad de coste.

Artefactos externos a Git: `C:/Users/danie/Documents/skill-review-nevera/`, con `antes.mp4`, `despues.mp4`, `comparacion.mp4` (antes izquierda/después derecha), `comparacion.jpg`, `encuadres.json` y el proyecto aislado. Actualizar la skill no modifica automáticamente proyectos existentes.

## Validación y límites

- Pruebas con cámaras Three.js de perspectiva y ortográfica: márgenes en ambos ejes, detrás de cámara, planos near/far, entradas inválidas y puntos sin mutar. Ejecutadas con el módulo Three.js instalado en `productividad`, sin instalar otro.
- Determinismo exacto de la muestra en cuatro instantes, repetidos y en orden inverso.
- FFprobe y decodificación del después: 105 fotogramas H.264/yuv420p, 1080×1920/30 fps, video y audio AAC estéreo de 48 kHz desde cero, ambos de 3,5 s. La muestra del renderizador genérico no lleva etiquetas de color; no se presenta como un final que haya pasado todas las comprobaciones de exportación.
- Audio antes/después: correlación interior de aproximadamente 0,9985 al decodificar mono a 48 kHz. Acredita conservación/alineación de señal, no sincronía artística ni mejora sonora.
- Validador de la skill, sintaxis JavaScript, auditoría de plantilla, enlaces locales y `git diff --check`. La prueba anterior de encuadre 2D también se conserva y pasa.
- Pendientes: escucha y reproducción continua, anticipación/amortiguación del salto, revisión de enlaces con planos vecinos, precisión del guion y valores ilustrativos. La muestra no vuelve a producir todo el episodio ni verifica otros sistemas/GPU.

## Feedback específico para el video

1. Cambiar la frase a **«No fabrica frío: saca calor»** o «Tu nevera mueve el calor». El aparato transfiere calor y consume trabajo; no extrae una sustancia llamada frío. La relación física es calor expulsado = calor extraído + trabajo. [OpenStax, aplicaciones de la termodinámica](https://openstax.org/books/college-physics-2e/pages/15-5-applications-of-thermodynamics-heat-pumps-and-refrigerators).
2. Presentar los números de temperatura como ilustrativos o sustituirlos por «más calor / más fresco» si no hay datos. La prueba visual retira el termómetro del plano del aire, pero no reescribe los otros planos ni la voz.
3. Mantener a los personajes cuando reaccionan; durante una explicación compleja, dar prioridad al objeto y recuperar su reacción en el siguiente plano.
4. Preparar el salto con una compresión breve y resolver la caída con amortiguación. Evitar que el logro cruce los ojos; en el muestreo del cierre invade el rostro. Esto sigue pendiente en el video.
5. En sonido, revisar con escucha los acentos en escáner, compresor, aparición del calor exterior y aterrizaje. No añadir golpes constantes ni recomprimir la mezcla por su LRA.

Apoyo técnico del auxiliar: [Three.js, Vector3.project](https://threejs.org/docs/pages/Vector3.html#project), consultado el 2026-11-03. Proyectar puntos no es una prueba de visibilidad por oclusión.
