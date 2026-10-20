# Migraciones de base de datos

Los cambios de esquema se versionan aquí con un número correlativo y se aplican
en orden sobre una base creada con `../ClubFutbolDB.sql`.

| N.º | Archivo | Decisión | Estado |
|---|---|---|---|
| 001 | `001_inactivacion_logica.sql` | ADR-0003, ADR-0004 | Lista para aplicar |

Reglas:

1. Nunca editar una migración ya aplicada; los cambios nuevos van en un archivo nuevo.
2. Toda migración debe ser idempotente y terminar con una consulta de verificación.
3. Hacer copia de seguridad de `ClubFutbolDB` antes de aplicarla.
