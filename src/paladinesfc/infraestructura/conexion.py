"""Fábrica de conexiones a SQL Server (pyodbc) a partir de la configuración externa."""
from __future__ import annotations

from paladinesfc.infraestructura.config import cadena_conexion


def abrir_conexion():
    """Abre una conexión nueva con ``autocommit`` desactivado.

    El import de ``pyodbc`` es diferido para que el dominio, los servicios y las
    pruebas puedan ejecutarse en equipos sin el driver ODBC instalado.
    """
    import pyodbc

    conexion = pyodbc.connect(cadena_conexion(), autocommit=False)
    return conexion
