# Mediciones antes/después de los escenarios de calidad

Generado por `python evaluacion/medir_escenarios.py` el 2026-11-05 12:54 sobre la base `ClubFutbolDB_MedicionDespues` en `QIYIB\SQLEXPRESS`.

Misma operación, mismos datos, mismo servidor: **antes** = esquema original + código
original (`evaluacion/original/crud_mvp_original.py`, copia fiel de `crud.py`);
**después** = esquema con migraciones + servicios de la re-arquitectura.

## Resumen

| Escenario | Antes | Después | Medida (Semana 13) | ¿Cumple? |
|---|---|---|---|---|
| E2 Confiabilidad | 10 de 10 fallos dejan al jugador sin principal | 0 de 10 | 0 estados parciales en 10 fallos | Sí |
| E2 Confiabilidad (tiempo) | — | reversión en 36.78 ms como máximo | Reversión en menos de 2 s (Semana 8) | Sí |
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

**Tiempo de reversión** (medida de la Semana 8: menos de 2 segundos): desde que se ordena
el cambio hasta que la unidad de trabajo terminó el `ROLLBACK` y cerró la conexión.
Mediana 4.97 ms; máximo 36.78 ms en 10 fallos.

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
| 50 | Tutores | 50 | 1 | 98.0 % | 13.27 | 11.26 | Sí |
| 50 | Jugadores | 50 | 1 | 98.0 % | 10.38 | 9.81 | Sí |
| 50 | Profesores | 50 | 1 | 98.0 % | 14.12 | 10.58 | Sí |
| 500 | Tutores | 500 | 1 | 99.8 % | 10.45 | 9.87 | Sí |
| 500 | Jugadores | 500 | 1 | 99.8 % | 12.33 | 9.23 | Sí |
| 500 | Profesores | 500 | 1 | 99.8 % | 11.09 | 9.14 | Sí |
| 2000 | Tutores | 2000 | 1 | 100.0 % | 16.68 | 10.21 | Sí |
| 2000 | Jugadores | 2000 | 1 | 100.0 % | 21.49 | 17.75 | Sí |
| 2000 | Profesores | 2000 | 1 | 100.0 % | 17.73 | 9.62 | Sí |

**Abrir el formulario de edición** de un registro:

| Registros | Entidad | Filas antes | Filas después | Reducción | ms antes | ms después |
|---|---|---|---|---|---|---|
| 50 | Tutores | 50 | 1 | 98.0 % | 9.92 | 11.71 |
| 50 | Jugadores | 50 | 1 | 98.0 % | 20.5 | 14.96 |
| 50 | Profesores | 50 | 1 | 98.0 % | 9.51 | 11.52 |
| 500 | Tutores | 500 | 1 | 99.8 % | 10.4 | 9.18 |
| 500 | Jugadores | 500 | 1 | 99.8 % | 12.44 | 8.8 |
| 500 | Profesores | 500 | 1 | 99.8 % | 10.71 | 8.69 |
| 2000 | Tutores | 2000 | 1 | 100.0 % | 15.84 | 9.12 |
| 2000 | Jugadores | 2000 | 1 | 100.0 % | 22.7 | 9.79 |
| 2000 | Profesores | 2000 | 1 | 100.0 % | 18.5 | 8.86 |

Los tiempos dependen del equipo; la cifra que no depende del equipo es la de filas
transferidas: antes crecía con la tabla y ahora es constante.
