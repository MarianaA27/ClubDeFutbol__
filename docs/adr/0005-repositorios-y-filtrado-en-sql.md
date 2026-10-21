# ADR-0005: Repositorios con filtrado en SQL y sin SQL en la interfaz

* **Estado:** Implementada en el MVP
* **Fecha:** 2026-10-19
* **Responsable:** Carlos Daniel Palacios Murillo

## Contexto y problema (Semana 3 — P5: violación de capas y consultas ineficientes)

* **Capa saltada:** `PanelGestionPlantilla._quitar_jugador()` ejecuta un `DELETE` escrito a
  mano con `crud.ejecutar_query()` desde la presentación.
* **Filtrado en memoria:** las búsquedas por cédula de `TabJugadores`, `TabTutores` y
  `TabProfesores` traen la tabla completa y filtran con una comprensión de lista; `FormTutor._cargar`
  y `FormProfesor._cargar` descargan toda la tabla para editar un solo registro. Mientras
  tanto, `crud.buscar_tutores()` ya filtraba en SQL… pero nunca se usaba.
* **Conexiones paralelas:** `crud.crear_sesion()` y `crud.get_datos_dashboard()` abren su
  propia conexión, así que `db.py` no es el único punto de acceso.
* **Código muerto:** 14 funciones de `crud.py` no se llaman desde ninguna pantalla (entre
  ellas `get_tutores_de_jugador()`); `guardar_alineacion()` y `get_alineacion()` están
  definidas dos veces.

## Decisión

1. Cada entidad del MVP tiene un **repositorio** (`infraestructura/repositorios/`) que es
   el único lugar con SQL para esa entidad. La interfaz nunca contiene SQL.
2. Todo filtro se resuelve **en el motor** con `WHERE` parametrizado:
   * búsqueda por cédula → `WHERE documento LIKE ?`;
   * edición → `obtener(id)` con `WHERE id_x = ?` (una fila);
   * listas de selección → `WHERE estado = 'activo'`.
3. Los repositorios trabajan sobre la conexión de la unidad de trabajo (ADR-0002); no
   abren conexiones propias.
4. Para los módulos **fuera del MVP**, el `DELETE` de la presentación se mueve a
   `legado/crud.py` (`quitar_jugador_de_alineacion`), de modo que ninguna pantalla ejecuta SQL.

## Código afectado

| Antes (sistema original) | Después (`src/`) |
|---|---|
| `App.py`: `TabJugadores._buscar`, `TabTutores._buscar`, `TabProfesores._buscar` | `RepositorioJugadoresSql.listar_con_tutor_principal(documento)`, `RepositorioTutoresSql.listar(documento)`, `RepositorioProfesoresSql.listar(documento)` |
| `App.py`: `FormTutor._cargar`, `FormProfesor._cargar` (tabla completa) | `TutorService.obtener(id)`, `ProfesorService.obtener(id)` |
| `crud.py`: `get_jugadores_con_tutor`, `get_tutores`, `get_profesores`, `get_detalle_jugador_completo`, `get_tutores_de_jugador` | `infraestructura/repositorios/{jugadores,tutores,profesores,vinculos}.py` |
| `App.py`: `PanelGestionPlantilla._quitar_jugador` (`crud.ejecutar_query` con DELETE) | `legado/crud.py: quitar_jugador_de_alineacion()` |

## Atributo de calidad que mejora (Semana 8)

* **Mantenibilidad — modularidad:** toda la escritura y lectura del MVP pasa por un punto
  conocido; es posible aplicar controles transversales.
* **Eficiencia de ejecución — comportamiento temporal y uso de recursos:** los datos
  transferidos ya no crecen con el tamaño de las tablas en búsquedas y ediciones (escenario E4).

## Consecuencias

* **Positivas:** el motor usa sus índices (`documento` es `UNIQUE`); la interfaz se
  congela menos tiempo en el hilo principal.
* **Negativas:** los módulos legados siguen filtrando en memoria (p. ej.
  `FormAsignarJugadorPlantilla._obtener_id_categoria`); quedan registrados en el tablero.

## Verificación

* `tests/test_repositorios.py::test_busqueda_de_jugador_por_documento_usa_where_en_el_motor`
* `tests/test_repositorios.py::test_obtener_profesor_mapea_por_nombre_y_trae_una_sola_fila`
* `tests/test_repositorios.py::test_listar_profesores_activos_filtra_en_sql`
* `grep -n "ejecutar_query" src/paladinesfc/presentacion/app.py` → sin resultados.
