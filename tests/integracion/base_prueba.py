"""
Base de datos de prueba en un SQL Server REAL (retroalimentación del Entregable 3).

Crea una base aislada (por defecto ``ClubFutbolDB_Pruebas``) con el mismo esquema
que usa el club —``src/sql/ClubFutbolDB.sql``— más todas las migraciones de
``src/sql/migraciones/`` en orden. Nunca toca la base real: el nombre debe empezar
por ``ClubFutbolDB_`` y ser distinto de la base configurada para la aplicación.

Lo usan las pruebas de ``tests/integracion/`` y los scripts de ``evaluacion/``.

Configuración: la misma de la aplicación (``config.ini`` o variables
``PALADINES_DB_*``); solo cambia el nombre de la base, que se toma de
``PALADINES_TEST_DATABASE`` o del argumento ``nombre``.
"""
from __future__ import annotations

import os
import re
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

from paladinesfc.infraestructura.config import ConfigBD, cargar_config

RAIZ = Path(__file__).resolve().parents[2]
CARPETA_SQL = RAIZ / "src" / "sql"
ESQUEMA = CARPETA_SQL / "ClubFutbolDB.sql"
CARPETA_MIGRACIONES = CARPETA_SQL / "migraciones"

NOMBRE_POR_DEFECTO = "ClubFutbolDB_Pruebas"
_NOMBRE_VALIDO = re.compile(r"^ClubFutbolDB_[A-Za-z0-9_]+$")

# Orden de borrado que respeta las llaves foráneas del esquema.
_TABLAS_EN_ORDEN_DE_BORRADO = (
    "SESION_JUGADOR", "PLANTILLA_ALINEACION", "SESION", "PLANTILLA_JUGADOR",
    "PLANTILLA_PROFESOR", "PAGO", "MOROSIDAD", "JUGADOR_TUTOR", "PLANTILLA",
    "CATEGORIA", "CANCHA", "CONCEPTO_PAGO", "JUGADOR", "TUTOR", "PROFESOR",
)


def _pyodbc():
    import pyodbc
    # Sin pool: una conexión "matada" en una prueba no debe reutilizarse en la siguiente.
    pyodbc.pooling = False
    return pyodbc


# ── configuración ──────────────────────────────────────────────────────────
def config_prueba(nombre: str | None = None) -> ConfigBD:
    """Configuración de la aplicación apuntando a la base de prueba."""
    nombre = nombre or os.environ.get("PALADINES_TEST_DATABASE") or NOMBRE_POR_DEFECTO
    app = cargar_config()
    if not _NOMBRE_VALIDO.match(nombre) or nombre.lower() == app.database.lower():
        raise ValueError(
            f"Nombre de base de prueba no permitido: '{nombre}'. Debe empezar por "
            "'ClubFutbolDB_' y ser distinto de la base de la aplicación.")
    return replace(app, database=nombre)


def conectar(cfg: ConfigBD, autocommit: bool = False):
    return _pyodbc().connect(cfg.cadena(), autocommit=autocommit)


# ── scripts SQL ────────────────────────────────────────────────────────────
_RE_GO = re.compile(r"^\s*GO\s*;?\s*$", re.IGNORECASE | re.MULTILINE)
_RE_COMENTARIO_BLOQUE = re.compile(r"/\*.*?\*/", re.DOTALL)
_RE_COMENTARIO_LINEA = re.compile(r"--[^\n]*")
_RE_CAMBIO_DE_BASE = re.compile(r"^\s*(CREATE\s+DATABASE|USE)\b", re.IGNORECASE)


def _sin_comentarios(lote: str) -> str:
    return _RE_COMENTARIO_LINEA.sub("", _RE_COMENTARIO_BLOQUE.sub("", lote)).strip()


def lotes_de(ruta: Path) -> list[str]:
    """Divide un script de SSMS en lotes (separador GO).

    Se omiten los lotes vacíos y los que crean o seleccionan la base
    (``CREATE DATABASE`` / ``USE``): la conexión ya apunta a la base de prueba.
    """
    texto = ruta.read_text(encoding="utf-8-sig")
    lotes = []
    for lote in _RE_GO.split(texto):
        limpio = _sin_comentarios(lote)
        if not limpio or _RE_CAMBIO_DE_BASE.match(limpio):
            continue
        lotes.append(lote.strip())
    return lotes


def migraciones() -> list[Path]:
    return sorted(CARPETA_MIGRACIONES.glob("[0-9][0-9][0-9]_*.sql"))


