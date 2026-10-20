"""ADR-0004 — las validaciones viven en un solo lugar del dominio."""
from datetime import date

import pytest

from paladinesfc.dominio import validaciones as v
from paladinesfc.dominio.errores import ReglaNegocioError


@pytest.mark.parametrize("valor", ["Ana María", "O'Neil", "José-Luis", "Ñuñez"])
def test_texto_valido(valor):
    assert v.texto(valor, "Nombres") == valor


@pytest.mark.parametrize("valor", ["", "   ", "Ana2", "Luis@"])
def test_texto_invalido(valor):
    with pytest.raises(ReglaNegocioError):
        v.texto(valor, "Nombres")


@pytest.mark.parametrize("valor,ok", [("12345", True), ("1234", False), ("1" * 16, False), ("10A23", False)])
def test_documento(valor, ok):
    if ok:
        assert v.documento(valor) == valor
    else:
        with pytest.raises(ReglaNegocioError):
            v.documento(valor)


def test_telefono_y_email():
    assert v.telefono("+573001234567") == "+573001234567"
    assert v.email("ANA@Correo.com") == "ana@correo.com"
    with pytest.raises(ReglaNegocioError):
        v.telefono("12")
    with pytest.raises(ReglaNegocioError):
        v.email("ana@correo")
    assert v.email("", obligatorio=False) is None


def test_fecha():
    assert v.fecha("2015-03-21") == date(2015, 3, 21)
    with pytest.raises(ReglaNegocioError):
        v.fecha("21/03/2015")


def test_opcion_normaliza_mayusculas():
    assert v.opcion("xl", v.TALLAS, "Talla uniforme", mayusculas=True) == "XL"
    with pytest.raises(ReglaNegocioError):
        v.opcion("XXXL", v.TALLAS, "Talla uniforme", mayusculas=True)


def test_entero_positivo_opcional():
    assert v.entero_positivo_opcional("", "Número") is None
    assert v.entero_positivo_opcional("10", "Número") == 10
    with pytest.raises(ReglaNegocioError):
        v.entero_positivo_opcional("0", "Número")
