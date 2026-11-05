# Mediciones antes/después de los escenarios de calidad

Generado por `python evaluacion/medir_escenarios.py` el 2026-11-04 23:47 sobre la base `ClubFutbolDB_MedicionDespues` en `localhost,1433`.

Misma operación, mismos datos, mismo servidor: **antes** = esquema original + código
original (`evaluacion/original/crud_mvp_original.py`, copia fiel de `crud.py`);
**después** = esquema con migraciones + servicios de la re-arquitectura.

## Resumen

| Escenario | Antes | Después | Medida (Semana 13) | ¿Cumple? |
|---|---|---|---|---|
| E2 Confiabilidad | 10 de 10 fallos dejan al jugador sin principal | 0 de 10 | 0 estados parciales en 10 fallos | Sí |
| E3 Seguridad | 57 filas de historial borradas | 0 filas | Conteos idénticos | Sí |
| E4 Eficiencia | edición: 2000 filas con 2000 registros | edición: 1 fila | ≥ 90 % menos filas con ≥ 50 registros | Sí |

## E2 — Fallo entre los dos UPDATE de "cambiar acudiente principal"

Se inyectó la pérdida de la conexión justo antes del segundo `UPDATE`, 10 veces con
cada versión. Se cuenta un *estado parcial* cuando el jugador queda sin exactamente un
acudiente principal.

| Versión | Fallos inyectados | Estados parciales |
|---|---|---|
| Antes (`set_acudiente_principal`, commit por sentencia) | 10 | 10 |
| Después (`VinculacionService` + unidad de trabajo) | 10 | 0 |

## E3 — Filas de historial perdidas al dar de baja

Profesor con 12 sesiones (3 jugadores con asistencia en cada una) y 2 plantillas; jugador
con 3 pagos, morosidad, 2 asistencias y su acudiente.

| Tabla | Baja profesor: antes | Baja profesor: después | Baja jugador: antes | Baja jugador: después |
|---|---|---|---|---|
| SESION | 12 | 0 | 0 | 0 |
| SESION_JUGADOR | 36 | 0 | 2 | 0 |
| PLANTILLA_PROFESOR | 2 | 0 | 0 | 0 |
| PLANTILLA_JUGADOR | 0 | 0 | 0 | 0 |
| PAGO | 0 | 0 | 3 | 0 |
| MOROSIDAD | 0 | 0 | 1 | 0 |
| JUGADOR_TUTOR | 0 | 0 | 1 | 0 |
| **Total** | **50** | **0** | **7** | **0** |

* Antes, el registro del profesor **desapareció**; después
  sigue existiendo como inactivo y
  ya no aparece en los desplegables.
* Jugador cuyo pago está ligado a su morosidad: antes,
  se borró sin error;
  después se dio de baja sin perder filas (0 filas).

## E4 — Filas transferidas y tiempo (mediana de 5 ejecuciones)

**Búsqueda por cédula** (una sola coincidencia):

| Registros | Entidad | Filas antes | Filas después | Reducción | ms antes | ms después | ¿Mismo resultado? |
|---|---|---|---|---|---|---|---|
| 50 | Tutores | 50 | 1 | 98.0 % | 7.24 | 6.86 | Sí |
| 50 | Jugadores | 50 | 1 | 98.0 % | 7.9 | 6.71 | Sí |
| 50 | Profesores | 50 | 1 | 98.0 % | 6.75 | 6.5 | Sí |
| 500 | Tutores | 500 | 1 | 99.8 % | 8.82 | 7.56 | Sí |
| 500 | Jugadores | 500 | 1 | 99.8 % | 10.77 | 7.16 | Sí |
| 500 | Profesores | 500 | 1 | 99.8 % | 8.81 | 6.8 | Sí |
| 2000 | Tutores | 2000 | 1 | 100.0 % | 16.05 | 8.23 | Sí |
| 2000 | Jugadores | 2000 | 1 | 100.0 % | 21.85 | 11.04 | Sí |
| 2000 | Profesores | 2000 | 1 | 100.0 % | 16.24 | 8.11 | Sí |

**Abrir el formulario de edición** de un registro:

| Registros | Entidad | Filas antes | Filas después | Reducción | ms antes | ms después |
|---|---|---|---|---|---|---|
| 50 | Tutores | 50 | 1 | 98.0 % | 6.75 | 6.79 |
| 50 | Jugadores | 50 | 1 | 98.0 % | 7.42 | 6.39 |
| 50 | Profesores | 50 | 1 | 98.0 % | 6.6 | 6.26 |
| 500 | Tutores | 500 | 1 | 99.8 % | 8.47 | 6.62 |
| 500 | Jugadores | 500 | 1 | 99.8 % | 10.18 | 6.32 |
| 500 | Profesores | 500 | 1 | 99.8 % | 8.71 | 6.28 |
| 2000 | Tutores | 2000 | 1 | 100.0 % | 14.63 | 6.61 |
| 2000 | Jugadores | 2000 | 1 | 100.0 % | 21.44 | 6.46 |
| 2000 | Profesores | 2000 | 1 | 100.0 % | 16.2 | 6.32 |

Los tiempos dependen del equipo; la cifra que no depende del equipo es la de filas
transferidas: antes crecía con la tabla y ahora es constante.
