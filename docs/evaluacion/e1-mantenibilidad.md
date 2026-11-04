# Escenario E1 — Mantenibilidad: medición antes/después

Generado por `python evaluacion/medir_e1.py` el 2026-11-03.
Original tomado de: primera versión de app.py en el historial de git.

**Estímulo:** agregar "entidad de salud (EPS)" al jugador: capturarlo al registrar,
editarlo y verlo en el listado.

## 1. Lecturas de datos por posición en las pantallas del MVP

Cada `fila[n]` es un punto que se rompe en silencio si una consulta cambia el
orden o el número de sus columnas (problema P1). Es lo que hacía arriesgado agregar
un campo en el sistema original.

| Pantalla | Antes | Después |
|---|---|---|
| `TabJugadores` | 5 | 0 |
| `FormJugador` | 17 | 0 |
| `VentanaDetalleJugador` | 31 | 0 |
| `FormVincularTutor` | 3 | 0 |
| `TabTutores` | 14 | 0 |
| `FormTutor` | 7 | 0 |
| `TabProfesores` | 11 | 0 |
| `FormProfesor` | 10 | 0 |
| **Total** | **98** | **0** |

## 2. El cambio real en el repositorio

Commits del escenario: 3 (`git log --grep="(E1)"`).

| Archivo de producción | Capa | Líneas |
|---|---|---|
| `src/paladinesfc/aplicacion/jugador_service.py` | Aplicación | +4 / −4 |
| `src/paladinesfc/dominio/jugador.py` | Dominio | +6 / −2 |
| `src/paladinesfc/infraestructura/repositorios/jugadores.py` | Infraestructura | +8 / −7 |
| `src/paladinesfc/presentacion/app.py` | Presentación | +15 / −10 |
| `src/sql/migraciones/002_eps_jugador.sql` | Base de datos (migración) | +25 / −0 |

Pruebas agregadas o ajustadas:

| Archivo | Líneas |
|---|---|
| `tests/fakes_repositorios.py` | +1 / −0 |
| `tests/integracion/test_e1_eps_sqlserver.py` | +24 / −0 |
| `tests/test_e1_campo_eps.py` | +38 / −0 |

Otros archivos: `src/sql/migraciones/README.md`

## 3. Resultado frente a la medida del escenario

| Criterio (Semana 13) | Resultado | ¿Cumple? |
|---|---|---|
| Un archivo por capa | 5 archivos de producción en 5 capas | Sí |
| Ningún archivo fuera del módulo Jugadores | 0 fuera del módulo | Sí |
| Cero accesos por índice | 0 lecturas posicionales en las pantallas del MVP (antes 98) | Sí |
| Menos de 4 horas | sin registrar (use --minutos) | — |
| Las pruebas existentes pasan | Ver la ejecución de `python -m pytest` en el PR del cambio | — |

**Diferencia con lo planeado.** La medida de la Semana 13 estimó "máximo 4 archivos"
(migración, entidad, repositorio y pantalla). El cambio real tocó también el
servicio de aplicación, porque sus casos de uso reciben los datos como parámetros
explícitos. Se cumple el criterio de fondo —un archivo por capa y nada fuera del
módulo—, pero el número correcto para esta arquitectura es uno por cada una de sus
5 capas.
