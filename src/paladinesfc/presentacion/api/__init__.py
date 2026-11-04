"""
API REST del MVP (entrega final, issue #37).

Es un SEGUNDO adaptador de la capa de presentación: usa exactamente los mismos
servicios de aplicación que la interfaz de escritorio, a través de la misma raíz
de composición. Agregarla no cambió ni el dominio, ni los servicios, ni la
infraestructura (evidencia de la regla de dependencias de la arquitectura).

    from paladinesfc.presentacion.api import crear_app
    app = crear_app()            # servicios reales sobre SQL Server
    app = crear_app(servicios)   # servicios inyectados (pruebas)
"""
from paladinesfc.presentacion.api.app import crear_app

__all__ = ["crear_app"]