def ejecutar_script(cfg: ConfigBD, ruta: Path) -> int:
    con = conectar(cfg, autocommit=True)
    try:
        cursor = con.cursor()
        for lote in lotes_de(ruta):
            cursor.execute(lote)
            while cursor.nextset():   # consume los resultados de SELECT de verificación
                pass
        return len(lotes_de(ruta))
    finally:
        con.close()


# ── ciclo de vida de la base ───────────────────────────────────────────────
def eliminar_base(cfg: ConfigBD) -> None:
    nombre = cfg.database
    if not _NOMBRE_VALIDO.match(nombre):
        raise ValueError(f"No se elimina '{nombre}': no es una base de prueba.")
    con = conectar(replace(cfg, database="master"), autocommit=True)
    try:
        con.cursor().execute(
            f"IF DB_ID(N'{nombre}') IS NOT NULL "
            f"BEGIN ALTER DATABASE [{nombre}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
            f"DROP DATABASE [{nombre}]; END")
    finally:
        con.close()


def crear_base(cfg: ConfigBD, con_migraciones: bool = True) -> list[str]:
    """Crea (o recrea) la base de prueba con el esquema del club y, opcionalmente, las migraciones.

    Devuelve la lista de scripts aplicados, en orden.
    """
    eliminar_base(cfg)
    con = conectar(replace(cfg, database="master"), autocommit=True)
    try:
        con.cursor().execute(f"CREATE DATABASE [{cfg.database}]")
    finally:
        con.close()
    aplicados = [ESQUEMA]
    ejecutar_script(cfg, ESQUEMA)
    if con_migraciones:
        for migracion in migraciones():
            ejecutar_script(cfg, migracion)
            aplicados.append(migracion)
    return [p.name for p in aplicados]


def limpiar(cfg: ConfigBD) -> None:
    """Vacía todas las tablas (entre pruebas) sin recrear la base."""
    con = conectar(cfg, autocommit=True)
    try:
        cursor = con.cursor()
        for tabla in _TABLAS_EN_ORDEN_DE_BORRADO:
            cursor.execute(f"DELETE FROM {tabla}")
    finally:
        con.close()


# ── servicios de la aplicación sobre la base de prueba ─────────────────────
def fabrica_uow(cfg: ConfigBD, fabrica_conexion=None):
    """Fábrica de unidades de trabajo REALES (UnidadDeTrabajoSql + pyodbc) sobre la base de prueba."""
    from paladinesfc.infraestructura.unidad_trabajo import UnidadDeTrabajoSql
    fabrica_conexion = fabrica_conexion or (lambda: conectar(cfg))
    return lambda operacion: UnidadDeTrabajoSql(fabrica_conexion, operacion)


def servicios(cfg: ConfigBD, fabrica_conexion=None):
    from paladinesfc.presentacion.contenedor import crear_servicios
    return crear_servicios(fabrica_uow(cfg, fabrica_conexion))


# ── inyección de fallos sobre una conexión REAL ────────────────────────────
class ConexionPerdida(Exception):
    """Simula la caída de la conexión justo antes de enviar una sentencia."""


class _CursorConFallo:
    def __init__(self, real, conexion):
        self._real, self._conexion = real, conexion

    def execute(self, sql, *parametros):
        if self._conexion.patron in sql:
            raise ConexionPerdida("Conexión perdida antes de enviar: " + " ".join(sql.split())[:60])
        self._conexion.enviadas.append(" ".join(sql.split()))
        self._real.execute(sql, *parametros)
        return self

    def __getattr__(self, nombre):
        return getattr(self._real, nombre)


class ConexionConFallo:
    """Conexión pyodbc real que falla al intentar enviar la sentencia que contiene ``patron``.

    Todo lo anterior SÍ llega a SQL Server (queda en ``enviadas``); así se comprueba que
    la reversión deshace sentencias que el motor realmente ejecutó.
    """

    def __init__(self, real, patron="SET acudiente_principal = 1"):
        self._real, self.patron, self.enviadas = real, patron, []

    @property
    def autocommit(self):
        return self._real.autocommit

    @autocommit.setter
    def autocommit(self, valor):
        self._real.autocommit = valor

    def cursor(self):
        return _CursorConFallo(self._real.cursor(), self)

    def commit(self):
        self._real.commit()

    def rollback(self):
        self._real.rollback()

    def close(self):
        self._real.close()


