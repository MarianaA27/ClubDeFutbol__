"""
Mapeo de resultados por NOMBRE de columna (ADR-0001, problema P1).

El sistema original devolvía tuplas ``(columnas, filas)`` y la interfaz leía
``fila[5]``, ``fila[8]``… Si una consulta cambiaba el orden de sus columnas, la
pantalla mostraba o guardaba el dato equivocado sin ningún error. Aquí cada fila
se convierte en un ``dict`` cuyas claves son los nombres de columna, y los
repositorios construyen entidades a partir de esas claves.
"""
from __future__ import annotations

from typing import Any


def columnas(cursor) -> list[str]:
    return [descripcion[0] for descripcion in (cursor.description or [])]


def filas_a_dicts(cursor) -> list[dict[str, Any]]:
    nombres = columnas(cursor)
    return [dict(zip(nombres, fila)) for fila in cursor.fetchall()]


def fila_a_dict(cursor) -> dict[str, Any] | None:
    nombres = columnas(cursor)
    fila = cursor.fetchone()
    return dict(zip(nombres, fila)) if fila is not None else None
