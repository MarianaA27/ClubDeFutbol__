"""
Configuración externa de la conexión a la base de datos.

Antes la cadena de conexión estaba fijada en ``db.py`` (``SERVER=GIANY``), por lo
que el sistema solo funcionaba en un equipo. Ahora se lee, en este orden:

1. Variables de entorno ``PALADINES_DB_DRIVER``, ``PALADINES_DB_SERVER``,
   ``PALADINES_DB_DATABASE``, ``PALADINES_DB_TRUSTED``, ``PALADINES_DB_USER``,
   ``PALADINES_DB_PASSWORD``.
2. Archivo ``config.ini`` en la raíz del repositorio (ver ``config.ini.example``),
   o la ruta indicada en ``PALADINES_CONFIG``.
3. Valores por defecto (instancia local, autenticación de Windows).
"""
from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[3]

_POR_DEFECTO = {
    "driver": "ODBC Driver 17 for SQL Server",
    "server": "localhost",
    "database": "ClubFutbolDB",
    "trusted_connection": "yes",
    "user": "",
    "password": "",
}

_ENV = {
    "driver": "PALADINES_DB_DRIVER",
    "server": "PALADINES_DB_SERVER",
    "database": "PALADINES_DB_DATABASE",
    "trusted_connection": "PALADINES_DB_TRUSTED",
    "user": "PALADINES_DB_USER",
    "password": "PALADINES_DB_PASSWORD",
}


@dataclass(frozen=True)
class ConfigBD:
    driver: str
    server: str
    database: str
    trusted_connection: bool
    user: str = ""
    password: str = ""

    def cadena(self) -> str:
        partes = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
        ]
        if self.trusted_connection:
            partes.append("Trusted_Connection=yes")
        else:
            partes.append(f"UID={self.user}")
            partes.append(f"PWD={self.password}")
        partes += ["Encrypt=yes", "TrustServerCertificate=yes"]
        return ";".join(partes) + ";"


def _es_verdadero(valor: str) -> bool:
    return str(valor).strip().lower() in {"1", "yes", "si", "sí", "true"}


def cargar_config(ruta_ini: str | os.PathLike | None = None,
                  entorno: dict | None = None) -> ConfigBD:
    """Construye la configuración combinando entorno > archivo > valores por defecto."""
    entorno = os.environ if entorno is None else entorno
    valores = dict(_POR_DEFECTO)

    ruta = Path(ruta_ini or entorno.get("PALADINES_CONFIG") or _RAIZ / "config.ini")
    if ruta.is_file():
        parser = configparser.ConfigParser()
        parser.read(ruta, encoding="utf-8")
        if parser.has_section("database"):
            for clave in valores:
                if parser.has_option("database", clave):
                    valores[clave] = parser.get("database", clave)

    for clave, variable in _ENV.items():
        if entorno.get(variable):
            valores[clave] = entorno[variable]

    return ConfigBD(
        driver=valores["driver"],
        server=valores["server"],
        database=valores["database"],
        trusted_connection=_es_verdadero(valores["trusted_connection"]),
        user=valores["user"],
        password=valores["password"],
    )


def cadena_conexion() -> str:
    return cargar_config().cadena()
