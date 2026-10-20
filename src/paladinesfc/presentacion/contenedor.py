"""
Raíz de composición: el ÚNICO lugar donde la presentación conoce la infraestructura.

Crea los servicios de aplicación inyectándoles una fábrica de unidades de trabajo
SQL Server. Las pantallas solo usan ``servicios.<modulo>.<caso_de_uso>()``.
"""
from __future__ import annotations

from dataclasses import dataclass

from paladinesfc.aplicacion.jugador_service import JugadorService
from paladinesfc.aplicacion.profesor_service import ProfesorService
from paladinesfc.aplicacion.tutor_service import TutorService
from paladinesfc.aplicacion.vinculacion_service import VinculacionService
from paladinesfc.infraestructura.unidad_trabajo import UnidadDeTrabajoSql


def _fabrica_uow(operacion: str) -> UnidadDeTrabajoSql:
    return UnidadDeTrabajoSql(operacion=operacion)


@dataclass(frozen=True)
class Servicios:
    jugadores: JugadorService
    tutores: TutorService
    profesores: ProfesorService
    vinculacion: VinculacionService


def crear_servicios(fabrica_uow=_fabrica_uow) -> Servicios:
    return Servicios(
        jugadores=JugadorService(fabrica_uow),
        tutores=TutorService(fabrica_uow),
        profesores=ProfesorService(fabrica_uow),
        vinculacion=VinculacionService(fabrica_uow),
    )


servicios = crear_servicios()
