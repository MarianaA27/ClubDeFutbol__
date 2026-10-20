"""ADR-0001 — el mapeo por nombre hace irrelevante el orden de las columnas."""
from paladinesfc.infraestructura.mapeo import fila_a_dict, filas_a_dicts


class _Cursor:
    def __init__(self, nombres, filas):
        self.description = [(n,) for n in nombres]
        self._filas = list(filas)

    def fetchall(self):
        return self._filas

    def fetchone(self):
        return self._filas[0] if self._filas else None


def test_reordenar_columnas_no_cambia_el_valor_leido():
    original = filas_a_dicts(_Cursor(["id", "documento", "telefono"], [(1, "1001", "300")]))
    reordenada = filas_a_dicts(_Cursor(["telefono", "id", "documento"], [("300", 1, "1001")]))
    assert original[0]["documento"] == reordenada[0]["documento"] == "1001"
    assert original[0]["telefono"] == reordenada[0]["telefono"] == "300"


def test_fila_a_dict_sin_resultados_devuelve_none():
    assert fila_a_dict(_Cursor(["id"], [])) is None
