# Caracterización de las 18 operaciones del MVP

Issue #14. Compara, operación por operación, el comportamiento observable del sistema
original con el de la re-arquitectura. Las operaciones son las de la tabla 1.4 del
Entregable 1. Cada fila tiene al menos una prueba en `tests/test_caracterizacion.py`
(se ejecutan con `python -m pytest tests/test_caracterizacion.py -v`) y las reglas
también se validan contra SQL Server en `tests/integracion/`.

**Convención:** *Se conserva* = la usuaria obtiene el mismo resultado que antes.
*Cambio deliberado* = corrige un defecto documentado (P1–P5); el cambio es intencional y
la prueba lo fija.

## Jugadores

| N.º | Operación | Sistema original | Re-arquitectura | Resultado | Prueba |
|---|---|---|---|---|---|
| 1 | Consultar listado con tutor | `get_jugadores_con_tutor()`; la pantalla leía cada dato por posición | `JugadorService.listar()`; mismas columnas por nombre, más la EPS (E1). Sin tutor: "Sin tutor", "-", "-" | Se conserva | `test_op01_*` |
| 2 | Consultar detalle completo | `get_detalle_jugador_completo()`: tres consultas en conexiones distintas | `JugadorService.detalle()`: jugador, tutores y plantillas en una sola unidad de trabajo | Se conserva | `test_op02_*` |
| 3 | Registrar jugador con tutor | `SP_InsertarJugadorTutor`; el tutor se elegía por el nombre visible | Una transacción (jugador + vínculo); el tutor se elige por id; mismos mensajes de validación | Cambio deliberado (P1, homónimos) | `test_op03_*` |
| 4 | Editar jugador | `update_jugador()` con una copia propia de las validaciones | La misma validación que el registro (fuente única); documento y fechas siguen sin poder editarse | Se conserva | `test_op04_*` |
| 5 | Eliminar jugador | Borrado físico en cascada (`SP_EliminarJugador`): pagos, morosidad, asistencias y vínculos | "Dar de baja": estado `inactivo`, no se borra nada; se conserva el bloqueo si tiene plantillas activas | Cambio deliberado (P3) | `test_op05_*` |
| 6 | Buscar por documento | Traía la tabla completa y filtraba en Python (`cedula in documento`) | Filtra en SQL Server con `LIKE '%cedula%'`: mismos resultados, solo viajan las filas que coinciden | Se conserva | `test_op06_*` |

## Jugador–Tutor

| N.º | Operación | Sistema original | Re-arquitectura | Resultado | Prueba |
|---|---|---|---|---|---|
| 7 | Vincular tutor | Comprobación, `UPDATE` e `INSERT` en transacciones separadas | Misma regla de duplicados, todo en una transacción; si el jugador no tenía principal, el nuevo pasa a serlo | Se conserva (más atómico) | `test_op07_*` |
| 8 | Cambiar acudiente principal | Dos `UPDATE` sueltos; con un tutor no vinculado, el jugador quedaba **sin principal** | Valida antes de escribir y ejecuta los dos `UPDATE` en una transacción; con un tutor no vinculado responde error y no cambia nada | Cambio deliberado (P2, P4) | `test_op08_*` |
| 9 | Desvincular tutor | Bloqueaba al único tutor, pero **permitía desvincular al principal** | Bloquea al único tutor y al acudiente principal | Cambio deliberado (P4) | `test_op09_*` |
| 10 | Listar tutores de un jugador | `get_tutores_de_jugador()` existía pero ninguna pantalla la usaba | `VinculacionService.tutores_de()`: principal primero; la usan el detalle y la API | Se conserva | `test_op10_*` |

## Tutores

| N.º | Operación | Sistema original | Re-arquitectura | Resultado | Prueba |
|---|---|---|---|---|---|
| 11 | Consultar listado | `get_tutores()`; la búsqueda filtraba en Python | `TutorService.listar()`; búsqueda con `WHERE` | Se conserva | `test_op11_*` |
| 12 | Registrar tutor | `SP_InsertarTutor`; un teléfono repetido mostraba el error crudo de pyodbc | Validación en el dominio; documento y teléfono repetidos dan un mensaje claro | Cambio deliberado (P4) | `test_op12_*` |
| 13 | Editar tutor | `UPDATE` directo, sin procedimiento (segunda vía de escritura) | Una sola vía: servicio → entidad → repositorio | Se conserva | `test_op13_*` |
| 14 | Eliminar tutor | `SP_EliminarTutor`: borrado físico, bloqueado si tenía cualquier vínculo | "Dar de baja": estado `inactivo` (migración 001), bloqueado si tiene jugadores **activos**; sus vínculos se conservan | Cambio deliberado (P3) | `test_op14_*` |

## Profesores

| N.º | Operación | Sistema original | Re-arquitectura | Resultado | Prueba |
|---|---|---|---|---|---|
| 15 | Consultar listado | `get_profesores()` | `ProfesorService.listar()` | Se conserva | `test_op15_*` |
| 16 | Registrar profesor | `SP_InsertarProfesor`; siempre nace activo | Igual, con validación del dominio y teléfono único con mensaje claro | Se conserva | `test_op16_*` |
| 17 | Editar profesor | `UPDATE` directo; `SP_ActualizarProfesor` existía, no se usaba y no recibía el documento | Una sola vía, que sí permite editar el documento; el SP huérfano se retiró (migración 001) | Se conserva | `test_op17_*` |
| 18 | Eliminar profesor | `SP_EliminarProfesor`: borraba en cascada sesiones, asistencias y asignaciones | "Dar de baja": estado `inactivo`, sale de los desplegables, conserva todo su historial y se puede reactivar | Cambio deliberado (P3) | `test_op18_*` |

## Resumen

| | Operaciones |
|---|---|
| Se conserva el comportamiento | 1, 2, 4, 6, 7, 10, 11, 13, 15, 16, 17 (11) |
| Cambio deliberado que corrige un defecto | 3, 5, 8, 9, 12, 14, 18 (7) |
| Comportamiento perdido sin intención | Ninguna |

Los siete cambios deliberados son los que anticipó el criterio de éxito del MVP: la
usuaria no percibe cambios en pantallas, campos ni flujo, salvo "Dar de baja" en lugar
de "Eliminar", los desplegables con el documento y los bloqueos que impiden dejar a un
jugador sin acudiente principal.
