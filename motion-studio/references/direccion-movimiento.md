# Dirigir movimiento, no una sucesión de láminas

Lee esta guía cuando el encargo incluya una referencia audiovisual o cuando la primera propuesta se parezca a una presentación. Los criterios siguientes son pautas de dirección de Motion Studio, no una fórmula que garantice calidad.

## 1. Analizar lo que la referencia hace en el tiempo

Un canal, una miniatura o una transcripción no bastan para evaluar animación. Selecciona uno o dos videos representativos y observa fragmentos reproducidos, no solo fotogramas. Registra URL, tiempos observados y qué pudiste comprobar. Si solo puedes ver imágenes, declara esa limitación y pide un fragmento cuando la dinámica sea decisiva. No presentes inferencias como una comparación visual verificada.

En `BRIEF.md`, descompón la referencia en:

| Dimensión | Qué observar y trasladar al encargo |
| --- | --- |
| Lenguaje | Tipografía cinética, infografía, interfaz, personaje actuando o combinación. |
| Acción | Qué hace el sujeto, qué cambia y qué consecuencia se ve. |
| Espacio | Encuadre, escala, profundidad, entorno y cambios de plano. |
| Tiempo | Aceleración, pausas, preparación, acción y asentamiento. |
| Enlace | Qué persiste entre planos o cómo un corte conecta las acciones. |
| Texto y sonido | Qué cuenta la imagen, qué dice el texto o la voz y cuándo intervienen. |

Concreta qué se conservará y qué se adaptará. No reduzcas una referencia a «fondo negro + color de acento + muñeco». No copies sus guiones, personajes o activos; identifica recursos de realización para una pieza original.

Si la referencia es un corto con personajes, no la conviertas silenciosamente en una infografía. Decide si el resultado necesita actuación y escenarios. Si faltan recursos o capacidad para ello, ofrece un alcance viable y pide al usuario elegir antes de sustituir el lenguaje visual.

## 2. Escribir acciones que se puedan animar

El storyboard debe describir un estado inicial, una acción y un estado resultante, además del texto. Separa una **escena** narrativa de los **planos** que la muestran. No todo párrafo necesita una pantalla nueva.

Ejemplo para una pieza sobre posponer tareas:

- Insuficiente: «Título: mañana empiezo; muñeco junto a un reloj; fundido a un diagrama».
- Propuesta de actuación: «El personaje alcanza el móvil, retira la mano del cuaderno y vuelve a hundirse en la silla. En el siguiente plano, el mismo gesto se repite mientras cambia la luz exterior. Finalmente aparta el móvil y abre el cuaderno; su acción cambia el encuadre hacia la tarea».

La segunda propuesta sigue siendo 2D, pero el mensaje depende de acciones y consecuencias. Si el encargo es una infografía, un diagrama también puede hacerlo: una decisión recorre la red y transforma su estructura, en vez de permanecer como un cuadro completo con un punto decorativo.

Para las acciones principales fija entrada/preparación, desarrollo, consecuencia y pausa. Usa anticipación, variaciones de velocidad, poses y movimiento secundario cuando aporten intención. No añadas rebotes o parallax para cumplir una cuota.

### Cámara y puesta en escena

Elige el encuadre según lo que debe verse: un plano amplio puede establecer relaciones; un detalle puede hacer legible un gesto o revelar una pista. Decide cuándo acercarte, seguir al sujeto o revelar el espacio, y cuándo conviene una cámara fija. Describe origen, destino, duración y foco en el storyboard. No apliques el mismo zoom a todos los planos.

Un movimiento de cámara debe conservar orientación y tener una intención: acompañar una acción, mostrar escala, dirigir atención o cambiar la información disponible. En 2D puedes usar encuadre, recorte y capas cuando corresponda; usa profundidad real si la realización y la referencia lo requieren. Elige la técnica que produzca el efecto acordado con recursos viables.

En un plano oscuro, decide qué detalle tiene que leerse y revisa ese foco a tamaño de entrega. Conserva el ambiente con luz localizada o separación de silueta; subir la exposición de toda la imagen puede destruir la intención. Un general establece el lugar; un corte a reacción puede revelar una emoción que ya se anima pero no se distingue. `encuadreZona()` en el kit ayuda a proteger el área necesaria, sin imponer una cuota de cortes.

### Actuación y poses

Para personajes, concreta intención, silueta y poses de preparación, acción y reacción. Revisa mirada, peso, equilibrio, contacto con el suelo y con objetos; una mano debe alcanzar lo que toca y el entorno debe responder cuando corresponda. La expresión puede verse en postura y ritmo, además del rostro. No resuelvas una actuación cambiando solo la posición de un icono rígido.

Para elementos gráficos, aplica el mismo criterio a sus estados: qué cambia, qué lo provoca y cómo se percibe peso o jerarquía. No añadas caras ni articulaciones por obligación.

### Transiciones, montaje e impacto

Decide qué enlaza los planos: una acción que continúa, una forma que se transforma, una dirección compartida, un contraste deliberado o una relación sonora. Un corte directo puede ser la mejor elección. Evita fundidos y barridos intercambiables que no respondan al contenido.

