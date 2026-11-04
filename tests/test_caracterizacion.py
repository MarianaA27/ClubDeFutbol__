"""
Pruebas de caracterización de las 18 operaciones del MVP (issue #14).

Cada prueba fija el comportamiento OBSERVABLE de una operación de la tabla 1.4 del
Entregable 1, tal como queda después de la re-arquitectura. La comparación con el
sistema original, operación por operación, está en docs/evaluacion/caracterizacion.md:

* "Se conserva": el resultado para la usuaria es el mismo que en el sistema original.
* "Cambio deliberado": corrige un defecto documentado (P1–P5) y la prueba lo fija.

Se ejecutan con la unidad de trabajo en memoria; las mismas reglas se validan contra
SQL Server en tests/integracion/.
"""
from datetime import date

import pytest

from paladinesfc.dominio import ReglaNegocioError
from paladinesfc.dominio.errores import NoEncontradoError
from paladinesfc.presentacion.contenedor import crear_servicios
from tests.fakes_repositorios import Almacen, fabrica

COLUMNAS_LISTADO_JUGADORES = {"id_jugador", "jugador", "documento", "estado", "fecha_nacimiento",
                              "talla_uniforme", "tutor_principal", "parentesco", "telefono_tutor"}


@pytest.fixture
def almacen():
    return Almacen()


@pytest.fixture
def s(almacen):
    return crear_servicios(fabrica(almacen))


def _tutor(s, doc="11111", tel="3001111111", nombres="Carlos"):
    return s.tutores.registrar(nombres, "Pérez", doc, tel, "c@correo.com", "Calle 1")


def _jugador(s, id_tutor, doc="1020304050"):
    return s.jugadores.registrar_con_tutor("Samuel", "Rojas", doc, "2015-05-10", "9", "S",
                                           "2024-02-01", None, id_tutor, "Padre")


def _profesor(s, doc="80001", tel="3101234567"):
    return s.profesores.registrar("Andrés", "Gómez", doc, tel, "a@correo.com", "Técnico", "2023-01-15")


# ── Jugadores ──────────────────────────────────────────────────────────────
def test_op01_listado_de_jugadores_con_su_tutor_principal_conserva_sus_columnas(s):
    _jugador(s, _tutor(s))
    fila = s.jugadores.listar()[0]
    assert COLUMNAS_LISTADO_JUGADORES <= set(fila)          # mismas columnas del original (+ EPS)
    assert (fila["tutor_principal"], fila["parentesco"]) == ("Carlos Pérez", "Padre")


def test_op01_jugador_sin_tutor_se_muestra_como_en_el_original(s, almacen):
    id_jugador = _jugador(s, _tutor(s))
    almacen.vinculos.clear()                                  # dato heredado sin vínculo
    fila = next(f for f in s.jugadores.listar() if f["id_jugador"] == id_jugador)
    assert (fila["tutor_principal"], fila["parentesco"], fila["telefono_tutor"]) == ("Sin tutor", "-", "-")


def test_op02_detalle_completo_trae_datos_tutores_y_plantillas(s):
    id_jugador = _jugador(s, _tutor(s))
    jugador, tutores, plantillas = s.jugadores.detalle(id_jugador)
    assert jugador.documento == "1020304050"
    assert tutores.principal is not None and tutores.es_consistente()
    assert plantillas == []


def test_op03_registrar_jugador_crea_jugador_y_acudiente_principal_juntos(s, almacen):
    id_tutor = _tutor(s)
    commits = almacen.commits
    id_jugador = _jugador(s, id_tutor)
    assert almacen.commits == commits + 1                     # una sola transacción
    assert s.vinculacion.tutores_de(id_jugador).principal is not None
    assert s.jugadores.obtener(id_jugador).estado == "activo"  # siempre nace activo


def test_op03_mensajes_de_validacion_del_original_se_conservan(s):
    id_tutor = _tutor(s)
    _jugador(s, id_tutor)
    with pytest.raises(ReglaNegocioError, match="Ya existe un jugador con el documento '1020304050'"):
        _jugador(s, id_tutor)
    with pytest.raises(ReglaNegocioError, match="fecha de ingreso debe ser posterior"):
        s.jugadores.registrar_con_tutor("Ana", "Ruiz", "55555", "2015-05-10", None, "S",
                                        "2010-01-01", None, id_tutor, "Madre")


