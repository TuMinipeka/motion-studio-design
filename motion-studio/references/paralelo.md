# Trabajo paralelo con Claude Code

Aplica esta guía cuando se soliciten subagentes o haya trabajo independiente suficiente. La skill mantiene su flujo: preproducción → muestra autorizada → revisión → completo autorizado y verificación. Delegar no adelanta una aprobación ni autoriza renderizar, generar voz de pago o publicar. Es una instrucción operativa para el coordinador con los subagentes nativos disponibles; no instala otro motor ni un servicio de orquestación.

## Activación y preparación

El agente principal asume la dirección, divide tareas y reúne resultados. Usa las herramientas nativas de delegación de la versión de Claude Code disponible y ejecuciones en segundo plano para tareas independientes. No lances una tarea y esperes su fin antes de asignar las demás si ya pueden avanzar. Si la sesión no expone subagentes, informa de ello y continúa las tareas viables sin fingir concurrencia; no cambies la configuración del usuario para habilitar equipos experimentales.

Antes de la aprobación del brief, los subagentes pueden investigar referencias y proponer guion/realización; no crean el proyecto ni capturan imágenes. Después, registra en `CONTRATO.md` dentro del proyecto lo mínimo necesario para coordinar trabajo. Usa `assets/paralelo/CONTRATO.md` como ficha adaptable, no como una lista de entregables obligatorios. El storyboard y brief siguen siendo las fuentes creativas; el contrato los referencia sin duplicarlos.

Fija antes de construir: versión del brief, alcance autorizado, fps/duración/cadencia, identificadores de planos y recursos, nombres y firmas de las interfaces, sistema de coordenadas, fuentes compartidas y propietario de cada archivo. Los cambios de una interfaz común los resuelve el coordinador y los comunica a sus consumidores antes de continuar.

## Reparto según el proyecto

| Responsable | Encargo y archivos propios posibles | Dependencias |
| --- | --- | --- |
| Coordinador | Brief/storyboard, configuración, `produccion.json`/`sincro.json`, contrato, composición `index.html`, integración y cola de render | Único responsable de archivos compartidos y aprobaciones |
| Aspecto visual | Materiales, iluminación, contornos; p. ej. `escena/look.py` | Interfaces y dirección visual acordadas |
| Personajes | Modelo, poses y expresiones del proyecto; p. ej. `escena/personajes.py` | API de materiales, escala y anclas; puede avanzar con interfaces provisionales acordadas |
| Escenarios | Decorado, objetos y anclas; p. ej. `escena/entorno.py` | API de materiales y coordenadas |
| Planos/actuación | Un grupo de planos o gag, p. ej. `planos/P01.py`, `planos/P02.py` | Cronología bloqueada, APIs de personajes/entorno; puede preparar cámaras/datos antes de integrarlos |
| Revisor independiente | Diagnóstico en `review/critica-ronda.md`; sin editar la producción | Artefactos terminados y referencia; no debe haber construido esos planos |

Son responsabilidades, no seis agentes obligatorios. En una pieza con recursos existentes, prioriza agentes por planos o gags. En una pieza nueva puede convenir separar aspecto, personajes y escenario primero. Combina papeles cuando haya poco trabajo independiente; empieza con dos o tres constructores si no hay evidencia para aumentar la concurrencia. El revisor interviene cuando haya material revisable, no ocupa un puesto esperando todo el proceso. Mantén el modelo elegido por el usuario/sesión; no fijes Opus/Sonnet ni prometas ahorro de tokens sin medirlo.

Cada archivo tiene un solo escritor. Nadie modifica la entrega de otro agente para desbloquearse: comunica la necesidad al coordinador. Define las firmas antes de repartir; permite implementaciones provisionales solo dentro del archivo propio y con la API acordada, sin presentar un sustituto como acabado. Cuando una dependencia sea imprescindible, entrega un avance y declara el bloqueo; el coordinador reasigna trabajo útil.

## Encargo que recibe cada subagente

No presupongas que conoce la conversación o que ha cargado la skill. Incluye en su encargo:

