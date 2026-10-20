"""
Unidad de trabajo transaccional (ADR-0002, problema P2).

En el sistema original ``ejecutar_query()`` abría una conexión, ejecutaba UNA
sentencia, hacía ``commit()`` y cerraba. Una operación de negocio con varias
sentencias (p. ej. cambiar el acudiente principal: dos UPDATE) quedaba partida
en varias transacciones; si fallaba entre ellas, la base quedaba inconsistente.

``UnidadDeTrabajoSql`` agrupa todas las sentencias de una operación de negocio
en UNA conexión y UNA transacción:

    with UnidadDeTrabajoSql() as uow:
        uow.ejecutar("UPDATE ...", (...))
        uow.ejecutar("UPDATE ...", (...))
        uow.commit()            # todo o nada

    # o, con los repositorios del MVP:
    with UnidadDeTrabajoSql() as uow:
        uow.vinculos.establecer_principal(id_jugador, id_tutor)
        uow.commit()

* Si ocurre cualquier excepción dentro del bloque → ``rollback`` automático,
  registro en la bitácora y la excepción se propaga.
* Si el bloque termina sin llamar a ``commit()`` → ``rollback`` (nada se
  persiste por accidente).
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from paladinesfc.infraestructura.bitacora import obtener_bitacora
from paladinesfc.infraestructura.mapeo import fila_a_dict, filas_a_dicts


class UnidadDeTrabajoSql:
    def __init__(self, fabrica_conexion: Callable[[], Any] | None = None,
                 operacion: str = "operación"):
        if fabrica_conexion is None:
            from paladinesfc.infraestructura.conexion import abrir_conexion
            fabrica_conexion = abrir_conexion
        self._fabrica = fabrica_conexion
        self._operacion = operacion
        self._conexion = None
        self._cursor = None
        self._confirmada = False
        self._bitacora = obtener_bitacora()

    # ── ciclo de vida ──────────────────────────────────────────────────────
    def __enter__(self) -> "UnidadDeTrabajoSql":
        self._conexion = self._fabrica()
        self._conexion.autocommit = False
        self._cursor = self._conexion.cursor()
        self._confirmada = False
        self._al_iniciar()
        return self

    def __exit__(self, tipo, excepcion, traza) -> bool:
        try:
            if tipo is not None:
                self._conexion.rollback()
                self._bitacora.error(
                    "Operación '%s' revertida: %s: %s",
                    self._operacion, tipo.__name__, excepcion)
            elif not self._confirmada:
                self._conexion.rollback()
        finally:
            self._conexion.close()
        return False  # nunca se traga la excepción

    def _al_iniciar(self) -> None:
        """Crea los repositorios del MVP sobre ESTA conexión/transacción."""
        from paladinesfc.infraestructura.repositorios import (
            RepositorioJugadoresSql, RepositorioProfesoresSql,
            RepositorioTutoresSql, RepositorioVinculosSql,
        )
        self.jugadores = RepositorioJugadoresSql(self)
        self.tutores = RepositorioTutoresSql(self)
        self.profesores = RepositorioProfesoresSql(self)
        self.vinculos = RepositorioVinculosSql(self)

    # ── transacción ────────────────────────────────────────────────────────
    def commit(self) -> None:
        self._conexion.commit()
        self._confirmada = True

    def rollback(self) -> None:
        self._conexion.rollback()

    # ── acceso a datos (usado por los repositorios) ────────────────────────
    def ejecutar(self, sql: str, parametros: Sequence[Any] = ()) -> int:
        """Ejecuta una sentencia de escritura y devuelve las filas afectadas."""
        if parametros:
            self._cursor.execute(sql, tuple(parametros))
        else:
            self._cursor.execute(sql)
        return self._cursor.rowcount

    def consultar(self, sql: str, parametros: Sequence[Any] = ()) -> list[dict]:
        if parametros:
            self._cursor.execute(sql, tuple(parametros))
        else:
            self._cursor.execute(sql)
        return filas_a_dicts(self._cursor)

    def consultar_uno(self, sql: str, parametros: Sequence[Any] = ()) -> dict | None:
        if parametros:
            self._cursor.execute(sql, tuple(parametros))
        else:
            self._cursor.execute(sql)
        return fila_a_dict(self._cursor)

    def insertar(self, sql: str, parametros: Sequence[Any] = ()) -> int:
        """Ejecuta un INSERT y devuelve el identificador generado.

        Se usa ``SCOPE_IDENTITY()`` en el mismo lote: ``@@IDENTITY`` devolvería el
        id de MOROSIDAD que inserta el trigger ``TR_NuevoJugador_Morosidad``, y una
        cláusula OUTPUT sin INTO no se permite en tablas con triggers.
        """
        lote = f"SET NOCOUNT ON; {sql}; SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;"
        self._cursor.execute(lote, tuple(parametros))
        while self._cursor.description is None and self._cursor.nextset():
            pass
        fila = self._cursor.fetchone()
        if fila is None or fila[0] is None:
            raise RuntimeError("No se pudo obtener el identificador del registro insertado.")
        return int(fila[0])

    def escalar(self, sql: str, parametros: Sequence[Any] = ()):
        fila = self.consultar_uno(sql, parametros)
        return None if fila is None else next(iter(fila.values()))