Construye impacto mediante preparación y contraste: una pausa puede dar fuerza a una acción breve; un plano amplio puede hacer que un detalle posterior importe. Protege la lectura y el recorrido de la mirada. Mantén una gramática consistente con la referencia y el tono, en lugar de demostrar una transición distinta en cada escena.

### Producción y postproducción

En producción, usa la muestra para resolver los problemas difíciles de actuación, cámara y conexión entre planos, y extiende solo el lenguaje validado. Conserva proporciones, materiales, iluminación, dirección de movimientos y escala de elementos equivalentes.

Construye siguiendo la curva de energía del storyboard (`preproduccion.md`, "Curva de energía y re-ganchos"). Los re-ganchos y los clímax de acto se animan con el mismo cuidado que la apertura, no con lo que sobra al final. Si un plano explica, el diagrama u objeto muestra la relación o cambio relevante; la divulgación no necesita añadir actuación de personajes para justificarlo. Aplica `estilos.md` para proteger recorridos y elementos críticos. Al pasar `--ritmo`, revisa la tabla por tramos, no solo la media.

En postproducción, revisa la secuencia completa a velocidad normal: apertura, progresión, pausas y cierre. Comprueba continuidad de poses y espacio, cortes, contacto con objetos, legibilidad y coordinación de imagen/sonido. Registra problemas por plano y tiempo en `REVISION.md`, corrige lo que cambie la experiencia y vuelve a observarlo. Las métricas y pruebas técnicas complementan esa reproducción.

## 3. Detectar la deriva hacia una presentación

Replantea la propuesta si, salvo que el usuario haya pedido una presentación, predominan estas señales:

- Titular y panel completo aparecen, permanecen y son sustituidos por otro bloque con la misma composición.
- La mayor parte de la explicación está en texto o etiquetas; el objeto solo decora.
- Solo se anima opacidad, una línea de progreso, un contador, un punto o un personaje pequeño sobre un panel inmóvil.
- El encuadre no responde a la acción y todas las escenas usan la misma distribución de espacio.
- Se cambia una escena entera para continuar una acción que podría evolucionar dentro del mismo espacio.
- La energía se queda en el gancho: después, láminas de título de más de 1,5 s, diagramas fijos de más de 4 s, fondos vacíos entre secciones o personajes pequeños en planos generales largos.

No corrijas esto con movimiento permanente, zoom automático sobre cada lámina o 3D obligatorio. Las pausas y los planos fijos pueden ser deliberados. El criterio es si la acción, su puesta en escena y el montaje comunican el mensaje acordado.

## 4. Probar la parte difícil antes de multiplicarla

Tras aprobar el brief, solicita un alcance que incluya **una prueba animada corta**, además de imágenes de estilo. Como pauta, elige 3–6 segundos con una acción principal y un enlace entre planos; si el proyecto es más breve, prueba el fragmento representativo disponible.

```bash
node render.mjs --prueba=2,6
```

El modo captura solo ese intervalo en `review/pruebas/`, con la resolución y fps del proyecto y el mismo perfil `codificacion.final` que usará el completo; por defecto, CRF 12 y preset `slow`. Incluye el intervalo de `audio/final.wav` si existe, recortado al primer fotograma capturado, sin renormalizar el volumen del fragmento. `--sin-audio` permite una prueba visual muda. La aprobación debe corresponder al acabado real: no presentes `--ritmo` (vista diagnóstica reducida) como esa muestra. Con mezcla disponible, revisa ya voz, impacto y corte; si falta o no puedes escucharla, deja esa revisión pendiente para el usuario o el completo; el renderizador no verifica aprobaciones humanas ni estilo automáticamente.

Selecciona la dificultad real: si hay actuación y diálogo, la muestra debe incluirlos; una transición vistosa sola no valida al personaje. En piezas largas revisa también un plano de desarrollo al revisar el acto, sin añadir otra aprobación rutinaria. Reproduce la prueba a velocidad normal y comprueba:

1. El cambio principal se entiende sin que las etiquetas tengan que explicarlo todo.
2. Las poses, transformaciones o recorridos muestran una evolución real del sujeto.
3. El enlace entre planos mantiene intención, foco o continuidad.
4. El ritmo y el lenguaje coinciden con las propiedades de referencia realmente observadas.

Muestra la prueba al usuario y usa el aviso breve de [avisos-creativos.md](avisos-creativos.md): «Aprobar y generar el video completo en esta calidad» permite validar la experiencia y autorizar la exportación completa en calidad alta a la vez. Al aceptarlo, continúa con `--final` sin imponer un borrador reducido. Si necesita ajustes, corrige la muestra antes de multiplicar escenas. Si tu entorno no reproduce video, pide esa revisión al usuario y deja el criterio pendiente; no te asignes una nota de fluidez por una hoja de contacto.

## Fuentes

Consultadas el 2 de noviembre de 2026:

- [Figma — Principles in motion](https://www.figma.com/blog/principles-in-motion/): sus diseñadores explican el uso de secuencia, ritmo, transformaciones, anticipación, pausas y enlaces entre planos. Se adapta su criterio de dirección; no sus ejemplos como plantilla universal.
- [Ordinary Folk — Process](https://www.ordinaryfolk.co/process): el estudio distingue mensaje, lenguaje visual, animación de objetos y sonido. La elección de 2D, 3D u otros recursos responde a la historia.
