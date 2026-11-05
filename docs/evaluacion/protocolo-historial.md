# Protocolo de preservación del historial (E3)

Generado por `python evaluacion/protocolo_historial.py` el 2026-11-04 18:15 sobre la base `ClubFutbolDB_Copia` en `localhost\SQLEXPRESS`.

Origen de los datos: copia de una base preparada por el equipo para el protocolo, con datos
de prueba (no son los datos reales del club) y con las migraciones 001 a 004 ya aplicadas.
Las bajas se hicieron con `ProfesorService.inactivar` y `JugadorService.inactivar`; al final
se reactivaron, así que la base quedó como estaba.

## Resultado por criterio (Entregable 1, §3.5)

| Criterio | Comprobación | ¿Cumple? |
|---|---|---|
| 1. Preparación | Profesor 1 con 3 sesiones; jugador 1 con 3 pagos y 3 asistencias | Sí |
| 2. Conservación | Conteos de historial idénticos tras las bajas; estados 'inactivo' | Sí |
| 3. Exclusión operativa | Profesor fuera de los desplegables (servicio y legado); jugador fuera de convocables y asignables | Sí |
| 4. Consulta histórica | Sesiones con el nombre del profesor; reportes de asistencia e ingresos iguales | Sí |
| 5. Reversibilidad | Tras reactivar, mismos datos y de nuevo disponible | Sí |
| 6. Integridad referencial | 0 filas huérfanas en 9 llaves foráneas | Sí |

**Resultado global: CUMPLE los seis criterios.**

## Conteos de historial

| Tabla | Inicial | Tras las bajas | Diferencia |
|---|---|---|---|
| SESION | 3 | 3 | 0 |
| SESION_JUGADOR | 3 | 3 | 0 |
| PLANTILLA_JUGADOR | 1 | 1 | 0 |
| PLANTILLA_PROFESOR | 1 | 1 | 0 |
| PAGO | 3 | 3 | 0 |
| MOROSIDAD | 2 | 2 | 0 |
| JUGADOR_TUTOR | 2 | 2 | 0 |

## Llaves foráneas revisadas (criterio 6)

| Columna hija | Referencia | Huérfanas |
|---|---|---|
| JUGADOR_TUTOR.id_jugador | JUGADOR.id_jugador | 0 |
| MOROSIDAD.id_jugador | JUGADOR.id_jugador | 0 |
| PAGO.id_jugador | JUGADOR.id_jugador | 0 |
| PLANTILLA_ALINEACION.id_jugador | JUGADOR.id_jugador | 0 |
| PLANTILLA_JUGADOR.id_jugador | JUGADOR.id_jugador | 0 |
| SESION_JUGADOR.id_jugador | JUGADOR.id_jugador | 0 |
| PLANTILLA_PROFESOR.id_profesor | PROFESOR.id_profesor | 0 |
| SESION.id_profesor | PROFESOR.id_profesor | 0 |
| JUGADOR_TUTOR.id_tutor | TUTOR.id_tutor | 0 |

## Comparación con el sistema original

En el sistema original la misma baja ejecutaba `SP_EliminarProfesor` y `SP_EliminarJugador`,
que borran en cascada las sesiones, asistencias, pagos y morosidad. La medición antes/después
de ese borrado está en `docs/evaluacion/resultados-mediciones.md` (escenario E3).
