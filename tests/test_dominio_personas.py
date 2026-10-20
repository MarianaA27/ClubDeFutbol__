"""Entidades Jugador, Tutor y Profesor: reglas sin interfaz gráfica ni base de datos."""
from datetime import date

import pytest

from paladinesfc.dominio import Jugador, Profesor, ReglaNegocioError, Tutor

HOY = date(2026, 10, 19)


def _jugador(**cambios):
    datos = dict(nombres="Samuel", apellidos="Rojas", documento="1020304050",
                 fecha_nacimiento="2015-05-10", talla_uniforme="s",
                 fecha_ingreso="2024-02-01", numero_preferido="9", hoy=HOY)
    datos.update(cambios)
    return Jugador.nuevo(**datos)


def test_jugador_nuevo_nace_activo_y_normaliza():
    j = _jugador()
    assert j.estado == "activo"
    assert j.talla_uniforme == "S"
    assert j.numero_preferido == 9
    assert j.fecha_nacimiento == date(2015, 5, 10)


@pytest.mark.parametrize("cambios", [
    {"fecha_nacimiento": "2027-01-01"},
    {"fecha_ingreso": "2014-01-01"},
    {"talla_uniforme": "XXXL"},
    {"numero_preferido": "-3"},
    {"documento": "abc"},
])
def test_jugador_rechaza_datos_invalidos(cambios):
    with pytest.raises(ReglaNegocioError):
        _jugador(**cambios)


def test_jugador_actualizar_usa_la_misma_regla_de_estado():
    j = _jugador()
    j.actualizar("Samuel", "Rojas", None, "m", "lesionado", "")
    assert j.estado == "lesionado" and j.talla_uniforme == "M" and j.observaciones is None
    with pytest.raises(ReglaNegocioError):
        j.actualizar("Samuel", "Rojas", None, "M", "suspendido", None)


def test_jugador_inactivar_y_reactivar():
    j = _jugador()
    j.inactivar()
    assert j.estado == "inactivo"
    with pytest.raises(ReglaNegocioError):
        j.inactivar()
    j.reactivar()
    assert j.estado == "activo"


def test_tutor_etiqueta_distingue_homonimos():
    a = Tutor.nuevo("Carlos", "Pérez", "11111", "3001111111", "a@x.com", "Calle 1")
    b = Tutor.nuevo("Carlos", "Pérez", "22222", "3002222222", "b@x.com", "Calle 2")
    assert a.nombre_completo == b.nombre_completo
    assert a.etiqueta != b.etiqueta


def test_tutor_no_se_inactiva_con_jugadores_activos():
    t = Tutor.nuevo("Carlos", "Pérez", "11111", "3001111111", "a@x.com", "Calle 1")
    with pytest.raises(ReglaNegocioError):
        t.inactivar(jugadores_activos_a_cargo=2)
    t.inactivar(jugadores_activos_a_cargo=0)
    assert t.estado == "inactivo"


def test_profesor_registrar_y_editar_comparten_validacion():
    p = Profesor.nuevo("Luisa", "Gómez", "33333", "3003333333", "L@X.COM", "Arqueros", "2023-01-15")
    assert p.email == "l@x.com" and p.estado == "activo"
    with pytest.raises(ReglaNegocioError):
        p.actualizar("Luisa", "Gómez", "33333", "3003333333", "l@x.com", None, "vacaciones")
    p.inactivar()
    assert p.estado == "inactivo"
