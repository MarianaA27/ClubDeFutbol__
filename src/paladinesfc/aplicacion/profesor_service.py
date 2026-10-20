"""Casos de uso del módulo Profesores."""
from __future__ import annotations

from paladinesfc.aplicacion._base import ServicioBase
from paladinesfc.dominio.errores import NoEncontradoError, ReglaNegocioError
from paladinesfc.dominio.profesor import Profesor


class ProfesorService(ServicioBase):

    def listar(self, documento: str | None = None) -> list[Profesor]:
        with self._uow("listar profesores") as uow:
            return uow.profesores.listar(documento)

    def opciones(self) -> list[Profesor]:
        with self._uow("profesores para selección") as uow:
            return uow.profesores.listar(solo_activos=True)

    def obtener(self, id_profesor: int) -> Profesor:
        with self._uow("consultar profesor") as uow:
            return self._obtener(uow, id_profesor)

    def detalle(self, id_profesor: int) -> tuple[Profesor, list[dict]]:
        with self._uow("detalle de profesor") as uow:
            return self._obtener(uow, id_profesor), uow.profesores.plantillas_a_cargo(id_profesor)

    def registrar(self, nombres, apellidos, documento, telefono, email,
                  especialidad, fecha_ingreso) -> int:
        profesor = Profesor.nuevo(nombres, apellidos, documento, telefono, email,
                                  especialidad, fecha_ingreso)
        with self._uow("registrar profesor") as uow:
            self._validar_unicos(uow, profesor)
            id_profesor = uow.profesores.agregar(profesor)
            uow.commit()
            return id_profesor

    def actualizar(self, id_profesor, nombres, apellidos, documento, telefono, email,
                   especialidad, estado) -> None:
        with self._uow("actualizar profesor") as uow:
            profesor = self._obtener(uow, id_profesor)
            profesor.actualizar(nombres, apellidos, documento, telefono, email, especialidad, estado)
            self._validar_unicos(uow, profesor)
            uow.profesores.actualizar(profesor)
            uow.commit()

    def inactivar(self, id_profesor: int) -> None:
        """Baja lógica (ADR-0003): SESION, SESION_JUGADOR y PLANTILLA_PROFESOR se conservan."""
        with self._uow("inactivar profesor") as uow:
            profesor = self._obtener(uow, id_profesor)
            profesor.inactivar()
            uow.profesores.actualizar(profesor)
            uow.commit()

    def reactivar(self, id_profesor: int) -> None:
        with self._uow("reactivar profesor") as uow:
            profesor = self._obtener(uow, id_profesor)
            profesor.reactivar()
            uow.profesores.actualizar(profesor)
            uow.commit()

    @staticmethod
    def _validar_unicos(uow, profesor: Profesor) -> None:
        if uow.profesores.existe_documento(profesor.documento, profesor.id_profesor):
            raise ReglaNegocioError(f"Ya existe otro profesor con el documento '{profesor.documento}'.")
        if uow.profesores.existe_telefono(profesor.telefono, profesor.id_profesor):
            raise ReglaNegocioError(f"Ya existe otro profesor con el teléfono '{profesor.telefono}'.")

    @staticmethod
    def _obtener(uow, id_profesor) -> Profesor:
        profesor = uow.profesores.obtener(int(id_profesor))
        if profesor is None:
            raise NoEncontradoError("Profesor no encontrado.")
        return profesor
