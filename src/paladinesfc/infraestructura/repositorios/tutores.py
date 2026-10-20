"""Repositorio de tutores.

La columna ``TUTOR.estado`` la agrega la migración ``001_inactivacion_logica.sql``
(ADR-0003). Mientras no se aplique, el repositorio funciona igual que antes y la
inactivación responde con un mensaje que pide aplicar la migración.
"""
from __future__ import annotations

from paladinesfc.dominio.errores import ReglaNegocioError
from paladinesfc.dominio.tutor import Tutor
from paladinesfc.infraestructura.repositorios._base import RepositorioBase


class RepositorioTutoresSql(RepositorioBase):

    def __init__(self, uow):
        super().__init__(uow)
        self._con_estado: bool | None = None

    def tiene_columna_estado(self) -> bool:
        if self._con_estado is None:
            self._con_estado = self._uow.escalar(
                "SELECT COL_LENGTH('TUTOR', 'estado') AS n") is not None
        return self._con_estado

    def _columnas(self) -> str:
        base = "id_tutor, nombres, apellidos, documento, telefono, email, direccion"
        return base + (", estado" if self.tiene_columna_estado() else "")

    def obtener(self, id_tutor: int) -> Tutor | None:
        fila = self._uow.consultar_uno(
            f"SELECT {self._columnas()} FROM TUTOR WHERE id_tutor = ?", (int(id_tutor),))
        return Tutor.desde_bd(fila) if fila else None

    def existe_documento(self, documento: str, excluir_id: int | None = None) -> bool:
        return self._existe("TUTOR", "documento", documento, "id_tutor", excluir_id)

    def existe_telefono(self, telefono: str, excluir_id: int | None = None) -> bool:
        return self._existe("TUTOR", "telefono", telefono, "id_tutor", excluir_id)

    def listar(self, documento: str | None = None, solo_activos: bool = False) -> list[Tutor]:
        condiciones, parametros = [], []
        if documento and documento.strip():
            condiciones.append("documento LIKE ?")
            parametros.append(f"%{documento.strip()}%")
        if solo_activos and self.tiene_columna_estado():
            condiciones.append("estado = 'activo'")
        sql = f"SELECT {self._columnas()} FROM TUTOR"
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        sql += " ORDER BY apellidos, nombres"
        return [Tutor.desde_bd(f) for f in self._uow.consultar(sql, parametros)]

    def agregar(self, tutor: Tutor) -> int:
        id_nuevo = self._uow.insertar(
            """INSERT INTO TUTOR (nombres, apellidos, documento, telefono, email, direccion)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (tutor.nombres, tutor.apellidos, tutor.documento,
             tutor.telefono, tutor.email, tutor.direccion))
        tutor.id_tutor = id_nuevo
        return id_nuevo

    def actualizar(self, tutor: Tutor) -> None:
        sql = """UPDATE TUTOR SET nombres = ?, apellidos = ?, documento = ?,
                                  telefono = ?, email = ?, direccion = ?"""
        parametros = [tutor.nombres, tutor.apellidos, tutor.documento,
                      tutor.telefono, tutor.email, tutor.direccion]
        if self.tiene_columna_estado():
            sql += ", estado = ?"
            parametros.append(tutor.estado)
        elif tutor.estado != "activo":
            raise ReglaNegocioError(
                "La inactivación de tutores requiere aplicar la migración "
                "src/sql/migraciones/001_inactivacion_logica.sql.")
        sql += " WHERE id_tutor = ?"
        parametros.append(int(tutor.id_tutor))
        self._uow.ejecutar(sql, parametros)

    def contar_jugadores_activos(self, id_tutor: int) -> int:
        return self._uow.escalar(
            """SELECT COUNT(*) AS n
               FROM JUGADOR_TUTOR jt INNER JOIN JUGADOR j ON j.id_jugador = jt.id_jugador
               WHERE jt.id_tutor = ? AND j.estado <> 'inactivo'""",
            (int(id_tutor),)) or 0

    def jugadores_a_cargo(self, id_tutor: int) -> list[dict]:
        """Reemplaza VW_DetalleTutor (cuyas 6 columnas se mostraban corridas bajo 5 encabezados)."""
        return self._uow.consultar(
            """SELECT j.id_jugador, j.nombres + ' ' + j.apellidos AS jugador, j.documento,
                      j.estado, jt.parentesco, jt.acudiente_principal
               FROM JUGADOR_TUTOR jt INNER JOIN JUGADOR j ON j.id_jugador = jt.id_jugador
               WHERE jt.id_tutor = ?
               ORDER BY j.apellidos, j.nombres""",
            (int(id_tutor),))
