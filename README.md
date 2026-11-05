# PaladinesFC — Re-arquitectura del sistema de gestión del club

[![CI](https://github.com/MarianaA27/ClubDeFutbol__/actions/workflows/ci.yml/badge.svg)](https://github.com/MarianaA27/ClubDeFutbol__/actions/workflows/ci.yml)

Trabajo final de **Arquitectura de Sistemas** · Universidad Católica Luis Amigó · Profesor: Fernando Higuita Betancur

**Equipo:** Giany Andrés Salazar Bustamante · Mariana Aguilar Alcaraz · Carlos Daniel Palacios Murillo · Juan Camilo Moreno Pérez

## Descripción

PaladinesFC es una aplicación de escritorio (Python 3 + CustomTkinter + SQL Server)
desarrollada el semestre anterior para la asignatura de Bases de Datos. Reemplazó el
manejo en papel de un club de fútbol formativo: jugadores y sus acudientes, cuerpo
técnico, plantillas, sesiones, pagos y morosidad.

Este repositorio contiene su **re-arquitectura**: se conserva la interfaz y el
comportamiento para la usuaria, se reorganiza el código en capas con
responsabilidades claras y se expone el MVP también como **API REST**, sobre los
mismos servicios.

### Módulo MVP

La re-arquitectura se aplica a **Jugadores, Jugador–Tutor, Tutores y Profesores**
(18 operaciones). El resto de módulos sigue funcionando sobre el código original,
aislado y depurado en `src/paladinesfc/legado/`.

## Problemas arquitectónicos identificados

| Id | Problema | Decisión |
|---|---|---|
| P1 | La interfaz lee los datos por posición (`fila[5]`) y elige tutores por su nombre visible | [ADR-0001](docs/adr/0001-entidades-de-dominio-y-mapeo-por-nombre.md) |
| P2 | Cada sentencia es su propia transacción: las operaciones compuestas pueden quedar a medias | [ADR-0002](docs/adr/0002-unidad-de-trabajo-transaccional.md) |
| P3 | Eliminar un profesor o un jugador borra en cascada sesiones, asistencias y pagos | [ADR-0003](docs/adr/0003-inactivacion-logica.md) |
| P4 | La misma regla de negocio está en varios lugares y otras no se cumplen en ninguno | [ADR-0004](docs/adr/0004-fuente-unica-de-reglas-de-negocio.md) |
| P5 | SQL en la interfaz y búsquedas que descargan tablas completas | [ADR-0005](docs/adr/0005-repositorios-y-filtrado-en-sql.md) |

**Documento final de arquitectura (PDF):** [`docs/Documento_Final_Arquitectura_PaladinesFC.pdf`](docs/Documento_Final_Arquitectura_PaladinesFC.pdf) ·
**Documentación de arquitectura:** [`docs/arquitectura.md`](docs/arquitectura.md)
(arquitectura, componentes, decisiones, escenarios de calidad y refactorización realizada) ·
**Diagramas C4 v2, despliegue y secuencia:** [`docs/diagramas/`](docs/diagramas/) ·
**Evaluación antes/después:** [`docs/evaluacion/`](docs/evaluacion/) ·
**Evidencias de funcionamiento:** [`docs/evidencias/`](docs/evidencias/)

## Arquitectura en una línea

Monolito modular en capas con inversión de dependencias:
**presentación** (escritorio CustomTkinter **o** API FastAPI) → **aplicación** (servicios y
puertos) → **dominio** (entidades y reglas); la **infraestructura** (unidad de trabajo,
repositorios SQL, configuración, bitácora) implementa los puertos. Patrones aplicados:
Unit of Work, Repository, inyección de dependencias con raíz de composición, Adapter
(escritorio y API sobre los mismos servicios), Aggregate y Data Mapper.

## Estructura del repositorio

```
├── .github/workflows/ci.yml   integración continua: pruebas + SQL Server real + mediciones
├── docs/
│   ├── arquitectura.md        arquitectura, componentes, decisiones, escenarios, refactorización realizada
│   ├── adr/                   una decisión de refactorización por archivo
│   ├── diagramas/             C4 v2 (contexto, contenedores, componentes), despliegue y secuencia
│   ├── evaluacion/            caracterización y resultados de las mediciones antes/después
│   ├── evidencias/            capturas del sistema en ejecución y guion del flujo principal
│   └── plan/                  backlog hacia la Semana 15
├── evaluacion/                scripts de medición (E1–E4), copia de la base y protocolo de historial
├── src/
│   ├── paladinesfc/
│   │   ├── presentacion/      interfaz CustomTkinter, API REST (api/) y raíz de composición
│   │   ├── aplicacion/        casos de uso (servicios) y puertos
│   │   ├── dominio/           entidades y reglas de negocio
│   │   ├── infraestructura/   configuración, unidad de trabajo, repositorios, bitácora
│   │   └── legado/            crud.py y db.py de los módulos fuera del MVP
│   └── sql/                   esquema original y migraciones 001–004
├── tests/                     pruebas unitarias y de integración (tests/integracion/)
├── ClubFutbol.spec            empaquetado con PyInstaller
├── config.ini.example
├── requirements.txt
├── run.py                     aplicación de escritorio
└── run_api.py                 API REST
```

## Instalación

### Requisitos

* Windows 10/11 con **Python 3.10 o superior**
* **SQL Server** (Express sirve) y **Microsoft ODBC Driver 17 u 18 for SQL Server**

### Pasos

```bash
# 1. Dependencias
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Base de datos (en SSMS, en este orden; hacer copia de seguridad antes de las migraciones)
#    src/sql/ClubFutbolDB.sql
#    src/sql/migraciones/001_inactivacion_logica.sql
#    src/sql/migraciones/002_eps_jugador.sql
#    src/sql/migraciones/003_retiro_objetos_reemplazados.sql
#    src/sql/migraciones/004_reparar_sp_asignar_jugador_plantilla.sql

# 3. Configuración de la conexión
copy config.ini.example config.ini
#    editar "server" con el nombre de su instancia, p. ej. localhost\SQLEXPRESS
```

Para ensayar las migraciones sin tocar la base del club: `python evaluacion/migrar_copia.py`
(la respalda, la restaura como `ClubFutbolDB_Copia` y migra la copia).

También se puede configurar la conexión con variables de entorno
(`PALADINES_DB_DRIVER`, `PALADINES_DB_SERVER`, `PALADINES_DB_DATABASE`, `PALADINES_DB_TRUSTED`,
`PALADINES_DB_USER`, `PALADINES_DB_PASSWORD`), que tienen prioridad sobre `config.ini`.

## Ejecución

| Qué | Comando | Dónde |
|---|---|---|
| Aplicación de escritorio | `python run.py` | Ventana de PaladinesFC |
| API REST | `python run_api.py` | <http://127.0.0.1:8000> |
| Documentación de la API (Swagger) | con la API en ejecución | <http://127.0.0.1:8000/docs> |
| Documentación alternativa (ReDoc) | con la API en ejecución | <http://127.0.0.1:8000/redoc> |

Los fallos de las operaciones del MVP se registran en `logs/paladinesfc.log`.

## API REST

La API usa **los mismos servicios** que la aplicación de escritorio (misma raíz de
composición), así que aplica las mismas reglas: una transacción por operación, baja
lógica en lugar de borrado y selección de tutores por id. En Swagger (`/docs`) cada
endpoint se puede probar con el botón **Try it out**.

### Endpoints

| Método | Ruta | Descripción | Ejemplo de entrada | Ejemplo de respuesta |
|---|---|---|---|---|
| GET | `/salud` | Comprueba que la API responde | — | `200` `{"estado": "ok"}` |
| GET | `/jugadores?documento=10203` | Lista jugadores con su acudiente principal; `documento` filtra por cédula (en el motor) | — | `200` `[{"id_jugador": 3, "jugador": "Samuel Rojas", "documento": "1020304050", "estado": "activo", "fecha_nacimiento": "2015-05-10", "talla_uniforme": "S", "eps": "Sura", "tutor_principal": "Carlos Pérez", "parentesco": "Padre", "telefono_tutor": "3001111111"}]` |
| POST | `/jugadores` | Registra un jugador y su vínculo con el acudiente principal en una sola transacción | `{"nombres": "Samuel", "apellidos": "Rojas", "documento": "1020304050", "fecha_nacimiento": "2015-05-10", "fecha_ingreso": "2024-02-01", "talla_uniforme": "S", "numero_preferido": 9, "eps": "Sura", "id_tutor": 1, "parentesco": "Padre"}` | `201` `{"id": 3}` |
| GET | `/jugadores/{id_jugador}` | Consulta un jugador | — | `200` `{"id_jugador": 3, "nombres": "Samuel", "apellidos": "Rojas", "documento": "1020304050", "fecha_nacimiento": "2015-05-10", "fecha_ingreso": "2024-02-01", "talla_uniforme": "S", "numero_preferido": 9, "estado": "activo", "observaciones": null, "eps": "Sura"}` |
| GET | `/jugadores/{id_jugador}/detalle` | Jugador, sus tutores y sus plantillas activas | — | `200` `{"jugador": {...}, "tutores": [{"id_jugador_tutor": 4, "id_tutor": 1, "nombre_tutor": "Carlos Pérez", "parentesco": "Padre", "acudiente_principal": true, ...}], "plantillas_activas": []}` |
| PUT | `/jugadores/{id_jugador}` | Edita nombres, talla, estado, número, observaciones y EPS (documento y fechas no cambian) | `{"nombres": "Samuel", "apellidos": "Rojas", "talla_uniforme": "M", "estado": "activo", "numero_preferido": 10, "observaciones": null, "eps": "Sura"}` | `200` jugador actualizado `{"id_jugador": 3, "talla_uniforme": "M", ...}` |
| POST | `/jugadores/{id_jugador}/baja` | Da de baja (estado `inactivo`); conserva pagos, morosidad, asistencias y tutores | — | `200` `{"id_jugador": 3, "estado": "inactivo", ...}` |
| POST | `/jugadores/{id_jugador}/reactivacion` | Reactiva un jugador dado de baja | — | `200` `{"id_jugador": 3, "estado": "activo", ...}` |
| GET | `/jugadores/{id_jugador}/tutores` | Tutores del jugador, el principal primero | — | `200` `[{"id_jugador_tutor": 4, "id_tutor": 1, "nombre_tutor": "Carlos Pérez", "parentesco": "Padre", "acudiente_principal": true, "telefono": "3001111111", "email": "carlos@correo.com"}]` |
| POST | `/jugadores/{id_jugador}/tutores` | Vincula otro tutor | `{"id_tutor": 2, "parentesco": "Madre", "como_principal": false}` | `201` `{"id": 5}` |
| PUT | `/jugadores/{id_jugador}/tutores/principal` | Cambia el acudiente principal (dos escrituras, una transacción) | `{"id_tutor": 2}` | `200` lista de vínculos con `"acudiente_principal": true` solo en el tutor 2 |
| DELETE | `/jugadores/{id_jugador}/tutores/{id_jugador_tutor}` | Desvincula un tutor (no el único ni el principal) | — | `204` sin cuerpo · `400` `{"detalle": "No se puede desvincular al acudiente principal. Primero marque a otro tutor como principal."}` |
| GET | `/tutores?documento=111` | Lista o busca tutores | — | `200` `[{"id_tutor": 1, "nombres": "Carlos", "apellidos": "Pérez", "documento": "11111", "telefono": "3001111111", "email": "carlos@correo.com", "direccion": "Calle 10 # 20-30", "estado": "activo", "etiqueta": "Carlos Pérez — CC 11111"}]` |
| GET | `/tutores/activos` | Tutores activos para listas de selección (la etiqueta distingue homónimos) | — | `200` `[{"id_tutor": 1, "etiqueta": "Carlos Pérez — CC 11111", ...}]` |
| POST | `/tutores` | Registra un tutor | `{"nombres": "Carlos", "apellidos": "Pérez", "documento": "11111", "telefono": "3001111111", "email": "carlos@correo.com", "direccion": "Calle 10 # 20-30"}` | `201` `{"id": 1}` · `400` `{"detalle": "Ya existe un tutor con el documento '11111'."}` |
| GET | `/tutores/{id_tutor}` | Consulta un tutor | — | `200` `{"id_tutor": 1, "nombres": "Carlos", ..., "estado": "activo"}` |
| GET | `/tutores/{id_tutor}/jugadores` | Jugadores a cargo del tutor | — | `200` `[{"id_jugador": 3, "jugador": "Samuel Rojas", "documento": "1020304050", "estado": "activo", "parentesco": "Padre", "acudiente_principal": true}]` |
| PUT | `/tutores/{id_tutor}` | Edita un tutor | mismo cuerpo que `POST /tutores` | `200` tutor actualizado |
| POST | `/tutores/{id_tutor}/baja` | Da de baja un tutor sin jugadores activos a cargo | — | `200` `{"id_tutor": 2, "estado": "inactivo", ...}` · `400` `{"detalle": "No se puede inactivar el tutor porque tiene jugadores activos a cargo."}` |
| GET | `/profesores?documento=800` | Lista o busca profesores | — | `200` `[{"id_profesor": 6, "nombres": "Andrés", "apellidos": "Gómez", "documento": "80001", "telefono": "3101234567", "email": "andres@correo.com", "especialidad": "Técnico", "estado": "activo", "fecha_ingreso": "2023-01-15"}]` |
| GET | `/profesores/activos` | Profesores activos para listas de selección | — | `200` `[{"id_profesor": 6, ...}]` |
| POST | `/profesores` | Registra un profesor | `{"nombres": "Andrés", "apellidos": "Gómez", "documento": "80001", "telefono": "3101234567", "email": "andres@correo.com", "especialidad": "Técnico", "fecha_ingreso": "2023-01-15"}` | `201` `{"id": 6}` |
| GET | `/profesores/{id_profesor}` | Consulta un profesor | — | `200` `{"id_profesor": 6, "nombres": "Andrés", ..., "estado": "activo"}` |
| GET | `/profesores/{id_profesor}/plantillas` | Plantillas a cargo del profesor | — | `200` `[{"id_plantilla": 2, "nombre_plantilla": "Sub-12 A", "estado_plantilla": "activa", "cargo": "Técnico", "fecha_asignacion": "2026-01-25"}]` |
| PUT | `/profesores/{id_profesor}` | Edita un profesor (incluido el documento y el estado) | `{"nombres": "Andrés", "apellidos": "Gómez", "documento": "80001", "telefono": "3101234567", "email": "andres@correo.com", "especialidad": "Preparador físico", "estado": "activo"}` | `200` profesor actualizado |
| POST | `/profesores/{id_profesor}/baja` | Da de baja: sale de los desplegables y conserva sesiones, asistencias y plantillas | — | `200` `{"id_profesor": 6, "estado": "inactivo", ...}` |
| POST | `/profesores/{id_profesor}/reactivacion` | Reactiva un profesor | — | `200` `{"id_profesor": 6, "estado": "activo", ...}` |

### Respuestas de error

| Código | Cuándo | Cuerpo |
|---|---|---|
| `400` | Una regla de negocio no se cumple (documento repetido, formato inválido, desvincular al principal…) | `{"detalle": "mensaje para la usuaria"}` |
| `404` | El registro no existe | `{"detalle": "Jugador no encontrado."}` |
| `422` | El JSON no tiene los campos o tipos esperados (lo valida FastAPI) | `{"detail": [...]}` |
| `503` | No se pudo acceder a la base de datos (queda en la bitácora) | `{"detalle": "No se pudo completar la operación en la base de datos."}` |

## Pruebas

```bash
python -m pytest                 # 119 pruebas, sin SQL Server (dobles en memoria)
python -m pytest --integracion   # + 47 pruebas contra un SQL Server real
python -m pytest --cov=src/paladinesfc/dominio --cov=src/paladinesfc/aplicacion --cov-report=term   # cobertura (E1)
```

* **Unitarias:** dominio, servicios, unidad de trabajo (10 fallos inyectados), repositorios,
  API (`TestClient`), pantallas (prueba de humo) y caracterización de las 18 operaciones.
* **Integración** (`tests/integracion/`): crean una base aparte, `ClubFutbolDB_Pruebas`,
  con el esquema y todas las migraciones, y validan contra el motor real las
  transacciones (E2), la preservación del historial (E3), los repositorios, las
  migraciones y la API. **La base del club no se toca.** Ver
  [`tests/integracion/README.md`](tests/integracion/README.md).
* **Integración continua:** GitHub Actions ejecuta las dos suites en cada push y pull
  request, con SQL Server 2022 en un contenedor, y además las mediciones antes/después
  (pestaña **Actions**).

## Evaluación de los escenarios (antes/después)

| Escenario | Script | Resultado |
|---|---|---|
| E1 Mantenibilidad: agregar el campo EPS | `python evaluacion/medir_e1.py --minutos N` | [`e1-mantenibilidad.md`](docs/evaluacion/e1-mantenibilidad.md) |
| E1 Mantenibilidad: cobertura del dominio y la aplicación (≥ 70 %) | `python -m pytest --cov=src/paladinesfc/dominio --cov=src/paladinesfc/aplicacion` | [`cobertura.md`](docs/evaluacion/cobertura.md) |
| E2 Confiabilidad (estados parciales y tiempo de reversión), E3 Seguridad, E4 Eficiencia | `python evaluacion/medir_escenarios.py` | [`resultados-mediciones.md`](docs/evaluacion/resultados-mediciones.md) |
| E3 protocolo del Entregable 1 (§3.5), con datos de prueba | `python evaluacion/protocolo_historial.py --base ClubFutbolDB_Copia` | [`protocolo-historial.md`](docs/evaluacion/protocolo-historial.md) |
| Las 18 operaciones: qué se conserva y qué cambió | `python -m pytest tests/test_caracterizacion.py -v` | [`caracterizacion.md`](docs/evaluacion/caracterizacion.md) |

Detalles en [`evaluacion/README.md`](evaluacion/README.md).

## Empaquetado

```bash
pip install pyinstaller
pyinstaller ClubFutbol.spec
```

Genera `dist/ClubFutbol.exe` y copia `config.ini.example` a su lado: renómbrelo a
`config.ini` y ajuste el servidor. `config.ini` y `logs/` se buscan junto al `.exe`.

## Estado

| Decisión | Estado |
|---|---|
| ADR-0001 Entidades y mapeo por nombre | Implementada en el MVP (0 lecturas por posición en sus pantallas) |
| ADR-0002 Unidad de trabajo transaccional | Implementada y validada contra SQL Server |
| ADR-0003 Inactivación lógica | Implementada; migraciones 001–004 aplicadas y validadas |
| ADR-0004 Fuente única de reglas | Implementada; procedimientos duplicados retirados (migración 003) |
| ADR-0005 Repositorios con filtrado en SQL | Implementada en el MVP y en la API |
