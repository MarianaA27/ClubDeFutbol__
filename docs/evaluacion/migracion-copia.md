# Migraciones aplicadas sobre una copia de la base real

> **Aclaración sobre los datos:** la base de origen es una copia de seguridad preparada por
> el equipo (`ClubFutbolDB para el protocolo`), con datos de prueba, no los datos reales del
> club, y **ya tenía aplicadas las migraciones 001 a 004**. Por eso los conteos no cambian.
> Este informe demuestra que volver a ejecutar las migraciones es inocuo (idempotencia) y
> que las verificaciones pasan; no demuestra su primera aplicación sobre una base sin migrar.

Generado por `python evaluacion/migrar_copia.py` el 2026-11-04 18:15 sobre la base `ClubFutbolDB_Copia` en `localhost\SQLEXPRESS`.

Base de origen (no se modificó): `ClubFutbolDB`. Copia de seguridad: `C:\Program Files\Microsoft SQL Server\MSSQL17.SQLEXPRESS\MSSQL\DATA\ClubFutbolDB_antes_migraciones.bak`.

## 1. Conteo de filas antes y después de las migraciones

| Tabla | Antes | Después |  |
|---|---|---|---|
| CANCHA | 1 | 1 |  |
| CATEGORIA | 1 | 1 |  |
| CONCEPTO_PAGO | 1 | 1 |  |
| JUGADOR | 2 | 2 |  |
| JUGADOR_TUTOR | 2 | 2 |  |
| MOROSIDAD | 2 | 2 |  |
| PAGO | 3 | 3 |  |
| PLANTILLA | 1 | 1 |  |
| PLANTILLA_ALINEACION | 1 | 1 |  |
| PLANTILLA_JUGADOR | 1 | 1 |  |
| PLANTILLA_PROFESOR | 1 | 1 |  |
| PROFESOR | 1 | 1 |  |
| SESION | 3 | 3 |  |
| SESION_JUGADOR | 3 | 3 |  |
| TUTOR | 3 | 3 |  |

Tablas con cambios: ninguna.
La migración 001 solo puede cambiar `JUGADOR_TUTOR`: borra vínculos duplicados y repara
jugadores sin exactamente un acudiente principal.

## 2. Consultas de verificación de cada migración

### 001_inactivacion_logica.sql

| Verificación | Resultado |
|---|---|
| TUTOR.estado | OK |
| Jugadores sin exactamente un principal | 0 |
| Índices de reglas creados | 2 |
### 002_eps_jugador.sql

| Verificación | Resultado |
|---|---|
| JUGADOR.eps | OK |
### 003_retiro_objetos_reemplazados.sql

| Verificación | Resultado |
|---|---|
| Objetos del MVP reemplazados que siguen existiendo | 0 |
### 004_reparar_sp_asignar_jugador_plantilla.sql

| Verificación | Resultado |
|---|---|
| Parámetros de SP_AsignarJugadorPlantilla (deben ser 4) | 4 |
| PLANTILLA_JUGADOR.tipo | OK |

## 3. Idempotencia

Ejecutar de nuevo todas las migraciones no cambia ningún conteo: Sí.