def test_op04_editar_jugador_no_cambia_documento_ni_fechas(s):
    id_jugador = _jugador(s, _tutor(s))
    s.jugadores.actualizar(id_jugador, "Samuel", "Rojas", "10", "m", "lesionado", "Tobillo")
    j = s.jugadores.obtener(id_jugador)
    assert (j.talla_uniforme, j.estado, j.numero_preferido) == ("M", "lesionado", 10)
    assert (j.documento, j.fecha_nacimiento) == ("1020304050", date(2015, 5, 10))


def test_op05_dar_de_baja_jugador_ya_no_borra_cambio_deliberado(s, almacen):
    id_jugador = _jugador(s, _tutor(s))
    s.jugadores.inactivar(id_jugador)
    assert id_jugador in almacen.jugadores and s.jugadores.obtener(id_jugador).estado == "inactivo"


def test_op05_se_conserva_el_bloqueo_por_plantillas_activas(s, almacen):
    id_jugador = _jugador(s, _tutor(s))
    almacen.plantillas_activas[id_jugador] = 1
    with pytest.raises(ReglaNegocioError, match="plantillas activas"):
        s.jugadores.inactivar(id_jugador)


def test_op06_buscar_por_documento_coincide_por_fragmento_como_el_original(s):
    id_tutor = _tutor(s)
    _jugador(s, id_tutor, "1020304050")
    _jugador(s, id_tutor, "9988776655")
    assert [f["documento"] for f in s.jugadores.listar("0304")] == ["1020304050"]
    assert s.jugadores.listar("000000") == []


# ── Jugador–Tutor ──────────────────────────────────────────────────────────
def test_op07_vincular_tutor_y_rechazar_duplicado(s):
    t1, t2 = _tutor(s), _tutor(s, "22222", "3002222222", "Laura")
    id_jugador = _jugador(s, t1)
    s.vinculacion.vincular(id_jugador, t2, "Madre", como_principal=False)
    assert len(s.vinculacion.tutores_de(id_jugador).vinculos) == 2
    with pytest.raises(ReglaNegocioError, match="ya está vinculado"):
        s.vinculacion.vincular(id_jugador, t2, "Madre", como_principal=False)


def test_op07_vincular_como_principal_desmarca_al_anterior(s):
    t1, t2 = _tutor(s), _tutor(s, "22222", "3002222222", "Laura")
    id_jugador = _jugador(s, t1)
    s.vinculacion.vincular(id_jugador, t2, "Madre", como_principal=True)
    assert s.vinculacion.tutores_de(id_jugador).principal.id_tutor == t2


def test_op08_cambiar_principal_a_un_tutor_no_vinculado_ya_no_deja_al_jugador_sin_principal(s):
    """Defecto original: el 2.º UPDATE no afectaba filas y el jugador quedaba sin principal."""
    t1, t2 = _tutor(s), _tutor(s, "22222", "3002222222", "Laura")
    id_jugador = _jugador(s, t1)
    with pytest.raises(NoEncontradoError):
        s.vinculacion.cambiar_principal(id_jugador, t2)
    assert s.vinculacion.tutores_de(id_jugador).principal.id_tutor == t1


def test_op09_desvincular_al_acudiente_principal_se_bloquea_cambio_deliberado(s):
    """Defecto original: delete_jugador_tutor() leía acudiente_principal y no lo usaba."""
    t1, t2 = _tutor(s), _tutor(s, "22222", "3002222222", "Laura")
    id_jugador = _jugador(s, t1)
    s.vinculacion.vincular(id_jugador, t2, "Madre", como_principal=False)
    vinculos = s.vinculacion.tutores_de(id_jugador).vinculos
    principal = next(v for v in vinculos if v.acudiente_principal)
    with pytest.raises(ReglaNegocioError, match="acudiente principal"):
        s.vinculacion.desvincular(principal.id_jugador_tutor)
    otro = next(v for v in vinculos if not v.acudiente_principal)
    s.vinculacion.desvincular(otro.id_jugador_tutor)
    assert len(s.vinculacion.tutores_de(id_jugador).vinculos) == 1


