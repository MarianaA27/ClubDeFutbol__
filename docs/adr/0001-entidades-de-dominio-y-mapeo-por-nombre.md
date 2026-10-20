# ADR-0001: Entidades de dominio y mapeo por nombre de columna

* **Estado:** Implementada en el MVP
* **Fecha:** 2026-10-19
* **Responsable:** Mariana Aguilar Alcaraz

## Contexto y problema (Semana 3 — P1: contrato posicional entre capas)

Todas las funciones de `crud.py` devuelven la tupla `(columnas, filas)` y la interfaz
lee cada dato **por su posición**: `FormJugador._cargar_datos` usa `j[1]`, `j[5]`, `j[8]`, `j[9]`;
`VentanaDetalleJugador` decide quién es el acudiente principal con `r[6]`; `FormTutor._cargar`
toma el documento de `r[3]`. Además, los desplegables buscan el identificador comparando el
**texto visible**: `next((r[0] for r in self._tutores_data if str(r[1]) == tutor_txt), None)`.

El defecto ya se manifiesta en el sistema actual:

* "Ver detalle" de **Tutores** y **Profesores**: `VW_DetalleTutor` y `VW_DetalleProfesor`
  devuelven 6 columnas y la tabla tiene 5 encabezados; cada dato aparece bajo el encabezado
  equivocado (bajo "Tutor" se ve el id, bajo "Teléfono" el nombre…).
* Con dos tutores homónimos, el jugador queda vinculado al primero de la lista, no al elegido.

## Decisión

1. Los datos viajan entre capas como **entidades de dominio** (`Jugador`, `Tutor`, `Profesor`,
   `VinculoTutor`) o, en listados, como **diccionarios indexados por nombre de columna**.
2. La infraestructura convierte cada fila con `filas_a_dicts()` usando `cursor.description`;
   el orden de las columnas de la consulta deja de importar.
3. Los desplegables guardan un diccionario `etiqueta → id`; la etiqueta incluye el documento
   (`"Carlos Pérez — CC 22222"`), de modo que los homónimos se distinguen y la selección
   siempre se resuelve por clave primaria.
4. Las pantallas asocian cada fila del `Treeview` con su objeto (`_mapa_items`) en lugar de
   releer IDs por posición.

## Código afectado

| Antes (sistema original) | Después (`src/`) |
|---|---|
| `crud.py`: funciones `get_*` del MVP devuelven tuplas | `infraestructura/mapeo.py`, `infraestructura/repositorios/*.py` |
| — (no existían entidades) | `dominio/jugador.py`, `dominio/tutor.py`, `dominio/profesor.py`, `dominio/vinculo.py` |
| `App.py`: `FormJugador`, `VentanaDetalleJugador`, `FormVincularTutor`, `FormTutor`, `FormProfesor`, `TabTutores._ver_detalle`, `TabProfesores._ver_detalle` | `presentacion/app.py` (mismas clases, ahora leen atributos por nombre) |
| `App.py`: `FormAsignarProfesorPlantilla` (resolución por nombre) | `presentacion/app.py` (usa `ProfesorService.opciones()` y resuelve por id) |
| `VW_DetalleTutor`, `VW_DetalleProfesor` | `RepositorioTutoresSql.jugadores_a_cargo()`, `RepositorioProfesoresSql.plantillas_a_cargo()` |

## Atributo de calidad que mejora (Semana 8)

* **Mantenibilidad — modificabilidad.** Agregar o reordenar columnas ya no desplaza datos
  en la interfaz (escenario E1).
* **Seguridad — integridad.** Un menor no puede quedar vinculado al acudiente equivocado
  por un homónimo.

## Consecuencias

* **Positivas:** errores de lectura silenciosos pasan a ser imposibles o fallan con
  `KeyError` explícito; las entidades son reutilizables por los módulos que se migren después.
* **Negativas:** los módulos legados (plantillas, sesiones, finanzas) siguen con tuplas
  hasta su migración; conviven dos estilos durante la transición.

## Verificación

* `tests/test_mapeo.py::test_reordenar_columnas_no_cambia_el_valor_leido`
* `tests/test_servicios.py::test_homonimos_se_resuelven_por_id`
* `tests/test_presentacion_humo.py::test_flujo_completo_del_mvp_desde_las_pantallas`
  (registra un jugador eligiendo al **segundo** de dos tutores homónimos y comprueba el vínculo).
