"""
ADR-0002 — Unidad de trabajo transaccional.

Verifica el escenario de Confiabilidad de la Semana 8: ante un fallo inyectado a
mitad de una operación compuesta, la base queda idéntica al estado previo
(cero estados parciales) y el fallo queda en la bitácora.
"""
import logging

import pytest

from paladinesfc.infraestructura.unidad_trabajo import UnidadDeTrabajoSql
from tests.fakes_bd import ConexionFalsa, FalloInyectado

DESMARCAR = "UPDATE JUGADOR_TUTOR SET acudiente_principal = 0 WHERE id_jugador = ?"
MARCAR = "UPDATE JUGADOR_TUTOR SET acudiente_principal = 1 WHERE id_jugador = ? AND id_tutor = ?"


def _cambiar_principal(uow, id_jugador, id_tutor):
    """Las dos sentencias que en el sistema original eran transacciones separadas."""
    uow.ejecutar(DESMARCAR, (id_jugador,))
    uow.ejecutar(MARCAR, (id_jugador, id_tutor))
    uow.commit()


def test_operacion_completa_confirma_las_dos_sentencias_en_un_solo_commit():
    conexion = ConexionFalsa()
    with UnidadDeTrabajoSql(lambda: conexion) as uow:
        _cambiar_principal(uow, 7, 3)
    assert conexion.commits == 1
    assert len(conexion.confirmadas) == 2
    assert conexion.autocommit is False
    assert conexion.cerrada


@pytest.mark.parametrize("ejecucion", range(10))
def test_fallo_entre_las_dos_sentencias_no_deja_estados_parciales(ejecucion):
    """Diez inyecciones controladas: el fallo ocurre tras el primer UPDATE."""
    conexion = ConexionFalsa(fallar_en=2)
    with pytest.raises(FalloInyectado):
        with UnidadDeTrabajoSql(lambda: conexion) as uow:
            _cambiar_principal(uow, 7, 3)
    assert conexion.confirmadas == []      # la base queda igual que antes
    assert conexion.commits == 0
    assert conexion.rollbacks == 1
    assert conexion.cerrada


def test_sin_commit_explicito_no_se_persiste_nada():
    conexion = ConexionFalsa()
    with UnidadDeTrabajoSql(lambda: conexion) as uow:
        uow.ejecutar(DESMARCAR, (7,))
    assert conexion.confirmadas == []
    assert conexion.rollbacks == 1


def test_el_fallo_queda_registrado_en_la_bitacora(caplog):
    conexion = ConexionFalsa(fallar_en=2)
    with caplog.at_level(logging.ERROR, logger="paladinesfc"):
        with pytest.raises(FalloInyectado):
            with UnidadDeTrabajoSql(lambda: conexion, operacion="cambiar acudiente principal") as uow:
                _cambiar_principal(uow, 7, 3)
    assert "cambiar acudiente principal" in caplog.text
    assert "revertida" in caplog.text


def test_consultar_devuelve_diccionarios_por_nombre_de_columna():
    conexion = ConexionFalsa(respuestas=[(["id_jugador", "nombres"], [(1, "Ana"), (2, "Luis")])])
    with UnidadDeTrabajoSql(lambda: conexion) as uow:
        filas = uow.consultar("SELECT id_jugador, nombres FROM JUGADOR")
    assert filas == [{"id_jugador": 1, "nombres": "Ana"}, {"id_jugador": 2, "nombres": "Luis"}]
