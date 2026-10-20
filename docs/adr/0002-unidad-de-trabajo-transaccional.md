# ADR-0002: Unidad de trabajo transaccional

* **Estado:** Implementada y probada
* **Fecha:** 2026-10-19
* **Responsable:** Giany Andrés Salazar Bustamante

## Contexto y problema (Semana 3 — P2: ausencia de atomicidad)

`db.ejecutar_query()` abre una conexión, ejecuta **una** sentencia, hace `commit()` y cierra.
Las operaciones de negocio que necesitan varias sentencias quedan partidas en varias
transacciones:

| Operación | Sentencias independientes en el sistema original |
|---|---|
| Cambiar acudiente principal (`set_acudiente_principal`) | `UPDATE` (desmarcar) + `UPDATE` (marcar) |
| Vincular tutor (`insert_jugador_tutor`) | `SELECT` + `UPDATE` + `INSERT` |
| Desvincular tutor (`delete_jugador_tutor`) | `SELECT` + `SELECT` + `DELETE` |
| Eliminar jugador (`delete_jugador`) | `SELECT` de verificación + `EXEC` en otra conexión |

Si la ejecución falla entre dos sentencias, la base queda en un estado que viola una
regla de negocio (p. ej. un jugador sin acudiente principal) y nada lo detecta ni lo repara.

## Decisión

Toda operación de negocio del MVP se ejecuta dentro de una **unidad de trabajo**
(`UnidadDeTrabajoSql`): una conexión, `autocommit=False` y una sola transacción.

```python
with UnidadDeTrabajoSql(operacion="cambiar acudiente principal") as uow:
    uow.vinculos.establecer_principal(id_jugador, id_tutor)   # 2 UPDATE
    uow.commit()                                               # todo o nada
```

* Excepción dentro del bloque → `rollback()` automático, registro en la **bitácora**
  (`logs/paladinesfc.log`) y la excepción se propaga a la interfaz.
* Bloque sin `commit()` explícito → `rollback()` (nada se persiste por accidente).
* Los repositorios no abren conexiones: usan la de la unidad de trabajo.
* Los servicios dependen del **puerto** `UnidadDeTrabajo` (`aplicacion/puertos.py`), no de
  pyodbc; se prueban con una implementación en memoria.

**Mejora colateral:** la cadena de conexión deja de estar fijada en el código
(`SERVER=GIANY`) y se lee de `config.ini` o de variables `PALADINES_DB_*`
(`infraestructura/config.py`). `legado/db.py` también la usa.

## Código afectado

| Antes (sistema original) | Después (`src/`) |
|---|---|
| `db.py`: `obtener_conexion()`, `ejecutar_query()` | `infraestructura/conexion.py`, `infraestructura/unidad_trabajo.py`, `infraestructura/config.py`, `infraestructura/bitacora.py` |
| `crud.py`: `set_acudiente_principal`, `insert_jugador_tutor`, `delete_jugador_tutor`, `insert_jugador_con_tutor` | `aplicacion/vinculacion_service.py`, `aplicacion/jugador_service.py`, `infraestructura/repositorios/vinculos.py` |
| `SP_InsertarJugadorTutor` (transacción dentro del SP) | `JugadorService.registrar_con_tutor()` (transacción en la unidad de trabajo) |

## Atributo de calidad que mejora (Semana 8)

**Confiabilidad — tolerancia a fallos y capacidad de recuperación** (escenario E2).

## Consecuencias

* **Positivas:** cero estados parciales; un único punto donde se controla la transacción
  y se registran los fallos; los servicios son probables sin SQL Server.
* **Negativas:** la transacción se mantiene abierta durante la operación (irrelevante en un
  sistema monousuario); los módulos legados siguen con `commit` por sentencia hasta migrarse.

## Verificación

```bash
python -m pytest tests/test_unidad_trabajo.py -v
```

`test_fallo_entre_las_dos_sentencias_no_deja_estados_parciales` ejecuta **10 inyecciones
controladas** de fallo después del primer `UPDATE` y comprueba que no se confirma nada,
que hay exactamente un `rollback` y que la conexión se cierra.
`test_el_fallo_queda_registrado_en_la_bitacora` comprueba el registro del fallo.
