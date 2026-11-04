"""
Escenario E3 (Seguridad: integridad y no repudio) contra SQL Server REAL — ADR-0003.

Se siembra el historial con SQL directo, se da de baja con los servicios de la
aplicación y se cuentan las filas de historial antes y después con una conexión
independiente. Medida de E3: conteos idénticos, cero filas huérfanas, el profesor
desaparece de los desplegables y se puede reactivar sin reingresar datos.
"""
import pytest

from paladinesfc.dominio.errores import ReglaNegocioError
from tests.integracion import base_prueba as bp

pytestmark = pytest.mark.integracion

TABLAS_HISTORIAL = ("SESION", "SESION_JUGADOR", "PLANTILLA_PROFESOR", "PLANTILLA_JUGADOR",
                    "PAGO", "MOROSIDAD", "JUGADOR_TUTOR")


def _conteos(cfg):
    return {tabla: bp.contar(cfg, tabla) for tabla in TABLAS_HISTORIAL}


def _huerfanas(cfg) -> int:
    consultas = [
        "SELECT COUNT(*) FROM SESION s WHERE NOT EXISTS (SELECT 1 FROM PROFESOR p WHERE p.id_profesor = s.id_profesor)",
        "SELECT COUNT(*) FROM SESION_JUGADOR sj WHERE NOT EXISTS (SELECT 1 FROM SESION s WHERE s.id_sesion = sj.id_sesion)",
        "SELECT COUNT(*) FROM PLANTILLA_PROFESOR pp WHERE NOT EXISTS (SELECT 1 FROM PROFESOR p WHERE p.id_profesor = pp.id_profesor)",
        "SELECT COUNT(*) FROM PAGO pg WHERE NOT EXISTS (SELECT 1 FROM JUGADOR j WHERE j.id_jugador = pg.id_jugador)",
        "SELECT COUNT(*) FROM MOROSIDAD m WHERE NOT EXISTS (SELECT 1 FROM JUGADOR j WHERE j.id_jugador = m.id_jugador)",
    ]
    return sum(int(bp.escalar(cfg, q)) for q in consultas)


def test_baja_de_profesor_con_12_sesiones_y_2_plantillas_conserva_todo_el_historial(siembra, servicios, base):
    id_profesor, _, _ = siembra.profesor_con_historial(sesiones=12, plantillas=2, jugadores=3)
    antes = _conteos(base)
    asistencias_antes = bp.escalar(base, "SELECT SUM(CAST(asistencia AS INT)) FROM SESION_JUGADOR")

    servicios.profesores.inactivar(id_profesor)

    assert _conteos(base) == antes
    assert bp.contar(base, "SESION", "id_profesor = ?", (id_profesor,)) == 12
    assert bp.contar(base, "PLANTILLA_PROFESOR", "id_profesor = ?", (id_profesor,)) == 2
    assert bp.escalar(base, "SELECT SUM(CAST(asistencia AS INT)) FROM SESION_JUGADOR") == asistencias_antes
    assert _huerfanas(base) == 0
    assert bp.escalar(base, "SELECT estado FROM PROFESOR WHERE id_profesor = ?", (id_profesor,)) == "inactivo"


def test_profesor_dado_de_baja_sale_de_los_desplegables_y_se_reactiva(siembra, servicios, base):
    id_profesor, _, _ = siembra.profesor_con_historial(sesiones=3, plantillas=1, jugadores=1)
    otro = siembra.profesor(nombres="Marta", apellidos="López")

    servicios.profesores.inactivar(id_profesor)
    opciones = [p.id_profesor for p in servicios.profesores.opciones()]
    assert id_profesor not in opciones and otro in opciones
    # Las sesiones siguen mostrando su nombre (historial legible)
    assert bp.contar(base, "SESION s JOIN PROFESOR p ON p.id_profesor = s.id_profesor",
                     "p.id_profesor = ?", (id_profesor,)) == 3

    servicios.profesores.reactivar(id_profesor)
    assert id_profesor in [p.id_profesor for p in servicios.profesores.opciones()]
    assert servicios.profesores.obtener(id_profesor).email.startswith("profe")   # sin reingresar datos


def test_baja_de_jugador_conserva_pagos_morosidad_asistencias_y_vinculos(siembra, servicios, base):
    j, t1, t2 = siembra.jugador_con_dos_tutores()
    id_concepto = siembra.concepto()
    id_morosidad = siembra.morosidad_de(j)
    siembra.pago(j, id_concepto, id_morosidad, mes=2)   # pago ligado a la morosidad
    siembra.pago(j, id_concepto, None, mes=3)
    siembra.pago(j, id_concepto, None, mes=4)
    id_profesor = siembra.profesor()
    id_cat, id_cancha = siembra.categoria(), siembra.cancha()
    id_pl = siembra.plantilla(id_cat)
    siembra.plantilla_jugador(id_pl, j, estado="inactivo")   # ya salió de la plantilla
    for dia in (1, 2):
        siembra.asistencia(siembra.sesion(id_profesor, id_cancha, id_cat, id_pl, dia), j)
    antes = _conteos(base)

    servicios.jugadores.inactivar(j)

    assert _conteos(base) == antes
    assert bp.contar(base, "PAGO", "id_jugador = ?", (j,)) == 3
    assert bp.contar(base, "MOROSIDAD", "id_jugador = ?", (j,)) == 1
    assert bp.contar(base, "JUGADOR_TUTOR", "id_jugador = ?", (j,)) == 2
    assert bp.escalar(base, "SELECT estado FROM JUGADOR WHERE id_jugador = ?", (j,)) == "inactivo"
    assert _huerfanas(base) == 0

    servicios.jugadores.reactivar(j)
    assert bp.escalar(base, "SELECT estado FROM JUGADOR WHERE id_jugador = ?", (j,)) == "activo"


def test_jugador_con_plantilla_activa_no_se_da_de_baja(siembra, servicios, base):
    j = siembra.jugador()
    siembra.plantilla_jugador(siembra.plantilla(siembra.categoria()), j, estado="activo")
    with pytest.raises(ReglaNegocioError, match="plantillas activas"):
        servicios.jugadores.inactivar(j)
    assert bp.escalar(base, "SELECT estado FROM JUGADOR WHERE id_jugador = ?", (j,)) == "activo"


def test_tutor_solo_se_da_de_baja_sin_jugadores_activos_y_conserva_sus_vinculos(siembra, servicios, base):
    j, t1, t2 = siembra.jugador_con_dos_tutores()
    with pytest.raises(ReglaNegocioError, match="jugadores activos"):
        servicios.tutores.inactivar(t2)

    siembra.ejecutar("UPDATE JUGADOR SET estado = 'inactivo' WHERE id_jugador = ?", (j,))
    servicios.tutores.inactivar(t2)
    assert bp.escalar(base, "SELECT estado FROM TUTOR WHERE id_tutor = ?", (t2,)) == "inactivo"
    assert bp.contar(base, "JUGADOR_TUTOR", "id_tutor = ?", (t2,)) == 1
    assert t2 not in [t.id_tutor for t in servicios.tutores.opciones()]


def test_ya_no_existe_ninguna_via_de_borrado_fisico(base):
    """La migración 001 retiró los procedimientos que borraban en cascada (P3)."""
    for procedimiento in ("SP_EliminarJugador", "SP_EliminarProfesor", "SP_EliminarTutor"):
        assert bp.escalar(base, "SELECT OBJECT_ID(?, 'P')", (procedimiento,)) is None
