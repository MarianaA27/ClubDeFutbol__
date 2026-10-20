"""
Bitácora del sistema (escenario de Confiabilidad, Semana 8).

Toda operación revertida por la unidad de trabajo queda registrada con su causa
en ``logs/paladinesfc.log`` (archivo rotativo de 1 MB, 5 copias).
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_NOMBRE = "paladinesfc"
_CARPETA_LOGS = Path(__file__).resolve().parents[3] / "logs"


def obtener_bitacora() -> logging.Logger:
    logger = logging.getLogger(_NOMBRE)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        try:
            _CARPETA_LOGS.mkdir(parents=True, exist_ok=True)
            manejador = RotatingFileHandler(
                _CARPETA_LOGS / "paladinesfc.log",
                maxBytes=1_000_000, backupCount=5, encoding="utf-8",
            )
        except OSError:
            manejador = logging.StreamHandler()
        manejador.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(manejador)
    return logger
