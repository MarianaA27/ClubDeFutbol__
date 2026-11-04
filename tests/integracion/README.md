# Pruebas de integración contra SQL Server

Atienden la retroalimentación del Entregable 3: *"Validar transacciones e historial
contra SQL Server real, no solo dobles"*.

| Archivo | Qué valida contra el motor real |
|---|---|
| `test_transacciones_sqlserver.py` | **E2**: 10 fallos inyectados entre los dos `UPDATE` de "cambiar acudiente principal", un error real del motor (índice único) y la pérdida real de la sesión (`KILL`). En todos los casos el jugador conserva su acudiente principal. |
| `test_historial_sqlserver.py` | **E3**: la baja de un profesor con 12 sesiones y 2 plantillas, y la de un jugador con pagos y morosidad, conservan todas las filas de historial (conteos idénticos, cero huérfanas); reactivación; ya no existen procedimientos de borrado físico. |
| `test_repositorios_sqlserver.py` | SQL de los repositorios: `SCOPE_IDENTITY()` con el trigger de morosidad, búsqueda con `WHERE`, homónimos resueltos por id, índices únicos de la migración 001. |

## Cómo ejecutarlas

Requisitos: SQL Server (Express sirve), ODBC Driver 17 o 18 y un usuario con
permiso para **crear bases de datos** (la autenticación de Windows del
administrador del equipo lo tiene).

```bash
python -m pytest --integracion
```

* Usan la misma conexión de la aplicación (`config.ini` o `PALADINES_DB_*`), pero
  crean y borran una base **aparte**, `ClubFutbolDB_Pruebas`, con
  `src/sql/ClubFutbolDB.sql` + todas las migraciones. **La base del club no se toca.**
* Otro nombre de base: `PALADINES_TEST_DATABASE=ClubFutbolDB_Otra`.
* Para revisar la base en SSMS después de las pruebas: `PALADINES_CONSERVAR_BASE=1`.
* Sin `--integracion`, `python -m pytest` las omite y sigue sin necesitar SQL Server.

## Hallazgos

Ejecutarlas contra el motor real encontró dos defectos que los dobles no podían ver:

1. **`ClubFutbolDB.sql`** tenía un `SELECT` y un `CREATE OR ALTER PROCEDURE` en el
   mismo lote: SQL Server rechaza ese lote, así que `SP_AsignarJugadorPlantilla`
   nunca se actualizaba al crear la base desde cero. Se agregó el `GO` que faltaba.
2. **Unidad de trabajo:** cuando la sesión se pierde, `rollback()` también falla y
   ese segundo error ocultaba el original. Ahora se registra como aviso en la
   bitácora y se propaga el error que causó la falla (SQL Server ya revirtió la
   transacción al cerrar la sesión).
