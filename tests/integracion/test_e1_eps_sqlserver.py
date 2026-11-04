"""Escenario E1 contra SQL Server real: la migración 002 y el campo EPS de extremo a extremo."""
import pytest

from tests.integracion import base_prueba as bp

pytestmark = pytest.mark.integracion


def test_eps_se_guarda_se_edita_y_se_lista_en_sql_server(siembra, servicios, base):
    id_tutor = siembra.tutor()
    id_jugador = servicios.jugadores.registrar_con_tutor(
        "Samuel", "Rojas", "1020304050", "2015-05-10", "9", "S", "2024-02-01", None,
        id_tutor, "Padre", eps="Sura")
    assert bp.escalar(base, "SELECT eps FROM JUGADOR WHERE id_jugador = ?", (id_jugador,)) == "Sura"

    servicios.jugadores.actualizar(id_jugador, "Samuel", "Rojas", "9", "S", "activo", None, eps="Nueva EPS")
    assert servicios.jugadores.obtener(id_jugador).eps == "Nueva EPS"
    assert servicios.jugadores.listar("1020304050")[0]["eps"] == "Nueva EPS"


def test_jugadores_existentes_quedan_sin_eps(siembra, servicios):
    """La migración es aditiva: los registros anteriores siguen válidos (EPS vacía)."""
    siembra.jugador(documento="1011121314")
    assert servicios.jugadores.listar("1011121314")[0]["eps"] == "-"
