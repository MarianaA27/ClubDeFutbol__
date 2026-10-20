# Backlog hacia la Semana 15

Cada fila se crea como **issue** en GitHub y se agrega al tablero (*Projects* → plantilla
*Board* con las columnas **Por hacer · En progreso · En revisión · Hecho**). Cada pull request
debe cerrar su issue escribiendo `Closes #N` en la descripción.

Etiquetas sugeridas: `arquitectura`, `codigo`, `pruebas`, `bd`, `documentacion`, `entregable-3`, `entregable-final`.

## Entregable 3 (Semana 13)

| # | Issue | Responsable | Etiquetas |
|---|---|---|---|
| 1 | Estructura base del repositorio y código legado aislado | Giany | `codigo`, `entregable-3` |
| 2 | README y arquitectura.md iniciales | Juan Camilo | `documentacion`, `entregable-3` |
| 3 | ADR-0002: unidad de trabajo transaccional con pruebas de fallo inyectado | Giany | `arquitectura`, `codigo`, `pruebas` |
| 4 | ADR-0001 y ADR-0004: entidades de dominio, reglas y puertos | Mariana | `arquitectura`, `codigo`, `pruebas` |
| 5 | Diagramas C4 v1 (contexto, contenedores, componentes) y despliegue | Carlos | `arquitectura`, `documentacion` |
| 6 | ADR-0005: repositorios SQL del MVP | Giany | `codigo`, `pruebas` |
| 7 | Servicios de aplicación del MVP | Mariana | `codigo`, `pruebas` |
| 8 | ADR-0003: inactivación lógica y migración 001 | Juan Camilo | `arquitectura`, `bd` |
| 9 | Tabla de componentes y responsabilidades | Carlos | `documentacion` |
| 10 | Conectar las pantallas del MVP a los servicios | Giany | `codigo` |
| 11 | Escenarios de calidad actualizados y README final | Juan Camilo | `documentacion` |

## Pendientes (Semanas 14–15)

| # | Issue | Descripción / criterio de aceptación | Responsable | Semana |
|---|---|---|---|---|
| 12 | Pruebas de integración contra SQL Server | Ejecutar los repositorios sobre una base de prueba creada con `ClubFutbolDB.sql` + migración 001. Marcar las pruebas con `@pytest.mark.integracion` para que no corran sin BD | Giany | 14 |
| 13 | Integración continua | GitHub Actions que ejecute `python -m pytest` en cada push y pull request | Carlos | 14 |
| 14 | Pruebas de caracterización de las 18 operaciones | Documentar el comportamiento observable antes/después, incluidos los defectos corregidos | Mariana | 14 |
| 15 | Aplicar migración 001 en una copia de la base real | Copia de seguridad, ejecución, captura de la consulta de verificación | Juan Camilo | 14 |
| 16 | Protocolo de preservación del historial (Entregable 1, §3.5) | Conteos de `SESION`, `SESION_JUGADOR`, `PAGO`, `MOROSIDAD` antes y después de dar de baja; reactivación; cero filas huérfanas | Juan Camilo | 14 |
| 17 | Demostración del escenario E1 (campo EPS) | Rama de prueba que agregue el campo; medir archivos tocados y tiempo | Mariana | 14 |
| 18 | Medición del escenario E4 | Script que cuente filas transferidas por búsqueda y edición en la versión original y la nueva | Carlos | 14–15 |
| 19 | Limpieza del código legado | Eliminar `guardar_alineacion`/`get_alineacion` duplicadas y las funciones sin uso de `legado/crud.py`; retirar `SP_InsertarJugadorTutor` y los SP de inserción que el MVP ya no usa | Giany | 15 |
| 20 | Empaquetado | Actualizar `ClubFutbol.spec` a la nueva estructura (`run.py`, `config.ini`), generar el `.exe` y probarlo en un equipo limpio | Giany | 15 |
| 21 | Diagramas C4 versión 2 | Actualizar con lo realmente implementado y agregar diagrama de secuencia de "cambiar acudiente principal" | Carlos | 15 |
| 22 | Informe comparativo antes/después de los atributos de calidad | Resultados de E1–E4 con evidencia | Juan Camilo + Mariana | 15 |
| 23 | Presentación final y demostración en vivo | Guion, diapositivas y ensayo | Todo el equipo | 15 |
