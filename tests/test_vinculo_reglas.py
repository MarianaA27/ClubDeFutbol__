"""
Reglas de la vinculación Jugador–Tutor (ADR-0004).

Incluye los dos defectos del sistema original que dejaban a un jugador sin
acudiente principal.
"""
import pytest

from paladinesfc.dominio import ReglaNegocioError, TutoresDelJugador, VinculoTutor


def _agregado():
    return TutoresDelJugador(7, [
        VinculoTutor(7, 1, "Madre", True, id_jugador_tutor=10),
        VinculoTutor(7, 2, "Padre", False, id_jugador_tutor=11),
    ])


def test_vincular_como_principal_desmarca_al_anterior():
    tutores = _agregado()
    tutores.vincular(3, "Abuelo/a", como_principal=True)
    assert tutores.principal.id_tutor == 3
    assert tutores.es_consistente()


def test_vincular_no_principal_conserva_el_principal():
    tutores = _agregado()
    tutores.vincular(3, "Tío/a", como_principal=False)
    assert tutores.principal.id_tutor == 1


def test_no_se_vincula_dos_veces_el_mismo_tutor():
    with pytest.raises(ReglaNegocioError):
        _agregado().vincular(2, "Padre", como_principal=False)


def test_si_no_hay_principal_el_nuevo_tutor_lo_es():
    tutores = TutoresDelJugador(7, [VinculoTutor(7, 1, "Madre", False, id_jugador_tutor=10)])
    tutores.vincular(2, "Padre", como_principal=False)
    assert tutores.principal.id_tutor == 2


def test_cambiar_principal_a_tutor_no_vinculado_falla_sin_modificar_nada():
    """Defecto original: el 2.º UPDATE no afectaba filas y el jugador quedaba sin principal."""
    tutores = _agregado()
    with pytest.raises(ReglaNegocioError):
        tutores.cambiar_principal(99)
    assert tutores.principal.id_tutor == 1


def test_cambiar_principal():
    tutores = _agregado()
    tutores.cambiar_principal(2)
    assert tutores.principal.id_tutor == 2 and tutores.es_consistente()


def test_no_se_desvincula_al_unico_tutor():
    tutores = TutoresDelJugador(7, [VinculoTutor(7, 1, "Madre", True, id_jugador_tutor=10)])
    with pytest.raises(ReglaNegocioError):
        tutores.desvincular(10)


def test_no_se_desvincula_al_acudiente_principal():
    """Defecto original: delete_jugador_tutor() leía acudiente_principal y lo ignoraba."""
    tutores = _agregado()
    with pytest.raises(ReglaNegocioError):
        tutores.desvincular(10)
    assert tutores.es_consistente()


def test_desvincular_tutor_secundario():
    tutores = _agregado()
    tutores.desvincular(11)
    assert [x.id_tutor for x in tutores.vinculos] == [1]
