# PaladinesFC — Re-arquitectura del sistema de gestión del club

Trabajo final de **Arquitectura de Sistemas** · Universidad Católica Luis Amigó · Profesor: Fernando Higuita Betancur

**Equipo:** Giany Andrés Salazar Bustamante · Mariana Aguilar Alcaraz · Carlos Daniel Palacios Murillo · Juan Camilo Moreno Pérez

## Descripción

PaladinesFC es una aplicación de escritorio (Python 3 + CustomTkinter + SQL Server)
desarrollada el semestre anterior para la asignatura de Bases de Datos. Reemplazó el
manejo en papel de un club de fútbol formativo: jugadores y sus acudientes, cuerpo
técnico, plantillas, sesiones, pagos y morosidad.

Este repositorio contiene su **re-arquitectura**: se conserva la interfaz y el
comportamiento para la usuaria, y se reorganiza el código en capas con
responsabilidades claras.

### Módulo MVP

La re-arquitectura se aplica a **Jugadores, Jugador–Tutor, Tutores y Profesores**
(18 operaciones). El resto de módulos sigue funcionando sobre el código original,
aislado en `src/paladinesfc/legado/`.

## Problemas arquitectónicos identificados

| Id | Problema | Decisión |
|---|---|---|
| P1 | La interfaz lee los datos por posición (`fila[5]`) y elige tutores por su nombre visible | [ADR-0001](docs/adr/0001-entidades-de-dominio-y-mapeo-por-nombre.md) |
| P2 | Cada sentencia es su propia transacción: las operaciones compuestas pueden quedar a medias | [ADR-0002](docs/adr/0002-unidad-de-trabajo-transaccional.md) |
| P3 | Eliminar un profesor o un jugador borra en cascada sesiones, asistencias y pagos | [ADR-0003](docs/adr/0003-inactivacion-logica.md) |
| P4 | La misma regla de negocio está en varios lugares y otras no se cumplen en ninguno | [ADR-0004](docs/adr/0004-fuente-unica-de-reglas-de-negocio.md) |
| P5 | SQL en la interfaz y búsquedas que descargan tablas completas | [ADR-0005](docs/adr/0005-repositorios-y-filtrado-en-sql.md) |

**Documentación de arquitectura:** [`docs/arquitectura.md`](docs/arquitectura.md)
(arquitectura objetivo, componentes, decisiones y escenarios de calidad) ·
**Diagramas C4:** [`docs/diagramas/`](docs/diagramas/)

## Estructura del repositorio

```
├── docs/
│   ├── arquitectura.md        arquitectura objetivo, componentes, decisiones, escenarios
│   ├── adr/                   una decisión de refactorización por archivo
│   ├── diagramas/             C4 (contexto, contenedores, componentes) y despliegue
│   └── plan/                  backlog hacia la Semana 15
├── src/
│   ├── paladinesfc/
│   │   ├── presentacion/      interfaz CustomTkinter + raíz de composición
│   │   ├── aplicacion/        casos de uso (servicios) y puertos
│   │   ├── dominio/           entidades y reglas de negocio
│   │   ├── infraestructura/   configuración, unidad de trabajo, repositorios, bitácora
│   │   └── legado/            crud.py y db.py originales (módulos fuera del MVP)
│   └── sql/                   esquema original y migraciones
├── tests/                     pruebas automáticas (no requieren SQL Server)
├── config.ini.example
├── requirements.txt
└── run.py
```

## Ejecución

### Requisitos

* Windows 10/11 con **Python 3.10 o superior**
* **SQL Server** (Express sirve) y **Microsoft ODBC Driver 17 for SQL Server**

### Pasos

```bash
# 1. Dependencias
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Base de datos (en SSMS, en este orden)
#    src/sql/ClubFutbolDB.sql
#    src/sql/migraciones/001_inactivacion_logica.sql   (hacer copia de seguridad antes)

# 3. Configuración de la conexión
copy config.ini.example config.ini
#    editar "server" con el nombre de su instancia, p. ej. localhost\SQLEXPRESS

# 4. Ejecutar
python run.py
```

También se puede configurar la conexión con variables de entorno
(`PALADINES_DB_SERVER`, `PALADINES_DB_DATABASE`, `PALADINES_DB_TRUSTED`,
`PALADINES_DB_USER`, `PALADINES_DB_PASSWORD`), que tienen prioridad sobre `config.ini`.

Los fallos de las operaciones del MVP se registran en `logs/paladinesfc.log`.

### Pruebas

```bash
python -m pytest
```

Las 75 pruebas usan dobles en memoria, así que corren en cualquier equipo, sin SQL
Server ni pantalla. Entre ellas está la verificación del escenario de Confiabilidad:
10 fallos inyectados a mitad de "cambiar acudiente principal" sin estados parciales
(`tests/test_unidad_trabajo.py`).

## Estado

| Decisión | Estado |
|---|---|
| ADR-0001 Entidades y mapeo por nombre | Implementada en el MVP |
| ADR-0002 Unidad de trabajo transaccional | Implementada y probada |
| ADR-0003 Inactivación lógica | Implementada; migración 001 lista para aplicar |
| ADR-0004 Fuente única de reglas | Implementada en el MVP |
| ADR-0005 Repositorios con filtrado en SQL | Implementada en el MVP |

Tareas pendientes hacia la Semana 15: [`docs/plan/backlog-semana-15.md`](docs/plan/backlog-semana-15.md).
