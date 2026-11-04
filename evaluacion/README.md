# Evaluación de los escenarios de calidad (antes/después)

Scripts que responden a la retroalimentación del Entregable 3: *validar contra SQL
Server real* y *sustentar las mejoras con mediciones antes/después*. Todos usan la
conexión de `config.ini` (o `PALADINES_DB_*`) y trabajan sobre bases **aparte** cuyo
nombre empieza por `ClubFutbolDB_`; ninguno modifica la base del club. Cada uno escribe
su resultado en `docs/evaluacion/`.

| Script | Escenario / issue | Qué hace | Resultado |
|---|---|---|---|
| `medir_e1.py` | E1 Mantenibilidad (#17) | Cuenta las lecturas por posición en las pantallas del MVP (original vs. actual) y mide el cambio real del campo EPS a partir de los commits `(E1)` | `e1-mantenibilidad.md` |
| `migrar_copia.py` | Migraciones (#15) | Respalda la base del club, la restaura como `ClubFutbolDB_Copia` y aplica todas las migraciones sobre la copia, con conteos antes/después e idempotencia | `migracion-copia.md` |
| `protocolo_historial.py` | E3 Seguridad (#16) | Ejecuta los seis criterios del protocolo del Entregable 1 (§3.5) sobre la copia de la base real | `protocolo-historial.md` |
| `medir_escenarios.py` | E2, E3, E4 (#18) | Ejecuta la misma operación con el código original y con el nuevo, sobre dos bases con los mismos datos | `resultados-mediciones.md` y `.json` |

`original/crud_mvp_original.py` es una copia fiel de las funciones del MVP del sistema
original (`crud.py` y `db.py`). Se conserva solo para medir el "antes"; la aplicación no
la usa.

## Orden sugerido

```bash
python -m pytest --integracion                               # 1. validación contra SQL Server
python evaluacion/medir_e1.py --minutos <tiempo del cambio>   # 2. E1
python evaluacion/migrar_copia.py                            # 3. copia de la base real + migraciones
python evaluacion/protocolo_historial.py --base ClubFutbolDB_Copia   # 4. E3 con datos reales
python evaluacion/medir_escenarios.py                        # 5. E2, E3 y E4 antes/después
```

Quien no tenga la base del club puede usar `protocolo_historial.py --sembrar`, que crea
datos representativos. `medir_escenarios.py` también corre en la integración continua:
el resultado queda en la pestaña **Actions** del repositorio (artefacto
`resultados-mediciones` y resumen de la ejecución).
