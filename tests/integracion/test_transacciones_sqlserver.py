"""
Escenario E2 (Confiabilidad) contra SQL Server REAL — ADR-0002.

En las pruebas unitarias la conexión es un doble en memoria. Aquí las sentencias
llegan a una instancia real: se comprueba, consultando la tabla JUGADOR_TUTOR con
una conexión independiente, que un fallo a mitad de "cambiar acudiente principal"
no deja estados parciales.

Tres formas de fallo:
1. Fallo inyectado entre los dos UPDATE (10 repeticiones, como pide la medida de E2).
2. Error real del motor: la segunda sentencia viola un índice único.
3. Pérdida real de la sesión: la conexión se mata con KILL a mitad de la transacción.
"""
import logging

import pytest

from paladinesfc.aplicacion.vinculacion_service import VinculacionService
from paladinesfc.dominio.vinculo import VinculoTutor
from paladinesfc.infraestructura.unidad_trabajo import UnidadDeTrabajoSql
from tests.integracion import base_prueba as bp

pytestmark = pytest.mark.integracion

ConexionConFallo = bp.ConexionConFallo
ConexionPerdida = bp.ConexionPerdida


def test_cambiar_principal_se_confirma_en_sql_server(siembra, servicios, base):
    j, t1, t2 = siembra.jugador_con_dos_tutores()
    servicios.vinculacion.cambiar_principal(j, t2)
    assert bp.principales_de(base, j) == [t2]


@pytest.mark.parametrize("ejecucion", range(1, 11))
def test_fallo_entre_los_dos_update_no_deja_estado_parcial(siembra, base, ejecucion):
    """Medida de E2: cero estados parciales en 10 inyecciones de fallo controladas."""
    j, t1, t2 = siembra.jugador_con_dos_tutores()
    conexiones = []

    def conexion_con_fallo():
        conexiones.append(ConexionConFallo(bp.conectar(base)))
        return conexiones[-1]

    servicio = VinculacionService(bp.fabrica_uow(base, conexion_con_fallo))
    with pytest.raises(ConexionPerdida):
        servicio.cambiar_principal(j, t2)

    # El primer UPDATE (desmarcar a todos) SÍ llegó al motor...
    assert any("SET acudiente_principal = 0" in s for s in conexiones[0].enviadas)
    # ...pero se revirtió: el jugador conserva exactamente su principal original.
    assert bp.principales_de(base, j) == [t1]


def test_error_real_del_motor_revierte_la_operacion_completa(siembra, base):
    """La 2.ª sentencia viola UX_JT_jugador_tutor (migración 001); la 1.ª ya había desmarcado al principal."""
    j, t1, _ = siembra.jugador_con_dos_tutores()
    pyodbc = bp._pyodbc()
    with pytest.raises(pyodbc.IntegrityError):
        with UnidadDeTrabajoSql(lambda: bp.conectar(base), "vincular tutor duplicado") as uow:
            # Se salta a propósito la regla del dominio para que sea el MOTOR quien falle.
            uow.vinculos.agregar(VinculoTutor(j, t1, "Padre", acudiente_principal=True))
            uow.commit()
    assert bp.principales_de(base, j) == [t1]
    assert bp.contar(base, "JUGADOR_TUTOR", "id_jugador = ?", (j,)) == 2


def test_perdida_real_de_la_sesion_revierte_en_el_motor(siembra, base, caplog):
    """La sesión se mata con KILL entre los dos UPDATE: SQL Server revierte la transacción."""
    pyodbc = bp._pyodbc()
    j, t1, t2 = siembra.jugador_con_dos_tutores()
    admin = bp.conectar(base, autocommit=True)
    try:
        with caplog.at_level(logging.WARNING, logger="paladinesfc"):
            with pytest.raises(pyodbc.Error):
                with UnidadDeTrabajoSql(lambda: bp.conectar(base), "cambiar acudiente principal") as uow:
                    spid = uow.escalar("SELECT @@SPID AS spid")
                    uow.ejecutar("UPDATE JUGADOR_TUTOR SET acudiente_principal = 0 WHERE id_jugador = ?", (j,))
                    try:
                        admin.cursor().execute(f"KILL {int(spid)}")
                    except pyodbc.Error as error:
                        pytest.skip(f"El usuario de prueba no tiene permiso para KILL: {error}")
                    uow.ejecutar(
                        "UPDATE JUGADOR_TUTOR SET acudiente_principal = 1 WHERE id_jugador = ? AND id_tutor = ?",
                        (j, t2))
                    uow.commit()
    finally:
        admin.close()
    assert bp.principales_de(base, j) == [t1]
    assert "revertida" in caplog.text


def test_el_fallo_queda_registrado_en_la_bitacora(siembra, base, caplog):
    j, _, t2 = siembra.jugador_con_dos_tutores()
    servicio = VinculacionService(bp.fabrica_uow(base, lambda: ConexionConFallo(bp.conectar(base))))
    with caplog.at_level(logging.ERROR, logger="paladinesfc"):
        with pytest.raises(ConexionPerdida):
            servicio.cambiar_principal(j, t2)
    assert "cambiar acudiente principal" in caplog.text
    assert "revertida" in caplog.text


def test_registrar_jugador_con_tutor_es_atomico_en_sql_server(siembra, servicios, base, monkeypatch):
    """Si el INSERT del vínculo falla, tampoco queda el jugador (ni la morosidad que crea el trigger)."""
    from paladinesfc.dominio import validaciones
    pyodbc = bp._pyodbc()
    id_tutor = siembra.tutor()
    # Parentesco aceptado por el dominio pero más largo que la columna VARCHAR(50):
    # el jugador se inserta y el INSERT del vínculo lo rechaza el motor.
    largo = "Acudiente " + "x" * 60
    monkeypatch.setattr(validaciones, "PARENTESCOS", validaciones.PARENTESCOS + (largo,))
    with pytest.raises(pyodbc.Error):
        servicios.jugadores.registrar_con_tutor("Samuel", "Rojas", "1099887766", "2015-05-10", "9", "S",
                                                "2024-02-01", None, id_tutor, largo)
    assert bp.contar(base, "JUGADOR", "documento = ?", ("1099887766",)) == 0
    assert bp.contar(base, "MOROSIDAD") == 0
