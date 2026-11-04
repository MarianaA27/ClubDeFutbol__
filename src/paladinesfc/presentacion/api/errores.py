"""Traducción de los errores del dominio y de la base de datos a respuestas HTTP."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from paladinesfc.dominio.errores import NoEncontradoError, ReglaNegocioError
from paladinesfc.infraestructura.bitacora import obtener_bitacora


def _respuesta(estado: int, mensaje: str) -> JSONResponse:
    return JSONResponse(status_code=estado, content={"detalle": mensaje})


def _es_error_de_base_de_datos(error: Exception) -> bool:
    try:
        import pyodbc
    except ImportError:   # pragma: no cover - equipos sin driver ODBC
        return False
    return isinstance(error, pyodbc.Error)


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(NoEncontradoError)
    async def no_encontrado(_: Request, error: NoEncontradoError):
        return _respuesta(404, str(error))

    @app.exception_handler(ReglaNegocioError)
    async def regla_de_negocio(_: Request, error: ReglaNegocioError):
        return _respuesta(400, str(error))

    @app.exception_handler(Exception)
    async def inesperado(_: Request, error: Exception):
        if _es_error_de_base_de_datos(error):
            obtener_bitacora().error("API: error de base de datos: %s", error)
            return _respuesta(503, "No se pudo completar la operación en la base de datos.")
        obtener_bitacora().exception("API: error inesperado")
        return _respuesta(500, "Error interno del servidor.")
