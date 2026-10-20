"""Repositorio de la vinculación Jugador–Tutor."""
from __future__ import annotations

from paladinesfc.dominio.errores import ReglaNegocioError
from paladinesfc.dominio.vinculo import TutoresDelJugador, VinculoTutor
from paladinesfc.infraestructura.repositorios._base import RepositorioBase


class RepositorioVinculosSql(RepositorioBase):

    def de_jugador(self, id_jugador: int) -> TutoresDelJugador:
        filas = self._uow.consultar(
            """SELECT jt.id_jugador_tutor, jt.id_jugador, t.id_tutor,
                      t.nombres + ' ' + t.apellidos AS tutor,
                      t.telefono, t.email, jt.parentesco, jt.acudiente_principal
               FROM JUGADOR_TUTOR jt INNER JOIN TUTOR t ON t.id_tutor = jt.id_tutor
               WHERE jt.id_jugador = ?
               ORDER BY jt.acudiente_principal DESC, t.apellidos""",
            (int(id_jugador),))
        return TutoresDelJugador(int(id_jugador), [VinculoTutor.desde_bd(f) for f in filas])

    def de_vinculo(self, id_jugador_tutor: int) -> TutoresDelJugador | None:
        id_jugador = self._uow.escalar(
            "SELECT id_jugador FROM JUGADOR_TUTOR WHERE id_jugador_tutor = ?",
            (int(id_jugador_tutor),))
        return None if id_jugador is None else self.de_jugador(id_jugador)

    def agregar(self, vinculo: VinculoTutor) -> int:
        if vinculo.acudiente_principal:
            self._uow.ejecutar(
                "UPDATE JUGADOR_TUTOR SET acudiente_principal = 0 WHERE id_jugador = ?",
                (int(vinculo.id_jugador),))
        id_nuevo = self._uow.insertar(
            """INSERT INTO JUGADOR_TUTOR (id_jugador, id_tutor, parentesco, acudiente_principal)
               VALUES (?, ?, ?, ?)""",
            (int(vinculo.id_jugador), int(vinculo.id_tutor), vinculo.parentesco,
             1 if vinculo.acudiente_principal else 0))
        vinculo.id_jugador_tutor = id_nuevo
        return id_nuevo

    def establecer_principal(self, id_jugador: int, id_tutor: int) -> None:
        """Las dos sentencias del escenario de Confiabilidad, ahora en UNA transacción."""
        self._uow.ejecutar(
            "UPDATE JUGADOR_TUTOR SET acudiente_principal = 0 WHERE id_jugador = ?",
            (int(id_jugador),))
        afectadas = self._uow.ejecutar(
            "UPDATE JUGADOR_TUTOR SET acudiente_principal = 1 WHERE id_jugador = ? AND id_tutor = ?",
            (int(id_jugador), int(id_tutor)))
        if afectadas != 1:
            # Provoca rollback de la unidad de trabajo: el primer UPDATE se deshace.
            raise ReglaNegocioError("El tutor seleccionado no está vinculado a este jugador.")

    def eliminar(self, id_jugador_tutor: int) -> None:
        self._uow.ejecutar(
            "DELETE FROM JUGADOR_TUTOR WHERE id_jugador_tutor = ?", (int(id_jugador_tutor),))
