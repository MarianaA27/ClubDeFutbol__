"""
Repositorios SQL (ADR-0001 y ADR-0005), verificados con una conexión falsa.

* Las búsquedas por documento se resuelven con WHERE en el motor.
* Las filas se convierten en entidades por nombre de columna.
* Cambiar el acudiente principal a un tutor no vinculado revierte todo.
"""
from datetime import date

import pytest

from paladinesfc.dominio import ReglaNegocioError
from paladinesfc.infraestructura.unidad_trabajo import UnidadDeTrabajoSql
from tests.fakes_bd import ConexionFalsa

COLS_PROFESOR = ["id_profesor", "nombres", "apellidos", "documento", "telefono",
                 "email", "especialidad", "estado", "fecha_ingreso"]


def test_busqueda_de_jugador_por_documento_usa_where_en_el_motor():
    conexion = ConexionFalsa(respuestas=[(["id_jugador", "documento"], [(4, "1020")])])
    with UnidadDeTrabajoSql(lambda: conexion) as uow:
        filas = uow.jugadores.listar_con_tutor_principal("1020")
    sql, parametros = conexion.ejecutadas[0]
    assert "WHERE j.documento LIKE ?" in sql
    assert parametros == ("%1020%",)
    assert filas == [{"id_jugador": 4, "documento": "1020"}]


def test_listado_sin_filtro_no_agrega_where():
    conexion = ConexionFalsa(respuestas=[(["id_jugador"], [])])
    with UnidadDeTrabajoSql(lambda: conexion) as uow:
        uow.jugadores.listar_con_tutor_principal()
    assert "WHERE" not in conexion.ejecutadas[0][0]


def test_obtener_profesor_mapea_por_nombre_y_trae_una_sola_fila():
    fila = (5, "Luisa", "Gómez", "33333", "300", "l@x.com", None, "activo", date(2023, 1, 15))
    conexion = ConexionFalsa(respuestas=[(COLS_PROFESOR, [fila])])
    with UnidadDeTrabajoSql(lambda: conexion) as uow:
        profesor = uow.profesores.obtener(5)
    sql, parametros = conexion.ejecutadas[0]
    assert "WHERE id_profesor = ?" in sql and parametros == (5,)
    assert profesor.documento == "33333" and profesor.estado == "activo"


def test_listar_profesores_activos_filtra_en_sql():
    conexion = ConexionFalsa(respuestas=[(COLS_PROFESOR, [])])
    with UnidadDeTrabajoSql(lambda: conexion) as uow:
        uow.profesores.listar(documento="333", solo_activos=True)
    sql, parametros = conexion.ejecutadas[0]
    assert "documento LIKE ?" in sql and "estado = 'activo'" in sql
    assert parametros == ("%333%",)


def test_principal_a_tutor_no_vinculado_revierte_el_primer_update():
    # el segundo UPDATE no afecta filas → la operación completa se revierte
    conexion = ConexionFalsa(filas_afectadas=0)
    with pytest.raises(ReglaNegocioError):
        with UnidadDeTrabajoSql(lambda: conexion) as uow:
            uow.vinculos.establecer_principal(7, 99)
            uow.commit()
    assert conexion.confirmadas == []
    assert conexion.rollbacks == 1


def test_existe_documento_excluye_el_propio_registro():
    conexion = ConexionFalsa(respuestas=[(["n"], [(0,)])])
    with UnidadDeTrabajoSql(lambda: conexion) as uow:
        assert uow.tutores.existe_documento("11111", excluir_id=3) is False
    sql, parametros = conexion.ejecutadas[0]
    assert "id_tutor <> ?" in sql and parametros == ("11111", 3)


def test_insertar_usa_scope_identity_en_el_mismo_lote():
    from paladinesfc.dominio import Tutor
    conexion = ConexionFalsa(respuestas=[(["id"], [(15,)])])
    tutor = Tutor.nuevo("Carlos", "Pérez", "11111", "3001111111", "a@x.com", "Calle 1")
    with UnidadDeTrabajoSql(lambda: conexion) as uow:
        assert uow.tutores.agregar(tutor) == 15
        uow.commit()
    sql, _ = conexion.ejecutadas[0]
    assert sql.startswith("SET NOCOUNT ON; INSERT INTO TUTOR")
    assert "SCOPE_IDENTITY()" in sql
    assert tutor.id_tutor == 15
