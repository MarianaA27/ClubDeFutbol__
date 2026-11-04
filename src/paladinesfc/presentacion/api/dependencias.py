"""Acceso a los servicios de aplicación desde las rutas (inyección de dependencias de FastAPI)."""
from fastapi import Request

from paladinesfc.presentacion.contenedor import Servicios


def servicios(request: Request) -> Servicios:
    return request.app.state.servicios
