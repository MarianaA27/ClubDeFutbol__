"""
Repositorios y servicios del MVP contra SQL Server REAL (ADR-0001, ADR-0004, ADR-0005).

Comprueban lo que los dobles en memoria no pueden: el SQL real, el trigger de
morosidad, los índices únicos de la migración 001 y el filtrado en el motor.
"""
import pytest

from paladinesfc.dominio.errores import ReglaNegocioError
from tests.integracion import base_prueba as bp

pytestmark = pytest.mark.integracion


def test_registrar_jugador_devuelve_su_id_aunque_el_trigger_inserte_en_morosidad(siembra, servicios, base):
    """SCOPE_IDENTITY(): @@IDENTITY devolvería el id de MOROSIDAD que inserta TR_NuevoJugador_Morosidad."""
    siembra.jugador()                       # desalinea las secuencias de JUGADOR y MOROSIDAD
    siembra.ejecutar("INSERT INTO MOROSIDAD (id_jugador, fecha_vencimiento, estado_mora) "
                     "SELECT MIN(id_jugador), GETDATE(), 'pendiente' FROM JUGADOR")
    id_tutor = siembra.tutor()
    id_jugador = servicios.jugadores.registrar_con_tutor(
        "Samuel", "Rojas", "1020304050", "2015-05-10", "9", "S", "2024-02-01", None, id_tutor, "Padre")

    assert bp.escalar(base, "SELECT documento FROM JUGADOR WHERE id_jugador = ?", (id_jugador,)) == "1020304050"
    assert bp.contar(base, "MOROSIDAD", "id_jugador = ?", (id_jugador,)) == 1   # trigger
    assert bp.principales_de(base, id_jugador) == [id_tutor]


def test_busqueda_por_documento_se_filtra_en_el_motor(siembra, servicios):
    for k in range(30):
        siembra.tutor(nombres="Tutor", apellidos=f"Número {k}", documento=f"{55500 + k}", telefono=f"30055500{k:02d}")
    encontrados = servicios.tutores.listar("5551")
    assert sorted(t.documento for t in encontrados) == [f"{55510 + k}" for k in range(10)]


def test_homonimos_el_vinculo_apunta_al_tutor_seleccionado(siembra, servicios, base):
    siembra.tutor("Carlos", "Pérez", documento="11111", telefono="3001111111")
    segundo = siembra.tutor("Carlos", "Pérez", documento="22222", telefono="3002222222")
    etiquetas = {t.etiqueta: t.id_tutor for t in servicios.tutores.opciones()}
    assert etiquetas["Carlos Pérez — CC 22222"] == segundo

    id_jugador = servicios.jugadores.registrar_con_tutor(
        "Samuel", "Rojas", "1020304051", "2015-05-10", None, "S", "2024-02-01", None,
        etiquetas["Carlos Pérez — CC 22222"], "Padre")
    assert bp.principales_de(base, id_jugador) == [segundo]


def test_edicion_lee_por_nombre_de_columna_una_sola_fila(siembra, servicios):
    for _ in range(20):
        siembra.profesor()
    objetivo = siembra.profesor(nombres="Marta", apellidos="López", documento="90909", telefono="3109090909")
    profesor = servicios.profesores.obtener(objetivo)
    assert (profesor.nombres, profesor.documento, profesor.telefono) == ("Marta", "90909", "3109090909")


def test_documento_y_telefono_duplicados_dan_mensaje_claro_y_no_error_de_pyodbc(siembra, servicios):
    siembra.tutor(documento="33333", telefono="3003333333")
    with pytest.raises(ReglaNegocioError, match="documento"):
        servicios.tutores.registrar("Ana", "Ruiz", "33333", "3004444444", "a@correo.com", "Calle 2")
    with pytest.raises(ReglaNegocioError, match="teléfono"):
        servicios.tutores.registrar("Ana", "Ruiz", "44444", "3003333333", "a@correo.com", "Calle 2")


def test_el_motor_impide_dos_acudientes_principales(siembra, base):
    """Defensa en profundidad (ADR-0004): índice filtrado UX_JT_un_principal de la migración 001."""
    pyodbc = bp._pyodbc()
    j, _, t2 = siembra.jugador_con_dos_tutores()
    with pytest.raises(pyodbc.IntegrityError):
        siembra.ejecutar("UPDATE JUGADOR_TUTOR SET acudiente_principal = 1 WHERE id_jugador = ? AND id_tutor = ?",
                         (j, t2))
    assert len(bp.principales_de(base, j)) == 1


def test_flujo_de_vinculacion_completo(siembra, servicios, base):
    j, t1, t2 = siembra.jugador_con_dos_tutores()
    t3 = siembra.tutor("Rosa", "Díaz")
    servicios.vinculacion.vincular(j, t3, "Abuelo/a", como_principal=False)
    tutores = servicios.vinculacion.tutores_de(j)
    assert tutores.principal.id_tutor == t1 and len(tutores.vinculos) == 3

    principal = tutores.principal.id_jugador_tutor
    with pytest.raises(ReglaNegocioError, match="acudiente principal"):
        servicios.vinculacion.desvincular(principal)

    vinculo_t3 = next(v.id_jugador_tutor for v in tutores.vinculos if v.id_tutor == t3)
    servicios.vinculacion.desvincular(vinculo_t3)
    assert bp.contar(base, "JUGADOR_TUTOR", "id_jugador = ?", (j,)) == 2
