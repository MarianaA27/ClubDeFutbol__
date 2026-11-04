# Migraciones de base de datos

Los cambios de esquema se versionan aquí con un número correlativo y se aplican
en orden sobre una base creada con `../ClubFutbolDB.sql`.

| N.º | Archivo | Decisión | Estado |
|---|---|---|---|
| 001 | `001_inactivacion_logica.sql` | ADR-0003, ADR-0004 | Lista para aplicar |
| 002 | `002_eps_jugador.sql` | Escenario E1 (campo EPS) | Lista para aplicar |
| 003 | `003_retiro_objetos_reemplazados.sql` | ADR-0004, ADR-0005 (limpieza del legado) | Lista para aplicar |

Reglas:

1. Nunca editar una migración ya aplicada; los cambios nuevos van en un archivo nuevo.
2. Toda migración debe ser idempotente y terminar con una consulta de verificación.
3. Hacer copia de seguridad de `ClubFutbolDB` antes de aplicarla.
4. Para ensayarlas sin tocar la base del club: `python evaluacion/migrar_copia.py`
   (respalda la base, la restaura como copia y aplica todas las migraciones sobre la copia).
5. Las pruebas de integración (`python -m pytest --integracion`) crean una base desde cero
   con el esquema y **todas** las migraciones, así que cualquier error de una migración las hace fallar.