# ── consultas de verificación (por fuera del código que se prueba) ─────────
def escalar(cfg: ConfigBD, sql: str, parametros=()):
    con = conectar(cfg, autocommit=True)
    try:
        fila = con.cursor().execute(sql, parametros).fetchone()
        return None if fila is None else fila[0]
    finally:
        con.close()


def contar(cfg: ConfigBD, tabla: str, donde: str = "", parametros=()) -> int:
    sql = f"SELECT COUNT(*) FROM {tabla}" + (f" WHERE {donde}" if donde else "")
    return int(escalar(cfg, sql, parametros))


def principales_de(cfg: ConfigBD, id_jugador: int) -> list[int]:
    con = conectar(cfg, autocommit=True)
    try:
        filas = con.cursor().execute(
            "SELECT id_tutor FROM JUGADOR_TUTOR WHERE id_jugador = ? AND acudiente_principal = 1",
            (id_jugador,)).fetchall()
        return [f[0] for f in filas]
    finally:
        con.close()


# ── siembra de datos de prueba con SQL directo ─────────────────────────────
class Siembra:
    """Inserta datos de prueba con SQL directo, sin pasar por el código que se prueba."""

    def __init__(self, cfg: ConfigBD):
        self.cfg = cfg
        self._con = conectar(cfg, autocommit=True)
        self._cur = self._con.cursor()
        self._n = 0

    def cerrar(self) -> None:
        self._con.close()

    def _sec(self) -> int:
        self._n += 1
        return self._n

    def _insertar(self, sql: str, parametros) -> int:
        self._cur.execute(f"SET NOCOUNT ON; {sql}; SELECT CAST(SCOPE_IDENTITY() AS INT);", parametros)
        while self._cur.description is None and self._cur.nextset():
            pass
        return int(self._cur.fetchone()[0])

    def ejecutar(self, sql: str, parametros=()) -> None:
        self._cur.execute(sql, parametros)

    # personas
    def tutor(self, nombres="Carlos", apellidos="Pérez", documento=None, telefono=None) -> int:
        n = self._sec()
        return self._insertar(
            "INSERT INTO TUTOR (nombres, apellidos, documento, telefono, email, direccion) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (nombres, apellidos, documento or f"{70000 + n}", telefono or f"300{1000000 + n}",
             f"tutor{n}@correo.com", "Calle 1 # 2-3"))

    def jugador(self, nombres="Samuel", apellidos="Rojas", documento=None, estado="activo") -> int:
        n = self._sec()
        return self._insertar(
            "INSERT INTO JUGADOR (nombres, apellidos, documento, fecha_nacimiento, numero_preferido, "
            "talla_uniforme, estado, fecha_ingreso, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (nombres, apellidos, documento or f"{1020300000 + n}", date(2014, 5, 10), 9, "S",
             estado, date(2024, 2, 1), None))

    def vinculo(self, id_jugador: int, id_tutor: int, principal: bool, parentesco="Padre") -> int:
        return self._insertar(
            "INSERT INTO JUGADOR_TUTOR (id_jugador, id_tutor, parentesco, acudiente_principal) "
            "VALUES (?, ?, ?, ?)", (id_jugador, id_tutor, parentesco, 1 if principal else 0))

    def profesor(self, nombres="Andrés", apellidos="Gómez", documento=None, telefono=None,
                 estado="activo") -> int:
        n = self._sec()
        return self._insertar(
            "INSERT INTO PROFESOR (nombres, apellidos, documento, telefono, email, especialidad, "
            "estado, fecha_ingreso) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (nombres, apellidos, documento or f"{80000 + n}", telefono or f"310{1000000 + n}",
             f"profe{n}@correo.com", "Técnico", estado, date(2023, 1, 15)))

    # estructura deportiva
    def categoria(self) -> int:
        return self._insertar(
            "INSERT INTO CATEGORIA (nombre_categoria, anio_minimo, anio_maximo, estado, descripcion) "
            "VALUES (?, ?, ?, 'activa', NULL)", (f"Sub-12 {self._sec()}", 2013, 2015))

    def plantilla(self, id_categoria: int, estado="activa") -> int:
        return self._insertar(
            "INSERT INTO PLANTILLA (nombre_plantilla, id_categoria, fecha_creacion, temporada, estado) "
            "VALUES (?, ?, ?, '2026', ?)", (f"Plantilla {self._sec()}", id_categoria, date(2026, 1, 20), estado))

    def cancha(self) -> int:
        return self._insertar(
            "INSERT INTO CANCHA (nombre_cancha, direccion, tipo_superficie, capacidad, estado) "
            "VALUES (?, 'Cra 1', 'Sintética', 22, 'disponible')", (f"Cancha {self._sec()}",))

    def sesion(self, id_profesor, id_cancha, id_categoria, id_plantilla, dia=1) -> int:
        return self._insertar(
            "INSERT INTO SESION (fecha_sesion, id_profesor, id_cancha, id_categoria, id_plantilla, "
            "observaciones, tipo_sesion, estado) VALUES (?, ?, ?, ?, ?, NULL, 'Partido', 'realizada')",
            (datetime(2026, 3, min(dia, 28), 15, 0), id_profesor, id_cancha, id_categoria, id_plantilla))

    def asistencia(self, id_sesion, id_jugador, asistio=True) -> int:
        return self._insertar(
            "INSERT INTO SESION_JUGADOR (id_sesion, id_jugador, asistencia, convocado, numero_camiseta) "
            "VALUES (?, ?, ?, 1, NULL)", (id_sesion, id_jugador, 1 if asistio else 0))

    def plantilla_profesor(self, id_plantilla, id_profesor, cargo="Técnico") -> int:
        return self._insertar(
            "INSERT INTO PLANTILLA_PROFESOR (id_plantilla, id_profesor, fecha_asignacion, cargo) "
            "VALUES (?, ?, ?, ?)", (id_plantilla, id_profesor, date(2026, 1, 25), cargo))

    def plantilla_jugador(self, id_plantilla, id_jugador, estado="activo") -> int:
        return self._insertar(
            "INSERT INTO PLANTILLA_JUGADOR (id_plantilla, id_jugador, fecha_asignacion, estado) "
            "VALUES (?, ?, ?, ?)", (id_plantilla, id_jugador, date(2026, 1, 25), estado))

    # finanzas
    def concepto(self, nombre="Mensualidad") -> int:
        return self._insertar(
            "INSERT INTO CONCEPTO_PAGO (nombre_concepto, descripcion, valor_base, eliminable, estado) "
            "VALUES (?, NULL, 80000, 0, 'activo')", (f"{nombre} {self._sec()}",))

    def morosidad_de(self, id_jugador: int) -> int:
        """La crea el trigger TR_NuevoJugador_Morosidad al insertar el jugador."""
        self._cur.execute("SELECT MIN(id_morosidad) FROM MOROSIDAD WHERE id_jugador = ?", (id_jugador,))
        return int(self._cur.fetchone()[0])

    def pago(self, id_jugador, id_concepto, id_morosidad=None, mes=2) -> int:
        return self._insertar(
            "INSERT INTO PAGO (id_jugador, id_concepto, id_morosidad, fecha_pago, fecha_expiracion, "
            "valor_pagado, metodo_pago, observaciones) VALUES (?, ?, ?, ?, ?, 80000, 'Efectivo', NULL)",
            (id_jugador, id_concepto, id_morosidad, date(2026, mes, 5), date(2026, mes + 1, 5)))

    # escenarios completos
    def jugador_con_dos_tutores(self):
        """Jugador con su acudiente principal (t1) y un segundo tutor (t2)."""
        t1 = self.tutor("Carlos", "Pérez")
        t2 = self.tutor("Laura", "Gómez")
        j = self.jugador()
        self.vinculo(j, t1, principal=True, parentesco="Padre")
        self.vinculo(j, t2, principal=False, parentesco="Madre")
        return j, t1, t2

    def profesor_con_historial(self, sesiones=12, plantillas=2, jugadores=3):
        """Escenario E3 de la Semana 8: profesor con 12 sesiones con asistencia y 2 plantillas."""
        id_profesor = self.profesor()
        id_cat = self.categoria()
        id_cancha = self.cancha()
        ids_plantillas = [self.plantilla(id_cat) for _ in range(plantillas)]
        for id_pl in ids_plantillas:
            self.plantilla_profesor(id_pl, id_profesor)
        ids_jugadores = [self.jugador(nombres="Jugador", apellidos=f"Historial {k}") for k in range(jugadores)]
        for d in range(sesiones):
            id_s = self.sesion(id_profesor, id_cancha, id_cat, ids_plantillas[d % plantillas], dia=d + 1)
            for id_j in ids_jugadores:
                self.asistencia(id_s, id_j, asistio=(d + id_j) % 4 != 0)
        return id_profesor, ids_plantillas, ids_jugadores
