"""Casos de uso del módulo Tutores."""
from __future__ import annotations

from paladinesfc.aplicacion._base import ServicioBase
from paladinesfc.dominio.errores import NoEncontradoError, ReglaNegocioError
from paladinesfc.dominio.tutor import Tutor


class TutorService(ServicioBase):

    def listar(self, documento: str | None = None) -> list[Tutor]:
        with self._uow("listar tutores") as uow:
            return uow.tutores.listar(documento)

    def opciones(self) -> list[Tutor]:
        """Tutores activos para desplegables. La UI debe guardar el id, no el nombre (P1)."""
        with self._uow("tutores para selección") as uow:
            return uow.tutores.listar(solo_activos=True)

    def obtener(self, id_tutor: int) -> Tutor:
        with self._uow("consultar tutor") as uow:
            return self._obtener(uow, id_tutor)

    def detalle(self, id_tutor: int) -> tuple[Tutor, list[dict]]:
        with self._uow("detalle de tutor") as uow:
            return self._obtener(uow, id_tutor), uow.tutores.jugadores_a_cargo(id_tutor)

    def registrar(self, nombres, apellidos, documento, telefono, email, direccion) -> int:
        tutor = Tutor.nuevo(nombres, apellidos, documento, telefono, email, direccion)
        with self._uow("registrar tutor") as uow:
            self._validar_unicos(uow, tutor)
            id_tutor = uow.tutores.agregar(tutor)
            uow.commit()
            return id_tutor

    def actualizar(self, id_tutor, nombres, apellidos, documento, telefono, email, direccion) -> None:
        with self._uow("actualizar tutor") as uow:
            tutor = self._obtener(uow, id_tutor)
            tutor.actualizar(nombres, apellidos, documento, telefono, email, direccion)
            self._validar_unicos(uow, tutor)
            uow.tutores.actualizar(tutor)
            uow.commit()

    def inactivar(self, id_tutor: int) -> None:
        """Baja lógica (ADR-0003). Requiere la migración 001 (columna TUTOR.estado)."""
        with self._uow("inactivar tutor") as uow:
            tutor = self._obtener(uow, id_tutor)
            tutor.inactivar(uow.tutores.contar_jugadores_activos(id_tutor))
            uow.tutores.actualizar(tutor)
            uow.commit()

    @staticmethod
    def _validar_unicos(uow, tutor: Tutor) -> None:
        # Antes estas reglas solo existían como UNIQUE en la tabla y la usuaria
        # veía el error crudo de pyodbc.
        if uow.tutores.existe_documento(tutor.documento, tutor.id_tutor):
            raise ReglaNegocioError(f"Ya existe un tutor con el documento '{tutor.documento}'.")
        if uow.tutores.existe_telefono(tutor.telefono, tutor.id_tutor):
            raise ReglaNegocioError(f"Ya existe un tutor con el teléfono '{tutor.telefono}'.")

    @staticmethod
    def _obtener(uow, id_tutor) -> Tutor:
        tutor = uow.tutores.obtener(int(id_tutor))
        if tutor is None:
            raise NoEncontradoError("Tutor no encontrado.")
        return tutor
