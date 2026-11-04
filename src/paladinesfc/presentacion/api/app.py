"""Construcción de la aplicación FastAPI."""
from __future__ import annotations

from fastapi import FastAPI

from paladinesfc.presentacion.api.errores import registrar_manejadores
from paladinesfc.presentacion.api.rutas import jugadores, profesores, tutores

DESCRIPCION = """
API REST de los módulos del MVP de PaladinesFC: **Jugadores, Jugador–Tutor, Tutores y
Profesores**.

Usa los mismos servicios de aplicación que la interfaz de escritorio, así que aplica
las mismas reglas: una transacción por operación, baja lógica en lugar de borrado y
selección de tutores por id.

Errores: `400` regla de negocio no cumplida · `404` no encontrado · `422` formato de
JSON inválido · `503` no se pudo acceder a la base de datos. El cuerpo siempre es
`{"detalle": "mensaje"}` (salvo el `422`, que genera FastAPI).
"""


def crear_app(servicios=None) -> FastAPI:
    """``servicios``: los de ``presentacion.contenedor`` por defecto (SQL Server real)."""
    if servicios is None:
        from paladinesfc.presentacion.contenedor import servicios as servicios_reales
        servicios = servicios_reales
    app = FastAPI(title="PaladinesFC — API del MVP", version="1.0.0", description=DESCRIPCION)
    app.state.servicios = servicios
    registrar_manejadores(app)
    for modulo in (jugadores, tutores, profesores):
        app.include_router(modulo.router)

    @app.get("/salud", tags=["Sistema"], summary="Comprobar que la API responde")
    def salud():
        return {"estado": "ok"}

    return app
