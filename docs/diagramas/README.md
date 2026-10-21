# Diagramas de arquitectura — versión 1

Los diagramas muestran la **arquitectura objetivo** (cómo queda el sistema después
de la refactorización). Están hechos con [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML),
que viene incluido en PlantUML, así que no se necesita conexión a internet para exportarlos.

| Diagrama | Editable | Exportado |
|---|---|---|
| C4 nivel 1 — Contexto | [`fuentes/c4-1-contexto.puml`](fuentes/c4-1-contexto.puml) | [PNG](exportados/c4-1-contexto.png) · [SVG](exportados/c4-1-contexto.svg) |
| C4 nivel 2 — Contenedores | [`fuentes/c4-2-contenedores.puml`](fuentes/c4-2-contenedores.puml) | [PNG](exportados/c4-2-contenedores.png) · [SVG](exportados/c4-2-contenedores.svg) |
| C4 nivel 3 — Componentes del MVP | [`fuentes/c4-3-componentes.puml`](fuentes/c4-3-componentes.puml) | [PNG](exportados/c4-3-componentes.png) · [SVG](exportados/c4-3-componentes.svg) |
| Despliegue | [`fuentes/despliegue.puml`](fuentes/despliegue.puml) | [PNG](exportados/despliegue.png) · [SVG](exportados/despliegue.svg) |

## Cómo identificar el MVP

* **Contexto y contenedores:** en verde, el sistema/contenedor que aloja el MVP.
* **Componentes:** cada capa del MVP tiene su color (azul presentación, verde
  aplicación, naranja dominio, morado infraestructura). Lo que está **en gris y con
  línea punteada** es legado y queda fuera del alcance del MVP.

## Cómo editar y exportar

* **En línea:** pegar el contenido del `.puml` en <https://www.plantuml.com/plantuml>.
* **VS Code:** extensión *PlantUML* (jebbs.plantuml) → `Alt + D` para previsualizar.
* **Línea de comandos** (requiere Java):

```bash
java -jar plantuml.jar -tpng -o ../exportados docs/diagramas/fuentes/*.puml
java -jar plantuml.jar -tsvg -o ../exportados docs/diagramas/fuentes/*.puml
```

Después de editar un `.puml`, vuelvan a exportar y suban **los dos** (fuente y exportado) en el mismo commit.
