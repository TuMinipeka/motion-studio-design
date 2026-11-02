# Cambios y documentación

## Mensajes de commit

Usa [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):

```text
tipo(alcance): descripción breve

Motivo del cambio y resultado esperado, cuando ayuden a entenderlo.
Validación realizada y limitaciones relevantes.
```

El alcance es opcional; en este proyecto ayuda a localizar el cambio (`setup`, `render`, `audio`, `skill`, `docs`). Emplea `feat` para capacidades nuevas, `fix` para corregir defectos y `docs` para documentación. `refactor`, `test`, `chore`, `perf`, `build` y `ci` pueden usarse cuando describan el propósito real. Marca incompatibilidades con `!` o un pie `BREAKING CHANGE:` y explica cómo adaptarse.

Ejemplos de títulos:

```text
feat(setup): prepare shared rendering dependencies
fix(render): reject invalid preview intervals
docs(project): record improvements and commit conventions
```

Agrupa por propósito para que cada commit pueda revisarse. Evita títulos genéricos como «update» o «mejoras». Conserva el idioma de los títulos recientes de este repositorio: inglés para los commits y español para la documentación de uso. No reescribas historia ya publicada solo para normalizar mensajes.

## Registro de mejoras

Actualiza `CHANGELOG.md` junto con cada cambio de comportamiento, sin inventar una versión publicada. Cada entrada debe indicar:

- Qué problema o necesidad atiende y qué comportamiento añade o corrige.
- Cómo se usa y qué archivos o guía lo explican, si corresponde.
- Qué se comprobó realmente y qué sigue pendiente.

Actualiza también el README, `SKILL.md` y las referencias afectadas. Para análisis amplios, enlaza un documento en `docs/analysis/` en lugar de duplicarlo. Nunca presentes la validación de sintaxis, una hoja de contacto o una métrica como prueba de la calidad de un video completo.

## Antes de crear el commit

Revisa `git diff` y prepara solo los archivos del cambio. Ejecuta las verificaciones apropiadas: `git diff --check`, validación de la skill, sintaxis de scripts y pruebas funcionales cuando cambie código ejecutable. No instales dependencias globales ni produzcas videos del usuario para verificar un cambio que no lo requiere. Registra lo que no pudo probarse.

Las reglas se revisan manualmente; este repositorio no incorpora un hook automático que valide los mensajes de commit.
