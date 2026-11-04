"""Fixtures de las pruebas de integración contra SQL Server real.

La base de prueba se crea UNA vez por ejecución (esquema + migraciones) y se vacía
antes de cada prueba. Al terminar se elimina, salvo que se defina
``PALADINES_CONSERVAR_BASE=1`` (útil para revisarla en SSMS).
"""
import os

import pytest

from tests.integracion import base_prueba as bp


@pytest.fixture(scope="session")
def cfg_prueba():
    try:
        bp._pyodbc()
    except ImportError as error:   # pragma: no cover - depende del equipo
        pytest.fail(f"Las pruebas de integración necesitan pyodbc y el driver ODBC: {error}")
    cfg = bp.config_prueba()
    try:
        aplicados = bp.crear_base(cfg)
    except Exception as error:     # pragma: no cover - depende del equipo
        pytest.fail(
            f"No se pudo crear la base de prueba '{cfg.database}' en '{cfg.server}'. "
            f"Revise config.ini o PALADINES_DB_*. Detalle: {error}")
    print(f"\nBase de prueba {cfg.database} en {cfg.server}: {', '.join(aplicados)}")
    yield cfg
    if os.environ.get("PALADINES_CONSERVAR_BASE") != "1":
        bp.eliminar_base(cfg)


@pytest.fixture
def base(cfg_prueba):
    bp.limpiar(cfg_prueba)
    return cfg_prueba


@pytest.fixture
def siembra(base):
    s = bp.Siembra(base)
    yield s
    s.cerrar()


@pytest.fixture
def servicios(base):
    return bp.servicios(base)
