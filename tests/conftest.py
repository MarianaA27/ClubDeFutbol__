"""Configuración común de pytest.

* Agrega ``src`` al path para importar ``paladinesfc``.
* Las pruebas marcadas con ``@pytest.mark.integracion`` necesitan un SQL Server real
  y solo se ejecutan con ``python -m pytest --integracion`` (o con la variable de
  entorno ``PALADINES_INTEGRACION=1``). Sin esa opción se omiten, para que
  ``python -m pytest`` siga funcionando en cualquier equipo.
"""
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


def pytest_addoption(parser):
    parser.addoption(
        "--integracion", action="store_true", default=False,
        help="Ejecuta también las pruebas de integración contra SQL Server real.")


def _integracion_activa(config) -> bool:
    return bool(config.getoption("--integracion") or os.environ.get("PALADINES_INTEGRACION") == "1")


def pytest_collection_modifyitems(config, items):
    if _integracion_activa(config):
        return
    omitir = pytest.mark.skip(reason="Requiere SQL Server: ejecute con --integracion")
    for item in items:
        if "integracion" in item.keywords:
            item.add_marker(omitir)
