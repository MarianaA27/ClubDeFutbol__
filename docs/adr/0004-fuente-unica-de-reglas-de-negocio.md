# ADR-0004: Fuente única de reglas de negocio en el dominio

* **Estado:** Implementada en el MVP
* **Fecha:** 2026-10-19
* **Responsable:** Mariana Aguilar Alcaraz

## Contexto y problema (Semana 3 — P4: reglas duplicadas sin fuente única)

* El estado válido de un jugador está en **cuatro** lugares: `_validar_jugador()`, una copia
  dentro de `update_jugador()` (que no reutiliza la anterior), el `CHECK` de la tabla y el
  interior de `SP_ActualizarJugador`. La lista de tallas también está duplicada.
* `update_profesor()` reimplementa casi literalmente `_validar_profesor()`.
* Dos vías de escritura: `update_tutor()` hace `UPDATE` directo (no existe
  `SP_ActualizarTutor`) y `update_profesor()` también, aunque `SP_ActualizarProfesor` existe…
  pero nunca se invoca y **no recibe el documento**, así que usarlo impediría editarlo.
* Reglas que solo existen en la base: `TUTOR.telefono` y `PROFESOR.telefono` son `UNIQUE`,
  pero Python no lo valida y la usuaria ve el error crudo de pyodbc.
* La regla "exactamente un acudiente principal" **no se cumple en ningún lugar**:
  `delete_jugador_tutor()` consulta `acudiente_principal` y nunca usa el dato, y
  `set_acudiente_principal()` deja al jugador sin principal si el tutor no está vinculado.

## Decisión

1. Las reglas de negocio del MVP se escriben **una sola vez**, en el dominio:
   * `dominio/validaciones.py`: formatos y catálogos (`TALLAS`, `ESTADOS_JUGADOR`,
     `ESTADOS_PERSONA`, `PARENTESCOS`).
   * Entidades: crear y editar usan la misma validación (`Profesor.nuevo()` llama a
     `actualizar()`).
   * Agregado `TutoresDelJugador`: al menos un tutor, exactamente un principal, sin
     vínculos duplicados; no se desvincula al principal.
2. **Una sola vía de escritura** para el MVP: servicio → entidad → repositorio, con SQL
   parametrizado. Los SP de escritura del MVP dejan de usarse; la migración 001 elimina
   `SP_ActualizarProfesor` y los SP de borrado.
3. La base conserva sus `CHECK`/`UNIQUE` y suma índices únicos (migración 001) como
   **defensa en profundidad**, no como lugar donde se definen reglas: si la aplicación
   tuviera un error, el motor lo rechaza en vez de guardar datos inconsistentes.
4. La interfaz usa los catálogos del dominio para llenar sus desplegables.

## Código afectado

| Antes (sistema original) | Después (`src/`) |
|---|---|
| `crud.py`: `_validar_*`, validaciones en `update_jugador`, `update_profesor` | `dominio/validaciones.py`, `dominio/jugador.py`, `dominio/tutor.py`, `dominio/profesor.py` |
| `crud.py`: `insert_jugador_tutor`, `set_acudiente_principal`, `delete_jugador_tutor` | `dominio/vinculo.py` (`TutoresDelJugador`), `aplicacion/vinculacion_service.py` |
| `SP_ActualizarJugador`, `SP_InsertarTutor`, `SP_InsertarProfesor`, `SP_InsertarJugadorTutor` | Repositorios SQL (`infraestructura/repositorios/`) |
| `SP_ActualizarProfesor` (huérfano) | Eliminado por la migración 001 |
| Listas literales en `App.py` (tallas, estados, parentescos) | Importadas de `dominio/validaciones.py` |

## Atributo de calidad que mejora (Semana 8)

* **Mantenibilidad — modificabilidad y capacidad de ser probado:** cambiar una regla
  es cambiar un solo archivo, y las reglas se prueban sin interfaz ni base de datos.
* **Consistencia** (subcaracterística transversal del Entregable 1): la misma operación
  da el mismo resultado sin importar la vía de entrada.

## Consecuencias

* **Positivas:** las reglas quedan documentadas como código y cubiertas por pruebas
  (`tests/test_validaciones.py`, `tests/test_dominio_personas.py`, `tests/test_vinculo_reglas.py`).
* **Cambio de comportamiento deliberado:** ya no se puede desvincular al acudiente principal
  sin antes nombrar otro; antes se permitía y dejaba al menor sin principal.
* **Negativas:** `SP_InsertarJugadorTutor` y los SP de inserción quedan sin uso por el MVP;
  se conservan mientras se valida la migración y se retirarán en la Semana 15.

## Verificación

```bash
python -m pytest tests/test_validaciones.py tests/test_dominio_personas.py tests/test_vinculo_reglas.py -v
```

Búsqueda de duplicados: `grep -rn "XS\", \"S\", \"M\"" src/paladinesfc` solo debe aparecer en
`dominio/validaciones.py` (más la copia del código legado, fuera del MVP).