def test_op09_se_conserva_el_bloqueo_del_unico_tutor(s):
    id_jugador = _jugador(s, _tutor(s))
    unico = s.vinculacion.tutores_de(id_jugador).vinculos[0]
    with pytest.raises(ReglaNegocioError, match="único tutor"):
        s.vinculacion.desvincular(unico.id_jugador_tutor)


def test_op10_tutores_de_un_jugador_con_el_principal_primero(s):
    t1, t2 = _tutor(s), _tutor(s, "22222", "3002222222", "Laura")
    id_jugador = _jugador(s, t1)
    s.vinculacion.vincular(id_jugador, t2, "Madre", como_principal=False)
    tutores = s.vinculacion.tutores_de(id_jugador)
    assert tutores.es_consistente() and tutores.principal.id_tutor == t1


# ── Tutores ────────────────────────────────────────────────────────────────
def test_op11_listado_de_tutores_y_busqueda_por_documento(s):
    _tutor(s)
    _tutor(s, "22222", "3002222222", "Laura")
    assert len(s.tutores.listar()) == 2
    assert [t.documento for t in s.tutores.listar("222")] == ["22222"]


def test_op12_registrar_tutor_con_telefono_repetido_da_mensaje_claro(s):
    """Antes: error crudo de pyodbc por la restricción UNIQUE. Ahora: mensaje para la usuaria."""
    _tutor(s)
    with pytest.raises(ReglaNegocioError, match="teléfono"):
        _tutor(s, doc="22222", tel="3001111111")


def test_op13_editar_tutor(s):
    id_tutor = _tutor(s)
    s.tutores.actualizar(id_tutor, "Carlos", "Pérez", "11111", "3001111111", "nuevo@correo.com", "Carrera 9")
    assert s.tutores.obtener(id_tutor).direccion == "Carrera 9"


def test_op14_dar_de_baja_tutor_cambio_deliberado(s):
    """Antes: borrado físico, bloqueado si tenía CUALQUIER vínculo. Ahora: inactivo, bloqueado si tiene jugadores activos."""
    id_tutor = _tutor(s)
    id_jugador = _jugador(s, id_tutor)
    with pytest.raises(ReglaNegocioError, match="jugadores activos"):
        s.tutores.inactivar(id_tutor)
    s.jugadores.inactivar(id_jugador)
    s.tutores.inactivar(id_tutor)
    assert s.tutores.obtener(id_tutor).estado == "inactivo"
    assert id_tutor not in [t.id_tutor for t in s.tutores.opciones()]


# ── Profesores ─────────────────────────────────────────────────────────────
def test_op15_listado_de_profesores(s):
    _profesor(s)
    assert [p.documento for p in s.profesores.listar()] == ["80001"]


def test_op16_registrar_profesor_valida_y_nace_activo(s):
    id_profesor = _profesor(s)
    assert s.profesores.obtener(id_profesor).estado == "activo"
    with pytest.raises(ReglaNegocioError, match="Ya existe otro profesor con el documento"):
        _profesor(s, tel="3109999999")


def test_op17_editar_profesor_incluye_el_documento(s):
    """SP_ActualizarProfesor (huérfano) no recibía el documento; la vía única sí lo permite."""
    id_profesor = _profesor(s)
    s.profesores.actualizar(id_profesor, "Andrés", "Gómez", "80002", "3101234567", "a@correo.com",
                            "Arquero", "activo")
    assert s.profesores.obtener(id_profesor).documento == "80002"


def test_op18_dar_de_baja_profesor_no_borra_y_sale_de_los_desplegables(s, almacen):
    id_profesor = _profesor(s)
    s.profesores.inactivar(id_profesor)
    assert id_profesor in almacen.profesores
    assert s.profesores.opciones() == []
    s.profesores.reactivar(id_profesor)
    assert [p.id_profesor for p in s.profesores.opciones()] == [id_profesor]
