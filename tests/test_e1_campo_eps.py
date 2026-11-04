"""
Escenario E1 (Mantenibilidad): agregar "entidad de salud (EPS)" al jugador.

Demostración del cambio real (issue #17). El campo se captura al registrar, se
edita y se ve en el listado; es opcional, así que todo lo existente sigue
funcionando igual (100 % de las pruebas previas pasan sin cambios).
"""
import pytest

from paladinesfc.aplicacion.jugador_service import JugadorService
from paladinesfc.aplicacion.tutor_service import TutorService
from paladinesfc.dominio import Jugador, ReglaNegocioError
from tests.fakes_repositorios import Almacen, fabrica


def test_eps_es_opcional_y_se_normaliza():
    sin_eps = Jugador.nuevo("Ana", "Ruiz", "12345", "2014-01-01", "S", "2024-01-01")
    con_eps = Jugador.nuevo("Ana", "Ruiz", "12345", "2014-01-01", "S", "2024-01-01", eps="  Sura  ")
    assert sin_eps.eps is None
    assert con_eps.eps == "Sura"


def test_eps_no_supera_50_caracteres():
    with pytest.raises(ReglaNegocioError, match="EPS"):
        Jugador.nuevo("Ana", "Ruiz", "12345", "2014-01-01", "S", "2024-01-01", eps="x" * 51)


def test_eps_se_registra_se_edita_y_aparece_en_el_listado():
    almacen = Almacen()
    jugadores, tutores = JugadorService(fabrica(almacen)), TutorService(fabrica(almacen))
    id_tutor = tutores.registrar("Carlos", "Pérez", "11111", "3001111111", "c@x.com", "Calle 1")
    id_jugador = jugadores.registrar_con_tutor("Samuel", "Rojas", "1020304050", "2015-05-10", "9", "S",
                                               "2024-02-01", None, id_tutor, "Padre", eps="Sura")
    assert jugadores.obtener(id_jugador).eps == "Sura"

    jugadores.actualizar(id_jugador, "Samuel", "Rojas", "9", "S", "activo", None, eps="Nueva EPS")
    assert jugadores.obtener(id_jugador).eps == "Nueva EPS"
    assert jugadores.listar()[0]["eps"] == "Nueva EPS"
