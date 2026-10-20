"""Repositorio de jugadores."""
from __future__ import annotations

from paladinesfc.dominio.jugador import Jugador
from paladinesfc.infraestructura.repositorios._base import RepositorioBase

_COLUMNAS = """id_jugador, nombres, apellidos, documento, fecha_nacimiento,
               numero_preferido, talla_uniforme, estado, fecha_ingreso, observaciones"""


class RepositorioJugadoresSql(RepositorioBase):

    def obtener(self, id_jugador: int) -> Jugador | None:
        fila = self._uow.consultar_uno(
            f"SELECT {_COLUMNAS} FROM JUGADOR WHERE id_jugador = ?", (int(id_jugador),))
        return Jugador.desde_bd(fila) if fila else None

    def existe_documento(self, documento: str, excluir_id: int | None = None) -> bool:
        return self._existe("JUGADOR", "documento", documento, "id_jugador", excluir_id)

    def listar_con_tutor_principal(self, documento: str | None = None) -> list[dict]:
        """Listado de la pestaña Jugadores. La búsqueda por cédula se filtra en el motor."""
        sql = """
        SELECT j.id_jugador,
               j.nombres + ' ' + j.apellidos                       AS jugador,
               j.documento, j.estado, j.fecha_nacimiento, j.talla_uniforme,
               ISNULL(t.nombres + ' ' + t.apellidos, 'Sin tutor')  AS tutor_principal,
               ISNULL(jt.parentesco, '-')                           AS parentesco,
               ISNULL(t.telefono, '-')                              AS telefono_tutor
        FROM JUGADOR j
        LEFT JOIN JUGADOR_TUTOR jt ON jt.id_jugador = j.id_jugador AND jt.acudiente_principal = 1
        LEFT JOIN TUTOR t          ON t.id_tutor = jt.id_tutor
        """
        parametros: list = []
        if documento and documento.strip():
            sql += " WHERE j.documento LIKE ?"
            parametros.append(f"%{documento.strip()}%")
        sql += " ORDER BY j.apellidos, j.nombres"
        return self._uow.consultar(sql, parametros)

    def agregar(self, jugador: Jugador) -> int:
        id_nuevo = self._uow.insertar(
            """INSERT INTO JUGADOR (nombres, apellidos, documento, fecha_nacimiento,
                                    numero_preferido, talla_uniforme, estado,
                                    fecha_ingreso, observaciones)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (jugador.nombres, jugador.apellidos, jugador.documento,
             jugador.fecha_nacimiento, jugador.numero_preferido, jugador.talla_uniforme,
             jugador.estado, jugador.fecha_ingreso, jugador.observaciones))
        jugador.id_jugador = id_nuevo
        return id_nuevo

    def actualizar(self, jugador: Jugador) -> None:
        self._uow.ejecutar(
            """UPDATE JUGADOR
               SET nombres = ?, apellidos = ?, numero_preferido = ?,
                   talla_uniforme = ?, estado = ?, observaciones = ?
               WHERE id_jugador = ?""",
            (jugador.nombres, jugador.apellidos, jugador.numero_preferido,
             jugador.talla_uniforme, jugador.estado, jugador.observaciones,
             int(jugador.id_jugador)))

    def contar_plantillas_activas(self, id_jugador: int) -> int:
        return self._uow.escalar(
            "SELECT COUNT(*) AS n FROM PLANTILLA_JUGADOR WHERE id_jugador = ? AND estado = 'activo'",
            (int(id_jugador),)) or 0

    def plantillas_activas(self, id_jugador: int) -> list[dict]:
        return self._uow.consultar(
            """SELECT p.id_plantilla, p.nombre_plantilla, c.nombre_categoria,
                      p.temporada, p.estado, pj.fecha_asignacion
               FROM PLANTILLA_JUGADOR pj
               INNER JOIN PLANTILLA p ON pj.id_plantilla = p.id_plantilla
               INNER JOIN CATEGORIA c ON p.id_categoria = c.id_categoria
               WHERE pj.id_jugador = ? AND pj.estado = 'activo'
               ORDER BY c.nombre_categoria, p.nombre_plantilla""",
            (int(id_jugador),))
