"""Base común de los servicios de aplicación."""
from __future__ import annotations

from typing import Callable

from paladinesfc.aplicacion.puertos import UnidadDeTrabajo

FabricaUoW = Callable[[str], UnidadDeTrabajo]
"""Recibe el nombre de la operación (para la bitácora) y devuelve una unidad de trabajo nueva."""


class ServicioBase:
    def __init__(self, fabrica_uow: FabricaUoW):
        self._uow = fabrica_uow