```text
Lee <ruta-absoluta-skill>/SKILL.md y references/paralelo.md.
Proyecto: <ruta>. Brief/storyboard: <rutas y versión>. Contrato: <ruta>.
Objetivo: <entrega concreta y planos/rango>. Solo puedes escribir: <archivos exactos>.
Lee también: <referencias de la skill y fuentes necesarias para esta tarea>.
Interfaces/dependencias: <firmas, anclas, unidades y entregas disponibles>.
Autorización vigente: <alcance literal>; renders: solo mediante la cola del coordinador.
Valida lo permitido y devuelve archivos, pruebas, pendientes y petición de render si hace falta.
No cambies tiempos/identidad compartidos, no sobrescribas archivos ajenos ni delegues más sin asignación del coordinador.
```

El coordinador mantiene una lista breve de tareas pendientes, en curso, bloqueadas y verificadas, usando las herramientas nativas disponibles o el contrato. Guarda identificadores de los subagentes para recuperar sus resultados y enviar correcciones al mismo propietario. Evita duplicar contextos y registros completos: cada devolución resume entrega, cambios de interfaz, comprobaciones y pendientes, con rutas y tiempos concretos.

## Render mientras avanza otro trabajo

La escritura de código, preparación de recursos y análisis pueden avanzar en paralelo. La cola de GPU pertenece al coordinador: por defecto, un trabajo pesado activo. Los workers internos del renderizador ya consumen recursos; no multipliques procesos de Blender o navegadores porque haya más subagentes. Ajusta la concurrencia solo con medición y dentro de la GPU/calidad autorizadas.

Antes de renderizar, integra una entrega terminada, comprueba sus dependencias y fija una versión de todas sus fuentes. Mientras dure esa ejecución, nadie edita los archivos que consume, incluidos materiales y módulos compartidos. Los demás agentes trabajan en otros archivos que no sean dependencias activas; si necesitan cambiarlas, dejan una propuesta para la siguiente versión. Si no es posible separar esas fuentes, el coordinador prepara una copia aislada del proyecto para ese render y registra su procedencia, sin duplicar recursos grandes por rutina. No compartas carpetas de salida entre ejecuciones.

Ejemplo de solapamiento: se renderiza la muestra autorizada P01 desde fuentes fijas; otro agente prepara P02 y otro revisa los datos de efectos. Al terminar P01, se inspecciona y se autoriza en la cola el siguiente trabajo que esté listo. No se construye el completo fuera del alcance aprobado porque un agente haya quedado libre.

En 2.5D sigue `25d.md`: generadores por plano y fuentes declaradas con `--fuente` cuando proceda. `--solo` conserva el alcance de un recurso, pero un cambio global de generador/dependencias crea otra huella; no reutilices los demás dibujos como si ese cambio no les afectara. En HTML/Canvas conserva el contrato `window.seek(t)` y el motor existente. En edición, el coordinador conserva la propiedad de `montaje.json`; esta delegación no añade operaciones de edición pendientes.

## Integración, revisión y corrección

El coordinador acepta una entrega solo tras comprobar archivos, interfaces, cobertura temporal, recursos y pruebas aportadas. Integra una versión coherente; después ejecuta auditoría, determinismo, muestra, hojas, ritmo y verificación según la fase y las autorizaciones. Una tarea acabada por el subagente no equivale a una muestra aprobada.

Cuando haya una muestra o completo revisable, entrega a un crítico nuevo las referencias, brief y artefactos. Pide observaciones con plano/fotograma/tiempo y evidencia, distinguiendo imagen, reproducción y escucha realmente realizadas. Confirma cada defecto a tamaño de entrega. Devuelve las correcciones confirmadas al propietario del plano/gag, conservando cronología y alcance; cambios compartidos pasan por el coordinador. Usa las rondas y criterios ya previstos por `SKILL.md`, sin bucles ilimitados ni aprobaciones adicionales rutinarias.

Anota en `REVISION.md` qué se solapó, tiempos de inicio/fin de tareas y renders, esperas, fallos y rehacer trabajo. Mide también el tiempo total de pared. Para afirmar aceleración hace falta una referencia secuencial comparable con las mismas fuentes, calidad y alcance; más agentes o un render corto no la demuestran. Esta guía define coordinación; no garantiza que una sesión concreta delegue bien sin comprobar sus tareas y entregas.

## Prompt breve para Claude Code

```text
Usa /motion-studio con references/paralelo.md. Delega tareas independientes a subagentes de Claude en segundo plano, coordina archivos y renders, y respeta el flujo, las aprobaciones y la verificación de la skill.
```
