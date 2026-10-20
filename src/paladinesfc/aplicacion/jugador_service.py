"""Casos de uso del módulo Jugadores."""
from __future__ import annotations

from paladinesfc.aplicacion._base import ServicioBase
from paladinesfc.dominio.errores import NoEncontradoError, ReglaNegocioError
from paladinesfc.dominio.jugador import Jugador
from paladinesfc.dominio.vinculo import TutoresDelJugador


class JugadorService(ServicioBase):

    # ── consultas ──────────────────────────────────────────────────────────
    def listar(self, documento: str | None = None) -> list[dict]:
        with self._uow("listar jugadores") as uow:
            return uow.jugadores.listar_con_tutor_principal(documento)

    def obtener(self, id_jugador: int) -> Jugador:
        with self._uow("consultar jugador") as uow:
            return self._obtener(uow, id_jugador)

    def detalle(self, id_jugador: int) -> tuple[Jugador, TutoresDelJugador, list[dict]]:
        id_jugador = int(id_jugador)
        with self._uow("detalle de jugador") as uow:
            jugador = self._obtener(uow, id_jugador)
            return (jugador,
                    uow.vinculos.de_jugador(id_jugador),
                    uow.jugadores.plantillas_activas(id_jugador))

    # ── comandos ───────────────────────────────────────────────────────────
    def registrar_con_tutor(self, nombres, apellidos, documento, fecha_nacimiento,
                            numero_preferido, talla_uniforme, fecha_ingreso, observaciones,
                            id_tutor, parentesco) -> int:
        """Alta de jugador + vínculo con su acudiente principal en UNA transacción."""
        jugador = Jugador.nuevo(nombres, apellidos, documento, fecha_nacimiento,
                                talla_uniforme, fecha_ingreso, numero_preferido, observaciones)
        with self._uow("registrar jugador con tutor") as uow:
            if uow.jugadores.existe_documento(jugador.documento):
                raise ReglaNegocioError(f"Ya existe un jugador con el documento '{jugador.documento}'.")
            if id_tutor is None or uow.tutores.obtener(id_tutor) is None:
                raise ReglaNegocioError("Selecciona un tutor válido de la lista.")
            id_jugador = uow.jugadores.agregar(jugador)
            vinculo = TutoresDelJugador(id_jugador).vincular(id_tutor, parentesco, como_principal=True)
            uow.vinculos.agregar(vinculo)
            uow.commit()
            return id_jugador

    def actualizar(self, id_jugador, nombres, apellidos, numero_preferido,
                   talla_uniforme, estado, observaciones) -> None:
        with self._uow("actualizar jugador") as uow:
            jugador = self._obtener(uow, id_jugador)
            jugador.actualizar(nombres, apellidos, numero_preferido,
                               talla_uniforme, estado, observaciones)
            uow.jugadores.actualizar(jugador)
            uow.commit()

    def inactivar(self, id_jugador: int) -> None:
        """Baja lógica (ADR-0003). Conserva pagos, morosidad, asistencias y vínculos."""
        id_jugador = int(id_jugador)
        with self._uow("inactivar jugador") as uow:
            jugador = self._obtener(uow, id_jugador)
            if uow.jugadores.contar_plantillas_activas(id_jugador) > 0:
                raise ReglaNegocioError(
                    "El jugador tiene plantillas activas. "
                    "Retíralo de todas las plantillas antes de darlo de baja.")
            jugador.inactivar()
            uow.jugadores.actualizar(jugador)
            uow.commit()

    def reactivar(self, id_jugador: int) -> None:
        with self._uow("reactivar jugador") as uow:
            jugador = self._obtener(uow, id_jugador)
            jugador.reactivar()
            uow.jugadores.actualizar(jugador)
            uow.commit()

    @staticmethod
    def _obtener(uow, id_jugador) -> Jugador:
        jugador = uow.jugadores.obtener(int(id_jugador))
        if jugador is None:
            raise NoEncontradoError("Jugador no encontrado.")
        return jugador
