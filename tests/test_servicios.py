"""Servicios de aplicación del MVP probados con una unidad de trabajo en memoria."""
import pytest

from paladinesfc.aplicacion.jugador_service import JugadorService
from paladinesfc.aplicacion.profesor_service import ProfesorService
from paladinesfc.aplicacion.tutor_service import TutorService
from paladinesfc.aplicacion.vinculacion_service import VinculacionService
from paladinesfc.dominio import ReglaNegocioError
from tests.fakes_repositorios import Almacen, fabrica


@pytest.fixture
def almacen():
    return Almacen()


@pytest.fixture
def servicios(almacen):
    f = fabrica(almacen)
    return JugadorService(f), TutorService(f), ProfesorService(f), VinculacionService(f)


def _registrar_tutor(tutores, documento="11111", telefono="3001111111", nombres="Carlos"):
    return tutores.registrar(nombres, "Pérez", documento, telefono, "c@x.com", "Calle 1")


def _registrar_jugador(jugadores, id_tutor, documento="1020304050"):
    return jugadores.registrar_con_tutor("Samuel", "Rojas", documento, "2015-05-10", "9", "S",
                                         "2024-02-01", None, id_tutor, "Padre")


def test_registrar_jugador_crea_jugador_y_vinculo_principal_en_un_solo_commit(servicios, almacen):
    jugadores, tutores, _, vinculacion = servicios
    id_tutor = _registrar_tutor(tutores)
    commits_previos = almacen.commits
    id_jugador = _registrar_jugador(jugadores, id_tutor)
    assert almacen.commits == commits_previos + 1
    assert vinculacion.tutores_de(id_jugador).principal.id_tutor == id_tutor


def test_registro_falla_completo_si_el_tutor_no_existe(servicios, almacen):
    jugadores, *_ = servicios
    with pytest.raises(ReglaNegocioError):
        _registrar_jugador(jugadores, id_tutor=999)
    assert almacen.jugadores == {} and almacen.vinculos == {}


def test_documento_duplicado_de_jugador(servicios):
    jugadores, tutores, *_ = servicios
    id_tutor = _registrar_tutor(tutores)
    _registrar_jugador(jugadores, id_tutor)
    with pytest.raises(ReglaNegocioError, match="Ya existe un jugador"):
        _registrar_jugador(jugadores, id_tutor)


def test_homonimos_se_resuelven_por_id(servicios):
    """Escenario P1: dos tutores con el mismo nombre; el vínculo apunta al seleccionado."""
    jugadores, tutores, _, vinculacion = servicios
    _registrar_tutor(tutores, "11111", "3001111111")
    id_segundo = _registrar_tutor(tutores, "22222", "3002222222")
    id_jugador = _registrar_jugador(jugadores, id_segundo)
    assert vinculacion.tutores_de(id_jugador).principal.id_tutor == id_segundo


def test_telefono_duplicado_da_mensaje_claro(servicios):
    _, tutores, *_ = servicios
    _registrar_tutor(tutores, "11111", "3001111111")
    with pytest.raises(ReglaNegocioError, match="teléfono"):
        _registrar_tutor(tutores, "22222", "3001111111")


def test_cambiar_y_desvincular_respetan_un_unico_principal(servicios):
    jugadores, tutores, _, vinculacion = servicios
    madre = _registrar_tutor(tutores, "11111", "3001111111")
    padre = _registrar_tutor(tutores, "22222", "3002222222")
    id_jugador = _registrar_jugador(jugadores, madre)
    vinculacion.vincular(id_jugador, padre, "Padre", como_principal=False)
    vinculacion.cambiar_principal(id_jugador, padre)
    estado = vinculacion.tutores_de(id_jugador)
    assert estado.principal.id_tutor == padre and estado.es_consistente()
    id_vinculo_padre = estado.principal.id_jugador_tutor
    with pytest.raises(ReglaNegocioError):
        vinculacion.desvincular(id_vinculo_padre)   # es el principal
    assert vinculacion.tutores_de(id_jugador).es_consistente()


def test_inactivar_jugador_conserva_el_registro(servicios, almacen):
    jugadores, tutores, *_ = servicios
    id_jugador = _registrar_jugador(jugadores, _registrar_tutor(tutores))
    jugadores.inactivar(id_jugador)
    assert almacen.jugadores[id_jugador].estado == "inactivo"
    jugadores.reactivar(id_jugador)
    assert almacen.jugadores[id_jugador].estado == "activo"


def test_no_se_inactiva_jugador_con_plantillas_activas(servicios, almacen):
    jugadores, tutores, *_ = servicios
    id_jugador = _registrar_jugador(jugadores, _registrar_tutor(tutores))
    almacen.plantillas_activas[id_jugador] = 1
    with pytest.raises(ReglaNegocioError, match="plantillas activas"):
        jugadores.inactivar(id_jugador)


def test_inactivar_profesor_lo_saca_de_los_desplegables_sin_borrarlo(servicios, almacen):
    _, _, profesores, _ = servicios
    id_p = profesores.registrar("Luisa", "Gómez", "33333", "3003333333", "l@x.com", None, "2023-01-15")
    profesores.inactivar(id_p)
    assert id_p in almacen.profesores                      # no se borró
    assert all(p.id_profesor != id_p for p in profesores.opciones())
    profesores.reactivar(id_p)                              # reversible sin reingresar datos
    assert any(p.id_profesor == id_p for p in profesores.opciones())


def test_tutor_con_jugadores_activos_no_se_inactiva(servicios):
    jugadores, tutores, *_ = servicios
    id_tutor = _registrar_tutor(tutores)
    _registrar_jugador(jugadores, id_tutor)
    with pytest.raises(ReglaNegocioError, match="jugadores activos"):
        tutores.inactivar(id_tutor)
