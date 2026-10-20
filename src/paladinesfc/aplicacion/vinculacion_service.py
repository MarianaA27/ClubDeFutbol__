"""Casos de uso de la vinculación Jugador–Tutor (las tres operaciones compuestas del MVP)."""
from __future__ import annotations

from paladinesfc.aplicacion._base import ServicioBase
from paladinesfc.dominio.errores import NoEncontradoError, ReglaNegocioError
from paladinesfc.dominio.vinculo import TutoresDelJugador


class VinculacionService(ServicioBase):

    def tutores_de(self, id_jugador: int) -> TutoresDelJugador:
        with self._uow("listar tutores de jugador") as uow:
            return uow.vinculos.de_jugador(int(id_jugador))

    def vincular(self, id_jugador: int, id_tutor: int, parentesco: str,
                 como_principal: bool) -> int:
        with self._uow("vincular tutor") as uow:
            if id_tutor is None or uow.tutores.obtener(int(id_tutor)) is None:
                raise ReglaNegocioError("Selecciona un tutor válido de la lista.")
            tutores = uow.vinculos.de_jugador(int(id_jugador))
            nuevo = tutores.vincular(int(id_tutor), parentesco, como_principal)
            id_vinculo = uow.vinculos.agregar(nuevo)       # UPDATE + INSERT, misma transacción
            uow.commit()
            return id_vinculo

    def cambiar_principal(self, id_jugador: int, id_tutor: int) -> None:
        with self._uow("cambiar acudiente principal") as uow:
            tutores = uow.vinculos.de_jugador(int(id_jugador))
            tutores.cambiar_principal(int(id_tutor))       # valida antes de escribir
            uow.vinculos.establecer_principal(int(id_jugador), int(id_tutor))
            uow.commit()

    def desvincular(self, id_jugador_tutor: int) -> None:
        with self._uow("desvincular tutor") as uow:
            tutores = uow.vinculos.de_vinculo(int(id_jugador_tutor))
            if tutores is None:
                raise NoEncontradoError("Vínculo tutor-jugador no encontrado.")
            tutores.desvincular(int(id_jugador_tutor))     # lectura y borrado en la misma transacción
            uow.vinculos.eliminar(int(id_jugador_tutor))
            uow.commit()
