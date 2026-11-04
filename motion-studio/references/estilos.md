# Mantener el estilo de cada proyecto

Consulta esta guía al elegir el lenguaje visual o revisar una pieza distinta de las anteriores. El motor y los controles técnicos son comunes; personajes, voces, paleta, acabado y montaje pertenecen al proyecto. No los heredes de otro canal por haber usado la misma skill.

En los campos existentes de `BRIEF.md` («Lenguaje audiovisual» y «Dirección visual»), concreta lenguaje, acabado y rasgos que deben conservarse. Por ejemplo: «Divulgación 3D low-poly, render nítido, tipografía retro, humor con niño y perro; explicar mecanismos mediante cortes del objeto». Eso no significa pixelar la imagen ni aplicar la luz de un corto dramático. Reutiliza decisiones aprobadas, sin otro cuestionario o documento obligatorio.

| Lenguaje | Qué se dirige y revisa principalmente |
| --- | --- |
| Corto narrativo ilustrado | Actuación, emoción, continuidad de acciones y luz; las pausas y el vacío pueden sostener el relato. |
| Divulgación 3D estilizada | Causa → mecanismo → resultado. Encuadres, cortes del objeto y recorridos permiten entender relaciones espaciales. Personajes y efectos acompañan la explicación. |
| Motion graphics | Jerarquía, transformaciones, relaciones entre formas/datos y lectura. No exige personajes, profundidad real ni iluminación volumétrica. |
| Pixel art o acabado retro | El tamaño del píxel, filtrado y cadencia acordados son decisiones visuales. Una tipografía retro sobre 3D nítido no convierte toda la pieza en pixel art. |

Son criterios de selección, no cuatro estéticas obligatorias. Un proyecto puede combinarlos si el brief explica cómo.

## Cuando el video explica un mecanismo en 3D

En la ficha del plano, identifica los elementos imprescindibles para entender la causa y el resultado. Antes de extender la animación, revisa el inicio, el momento explicado por la voz y el final del movimiento de cámara:

- **Recorrido completo:** se entiende de dónde sale, por dónde pasa y adónde llega el flujo. El color mantiene significado entre planos. Si el recorrido completo no cabe en vertical, abre el encuadre, acorta gráficamente un tramo sin cambiar su dirección o divide la explicación en planos conectados.
- **Visibilidad:** comprueba bordes, cercanía de cámara y oclusiones. Un personaje no debe tapar el mecanismo al que alude la voz. El auxiliar `comprobarPuntos3D()` del kit detecta puntos críticos fuera de cuadro; no detecta objetos que los ocultan. La imagen sigue necesitando revisión.
- **Jerarquía de interfaz:** elige el dato o rótulo que ayuda a ese momento. Evita presentar simultáneamente un titular, un indicador y un logro que compitan con el mecanismo y los subtítulos. Revisa texto y demostración juntos, a tamaño de entrega.
- **Evidencia:** separa una magnitud medida de un valor ilustrativo. Un termómetro animado no acredita un experimento ni una temperatura universal; señala su carácter ilustrativo cuando pueda confundirse.

No marques el plano como listo si un elemento imprescindible queda oculto o fuera de cuadro y rompe la explicación. Resuélvelo en esa ficha y muestra, sin añadir otra aprobación rutinaria.

La muestra debe incluir el mecanismo difícil y su interfaz, no solo la reacción del personaje. Conserva los fps, acabado y recursos aprobados. No añadas partículas, desenfoque o resolución extra para disimular un problema de explicación.

## Evidencia por estilo

Registra en `REVISION.md` el estilo evaluado y el criterio aplicado. Compara con el mismo proyecto y referencia; no penalices un plano narrativo quieto por no tener el ritmo de un Short educativo, ni conviertas este último en un corto oscuro para parecer cinematográfico. Puntúa solo lo observado; geometría correcta y determinismo no demuestran fluidez, comprensión o retención.
