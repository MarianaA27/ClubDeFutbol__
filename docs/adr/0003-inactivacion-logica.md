# ADR-0003: Inactivación lógica en lugar de borrado físico

* **Estado:** Implementada en código; migración 001 lista para aplicar
* **Fecha:** 2026-10-19
* **Responsable:** Juan Camilo Moreno Pérez

## Contexto y problema (Semana 3 — P3: borrado físico en cascada)

* `SP_EliminarProfesor` borra el profesor y **en cascada** `SESION_JUGADOR`, `SESION` y
  `PLANTILLA_PROFESOR`: se pierden los partidos que dirigió y la asistencia de jugadores
  que siguen activos, aunque la tabla `PROFESOR` ya tiene una columna `estado`.
* `SP_EliminarJugador` borra `SESION_JUGADOR`, `PLANTILLA_JUGADOR`, `MOROSIDAD`, `PAGO` y
  `JUGADOR_TUTOR`: desaparece la trazabilidad financiera que el sistema debía garantizar.
  Además borra `MOROSIDAD` **antes** que `PAGO` (que la referencia) y no limpia
  `PLANTILLA_ALINEACION`, por lo que en esos casos falla con un error técnico de SQL.
* La interfaz pide confirmación, pero la operación es **irreversible**: no hay respaldo
  ni bitácora.

## Decisión

"Eliminar" pasa a ser **"Dar de baja"**: se cambia el `estado` a `inactivo` y no se borra nada.

| Entidad | Regla de baja | Efecto |
|---|---|---|
| Jugador | Bloqueada si tiene plantillas activas (regla original conservada) | `estado = 'inactivo'`; pagos, morosidad, asistencias y vínculos se conservan |
| Profesor | Siempre permitida | `estado = 'inactivo'`; deja de aparecer en los desplegables (`get_profesores_activos` y `ProfesorService.opciones()`); sus sesiones, asistencias y asignaciones a plantillas se conservan como historial |
| Tutor | Bloqueada si tiene jugadores **activos** a cargo | `estado = 'inactivo'` (requiere la migración 001, que agrega la columna) |

* **Reversible:** jugador y profesor se reactivan desde "Editar" cambiando el estado a
  `activo`, sin reingresar datos.
* **Esquema:** `JUGADOR` y `PROFESOR` ya tenían `estado`. `TUTOR` no, así que la migración
  `src/sql/migraciones/001_inactivacion_logica.sql` agrega `TUTOR.estado`. **Esto modifica
  el esquema**, a diferencia de lo anunciado en el Entregable 1 ("esquema preservado"): es
  un cambio aditivo, con valor por defecto, que no afecta a los módulos legados.
* La misma migración **retira** `SP_EliminarJugador`, `SP_EliminarProfesor` y
  `SP_EliminarTutor` para que no quede ninguna vía de borrado físico.
* El repositorio de tutores detecta si la columna existe: antes de aplicar la migración,
  todo funciona igual y solo la baja de tutores pide aplicarla.

## Código afectado

| Antes (sistema original) | Después (`src/`) |
|---|---|
| `crud.delete_jugador()` → `SP_EliminarJugador` | `JugadorService.inactivar()` / `reactivar()` |
| `crud.delete_profesor()` → `SP_EliminarProfesor` | `ProfesorService.inactivar()` / `reactivar()` |
| `crud.delete_tutor()` → `SP_EliminarTutor` | `TutorService.inactivar()` |
| Botones "Eliminar" de `TabJugadores`, `TabTutores`, `TabProfesores` | Botones "Dar de baja" en `presentacion/app.py` |
| — | `src/sql/migraciones/001_inactivacion_logica.sql` |

## Atributo de calidad que mejora (Semana 8)

* **Seguridad — integridad y no repudio:** la evidencia histórica (pagos, sesiones,
  asistencias) no se destruye (escenario E3).
* **Confiabilidad — capacidad de recuperación:** una baja equivocada se revierte.

## Consecuencias

* **Positivas:** cero pérdida de historial; los reportes de asistencia e ingresos dan los
  mismos totales antes y después de una baja.
* **Negativas:** toda consulta de selección debe filtrar `estado = 'activo'`. Las del MVP
  ya lo hacen; las de módulos legados que listan profesores en cuerpos técnicos siguen
  mostrando al profesor inactivo como historial (comportamiento aceptado).
* El cambio de esquema exige aplicar la migración en el equipo del club con copia de seguridad.

## Verificación

* `tests/test_servicios.py::test_inactivar_jugador_conserva_el_registro`
* `tests/test_servicios.py::test_inactivar_profesor_lo_saca_de_los_desplegables_sin_borrarlo`
* `tests/test_servicios.py::test_tutor_con_jugadores_activos_no_se_inactiva`
* Protocolo de preservación del historial (Entregable 1, §3.5) sobre una copia de la base
  real: pendiente para la Semana 14 (issue del tablero).
