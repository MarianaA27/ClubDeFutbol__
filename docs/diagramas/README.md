# Diagramas de arquitectura — versión 2

Los diagramas muestran **cómo quedó realmente el sistema** al terminar la
re-arquitectura (entrega final). La versión 1 (arquitectura objetivo del Entregable 3)
sigue en el historial de git. Cambios de la versión 2: la API REST como segundo
adaptador de presentación, las migraciones 001–003, la limpieza del código legado y
la integración continua con SQL Server real; se agrega un diagrama de secuencia del
flujo principal. Están hechos con [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML),
que viene incluido en PlantUML, así que no se necesita conexión a internet para exportarlos.

| Diagrama | Editable | Exportado |
|---|---|---|
| C4 nivel 1 — Contexto | [`fuentes/c4-1-contexto.puml`](fuentes/c4-1-contexto.puml) | [PNG](exportados/c4-1-contexto.png) · [SVG](exportados/c4-1-contexto.svg) |
| C4 nivel 2 — Contenedores | [`fuentes/c4-2-contenedores.puml`](fuentes/c4-2-contenedores.puml) | [PNG](exportados/c4-2-contenedores.png) · [SVG](exportados/c4-2-contenedores.svg) |
| C4 nivel 3 — Componentes del MVP | [`fuentes/c4-3-componentes.puml`](fuentes/c4-3-componentes.puml) | [PNG](exportados/c4-3-componentes.png) · [SVG](exportados/c4-3-componentes.svg) |
| Despliegue (equipo del club + integración continua) | [`fuentes/despliegue.puml`](fuentes/despliegue.puml) | [PNG](exportados/despliegue.png) · [SVG](exportados/despliegue.svg) |
| Secuencia: cambiar el acudiente principal | [`fuentes/secuencia-cambiar-principal.puml`](fuentes/secuencia-cambiar-principal.puml) | [PNG](exportados/secuencia-cambiar-principal.png) · [SVG](exportados/secuencia-cambiar-principal.svg) |

## Cómo identificar el MVP

* **Contexto y contenedores:** en verde, el sistema/contenedor que aloja el MVP; en azul
  oscuro, lo nuevo de la re-arquitectura (API REST, `config.ini`, bitácora).
* **Componentes:** cada capa del MVP tiene su color (azul presentación —escritorio y API—, verde
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
