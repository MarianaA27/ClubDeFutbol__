"""Utilidades comunes de los repositorios."""
from __future__ import annotations


class RepositorioBase:
    def __init__(self, uow):
        self._uow = uow

    def _existe(self, tabla: str, columna: str, valor, columna_id: str,
                excluir_id: int | None) -> bool:
        sql = f"SELECT COUNT(*) AS n FROM {tabla} WHERE {columna} = ?"
        parametros: list = [valor]
        if excluir_id is not None:
            sql += f" AND {columna_id} <> ?"
            parametros.append(int(excluir_id))
        return (self._uow.escalar(sql, parametros) or 0) > 0
