"""Repositorio de profesores.

La edición ya no tiene dos vías: ``SP_ActualizarProfesor`` (que nunca se invocaba
y no recibía el documento) queda obsoleto; toda escritura pasa por aquí (ADR-0004).
"""
from __future__ import annotations

from paladinesfc.dominio.profesor import Profesor
from paladinesfc.infraestructura.repositorios._base import RepositorioBase

_COLUMNAS = """id_profesor, nombres, apellidos, documento, telefono, email,
               especialidad, estado, fecha_ingreso"""


class RepositorioProfesoresSql(RepositorioBase):

    def obtener(self, id_profesor: int) -> Profesor | None:
        fila = self._uow.consultar_uno(
            f"SELECT {_COLUMNAS} FROM PROFESOR WHERE id_profesor = ?", (int(id_profesor),))
        return Profesor.desde_bd(fila) if fila else None

    def existe_documento(self, documento: str, excluir_id: int | None = None) -> bool:
        return self._existe("PROFESOR", "documento", documento, "id_profesor", excluir_id)

    def existe_telefono(self, telefono: str, excluir_id: int | None = None) -> bool:
        return self._existe("PROFESOR", "telefono", telefono, "id_profesor", excluir_id)

    def listar(self, documento: str | None = None, solo_activos: bool = False) -> list[Profesor]:
        condiciones, parametros = [], []
        if documento and documento.strip():
            condiciones.append("documento LIKE ?")
            parametros.append(f"%{documento.strip()}%")
        if solo_activos:
            condiciones.append("estado = 'activo'")
        sql = f"SELECT {_COLUMNAS} FROM PROFESOR"
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        sql += " ORDER BY apellidos, nombres"
        return [Profesor.desde_bd(f) for f in self._uow.consultar(sql, parametros)]

    def agregar(self, profesor: Profesor) -> int:
        id_nuevo = self._uow.insertar(
            """INSERT INTO PROFESOR (nombres, apellidos, documento, telefono, email,
                                     especialidad, estado, fecha_ingreso)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (profesor.nombres, profesor.apellidos, profesor.documento, profesor.telefono,
             profesor.email, profesor.especialidad, profesor.estado, profesor.fecha_ingreso))
        profesor.id_profesor = id_nuevo
        return id_nuevo

    def actualizar(self, profesor: Profesor) -> None:
        self._uow.ejecutar(
            """UPDATE PROFESOR
               SET nombres = ?, apellidos = ?, documento = ?, telefono = ?,
                   email = ?, especialidad = ?, estado = ?
               WHERE id_profesor = ?""",
            (profesor.nombres, profesor.apellidos, profesor.documento, profesor.telefono,
             profesor.email, profesor.especialidad, profesor.estado,
             int(profesor.id_profesor)))

    def plantillas_a_cargo(self, id_profesor: int) -> list[dict]:
        """Reemplaza VW_DetalleProfesor (mismo defecto de columnas corridas que VW_DetalleTutor)."""
        return self._uow.consultar(
            """SELECT pl.id_plantilla, pl.nombre_plantilla, pl.estado AS estado_plantilla,
                      pp.cargo, pp.fecha_asignacion
               FROM PLANTILLA_PROFESOR pp
               INNER JOIN PLANTILLA pl ON pl.id_plantilla = pp.id_plantilla
               WHERE pp.id_profesor = ?
               ORDER BY pl.nombre_plantilla""",
            (int(id_profesor),))
