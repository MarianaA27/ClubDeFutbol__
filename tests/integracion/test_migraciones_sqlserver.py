"""Las migraciones contra SQL Server real: aplicadas en orden, idempotentes y con su efecto."""
import pytest

from tests.integracion import base_prueba as bp

pytestmark = pytest.mark.integracion

RETIRADOS = ("SP_InsertarJugadorTutor", "SP_ActualizarJugador", "SP_InsertarTutor", "SP_InsertarProfesor",
             "SP_ActualizarProfesor", "SP_EliminarJugador", "SP_EliminarProfesor", "SP_EliminarTutor",
             "VW_DetalleJugador", "VW_DetalleTutor", "VW_DetalleProfesor")


def test_las_migraciones_son_idempotentes(siembra, base):
    j, t1, _ = siembra.jugador_con_dos_tutores()
    antes = {t: bp.contar(base, t) for t in ("JUGADOR", "TUTOR", "JUGADOR_TUTOR", "MOROSIDAD")}
    for migracion in bp.migraciones():
        bp.ejecutar_script(base, migracion)          # segunda aplicación
    assert {t: bp.contar(base, t) for t in antes} == antes
    assert bp.principales_de(base, j) == [t1]


def test_columnas_e_indices_que_agregan_las_migraciones(base):
    assert bp.escalar(base, "SELECT COL_LENGTH('TUTOR', 'estado')") is not None        # 001
    assert bp.escalar(base, "SELECT COL_LENGTH('JUGADOR', 'eps')") is not None         # 002
    indices = {f for (f,) in [(bp.escalar(base, "SELECT name FROM sys.indexes WHERE name = ?", (n,)),)
                              for n in ("UX_JT_jugador_tutor", "UX_JT_un_principal")]}
    assert indices == {"UX_JT_jugador_tutor", "UX_JT_un_principal"}


@pytest.mark.parametrize("objeto", RETIRADOS)
def test_objetos_reemplazados_por_el_mvp_ya_no_existen(base, objeto):
    assert bp.escalar(base, "SELECT OBJECT_ID(?)", (objeto,)) is None


def test_los_objetos_que_usan_los_modulos_legados_siguen_existiendo(base):
    for objeto in ("SP_AsignarJugadorPlantilla", "SP_CrearSesion", "SP_RegistrarPago",
                   "FN_FiltrarJugadoresParaPlantilla", "VW_ListaMorosos", "TR_NuevoJugador_Morosidad"):
        assert bp.escalar(base, "SELECT OBJECT_ID(?)", (objeto,)) is not None, objeto


def test_sp_asignar_jugador_plantilla_quedo_actualizado(base):
    """Antes del GO que faltaba en ClubFutbolDB.sql, el SP se quedaba con 3 parámetros (sin @tipo)."""
    parametros = bp.escalar(base, "SELECT COUNT(*) FROM sys.parameters WHERE object_id = OBJECT_ID('SP_AsignarJugadorPlantilla')")
    assert parametros == 4
