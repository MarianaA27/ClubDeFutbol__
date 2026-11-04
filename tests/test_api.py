"""
API REST del MVP (issue #37) probada con TestClient y la unidad de trabajo en memoria.

La API es un adaptador más de la presentación: recibe los MISMOS servicios que la
interfaz de escritorio. Estas pruebas recorren los casos de uso del MVP por HTTP.
"""
import pytest
from fastapi.testclient import TestClient

from paladinesfc.presentacion.api import crear_app
from paladinesfc.presentacion.contenedor import crear_servicios
from tests.fakes_repositorios import Almacen, fabrica

TUTOR = {"nombres": "Carlos", "apellidos": "Pérez", "documento": "11111", "telefono": "3001111111",
         "email": "carlos@correo.com", "direccion": "Calle 10 # 20-30"}
PROFESOR = {"nombres": "Andrés", "apellidos": "Gómez", "documento": "80001", "telefono": "3101234567",
            "email": "andres@correo.com", "especialidad": "Técnico", "fecha_ingreso": "2023-01-15"}


def _jugador(id_tutor, documento="1020304050", **extra):
    datos = {"nombres": "Samuel", "apellidos": "Rojas", "documento": documento,
             "fecha_nacimiento": "2015-05-10", "fecha_ingreso": "2024-02-01", "talla_uniforme": "S",
             "numero_preferido": 9, "eps": "Sura", "id_tutor": id_tutor, "parentesco": "Padre"}
    datos.update(extra)
    return datos


@pytest.fixture
def cliente():
    return TestClient(crear_app(crear_servicios(fabrica(Almacen()))))


@pytest.fixture
def id_tutor(cliente):
    return cliente.post("/tutores", json=TUTOR).json()["id"]


def test_salud_y_documentacion_swagger(cliente):
    assert cliente.get("/salud").json() == {"estado": "ok"}
    rutas = cliente.get("/openapi.json").json()["paths"]
    for ruta in ("/jugadores", "/jugadores/{id_jugador}/tutores/principal", "/tutores", "/profesores/activos"):
        assert ruta in rutas
    assert cliente.get("/docs").status_code == 200


# ── Tutores ────────────────────────────────────────────────────────────────
def test_registrar_consultar_editar_y_buscar_tutor(cliente, id_tutor):
    tutor = cliente.get(f"/tutores/{id_tutor}").json()
    assert tutor["etiqueta"] == "Carlos Pérez — CC 11111" and tutor["estado"] == "activo"

    editado = cliente.put(f"/tutores/{id_tutor}", json={**TUTOR, "direccion": "Carrera 5"}).json()
    assert editado["direccion"] == "Carrera 5"

    assert [t["documento"] for t in cliente.get("/tutores", params={"documento": "111"}).json()] == ["11111"]
    assert cliente.get("/tutores", params={"documento": "999"}).json() == []


def test_regla_de_negocio_responde_400_con_mensaje_claro(cliente, id_tutor):
    respuesta = cliente.post("/tutores", json=TUTOR)
    assert respuesta.status_code == 400
    assert respuesta.json() == {"detalle": "Ya existe un tutor con el documento '11111'."}


def test_formato_invalido_lo_rechaza_el_dominio(cliente):
    respuesta = cliente.post("/tutores", json={**TUTOR, "email": "sin-arroba"})
    assert respuesta.status_code == 400 and "Email" in respuesta.json()["detalle"]


def test_json_incompleto_responde_422(cliente):
    assert cliente.post("/tutores", json={"nombres": "Solo nombre"}).status_code == 422


def test_inexistente_responde_404(cliente):
    respuesta = cliente.get("/jugadores/999")
    assert respuesta.status_code == 404 and respuesta.json()["detalle"] == "Jugador no encontrado."


# ── Jugadores ──────────────────────────────────────────────────────────────
def test_registrar_jugador_con_tutor_y_listarlo(cliente, id_tutor):
    respuesta = cliente.post("/jugadores", json=_jugador(id_tutor))
    assert respuesta.status_code == 201
    id_jugador = respuesta.json()["id"]

    jugador = cliente.get(f"/jugadores/{id_jugador}").json()
    assert jugador["documento"] == "1020304050" and jugador["eps"] == "Sura"
    listado = cliente.get("/jugadores", params={"documento": "10203"}).json()
    assert listado[0]["tutor_principal"] == "Carlos Pérez" and listado[0]["parentesco"] == "Padre"


def test_editar_dar_de_baja_y_reactivar_jugador(cliente, id_tutor):
    id_jugador = cliente.post("/jugadores", json=_jugador(id_tutor)).json()["id"]
    edicion = {"nombres": "Samuel", "apellidos": "Rojas", "talla_uniforme": "M", "estado": "activo",
               "numero_preferido": 10, "observaciones": None, "eps": "Nueva EPS"}
    assert cliente.put(f"/jugadores/{id_jugador}", json=edicion).json()["talla_uniforme"] == "M"

    assert cliente.post(f"/jugadores/{id_jugador}/baja").json()["estado"] == "inactivo"
    assert cliente.get(f"/jugadores/{id_jugador}").status_code == 200       # no se borró
    assert cliente.post(f"/jugadores/{id_jugador}/reactivacion").json()["estado"] == "activo"


def test_registrar_jugador_con_tutor_inexistente_no_crea_nada(cliente):
    respuesta = cliente.post("/jugadores", json=_jugador(999))
    assert respuesta.status_code == 400
    assert cliente.get("/jugadores").json() == []


def test_detalle_de_jugador(cliente, id_tutor):
    id_jugador = cliente.post("/jugadores", json=_jugador(id_tutor)).json()["id"]
    detalle = cliente.get(f"/jugadores/{id_jugador}/detalle").json()
    assert detalle["jugador"]["id_jugador"] == id_jugador
    assert detalle["tutores"][0]["acudiente_principal"] is True
    assert detalle["plantillas_activas"] == []


# ── Jugador–Tutor ──────────────────────────────────────────────────────────
def test_flujo_de_vinculacion(cliente, id_tutor):
    id_jugador = cliente.post("/jugadores", json=_jugador(id_tutor)).json()["id"]
    madre = cliente.post("/tutores", json={**TUTOR, "nombres": "Laura", "documento": "22222",
                                           "telefono": "3002222222"}).json()["id"]
    assert cliente.post(f"/jugadores/{id_jugador}/tutores",
                        json={"id_tutor": madre, "parentesco": "Madre"}).status_code == 201

    vinculos = cliente.put(f"/jugadores/{id_jugador}/tutores/principal", json={"id_tutor": madre}).json()
    assert [v["id_tutor"] for v in vinculos if v["acudiente_principal"]] == [madre]

    principal = next(v for v in vinculos if v["acudiente_principal"])
    otro = next(v for v in vinculos if not v["acudiente_principal"])
    bloqueado = cliente.delete(f"/jugadores/{id_jugador}/tutores/{principal['id_jugador_tutor']}")
    assert bloqueado.status_code == 400 and "acudiente principal" in bloqueado.json()["detalle"]

    assert cliente.delete(f"/jugadores/{id_jugador}/tutores/{otro['id_jugador_tutor']}").status_code == 204
    assert len(cliente.get(f"/jugadores/{id_jugador}/tutores").json()) == 1


def test_no_se_vincula_dos_veces_el_mismo_tutor(cliente, id_tutor):
    id_jugador = cliente.post("/jugadores", json=_jugador(id_tutor)).json()["id"]
    respuesta = cliente.post(f"/jugadores/{id_jugador}/tutores", json={"id_tutor": id_tutor, "parentesco": "Padre"})
    assert respuesta.status_code == 400 and "ya está vinculado" in respuesta.json()["detalle"]


def test_no_se_desvincula_un_vinculo_de_otro_jugador(cliente, id_tutor):
    j1 = cliente.post("/jugadores", json=_jugador(id_tutor)).json()["id"]
    j2 = cliente.post("/jugadores", json=_jugador(id_tutor, documento="1020304051")).json()["id"]
    vinculo_de_j1 = cliente.get(f"/jugadores/{j1}/tutores").json()[0]["id_jugador_tutor"]
    assert cliente.delete(f"/jugadores/{j2}/tutores/{vinculo_de_j1}").status_code == 404


# ── Profesores ─────────────────────────────────────────────────────────────
def test_flujo_de_profesor_con_baja_logica(cliente):
    id_profesor = cliente.post("/profesores", json=PROFESOR).json()["id"]
    edicion = {k: v for k, v in PROFESOR.items() if k != "fecha_ingreso"} | {"estado": "activo",
                                                                              "especialidad": "Arquero"}
    assert cliente.put(f"/profesores/{id_profesor}", json=edicion).json()["especialidad"] == "Arquero"

    assert cliente.post(f"/profesores/{id_profesor}/baja").json()["estado"] == "inactivo"
    assert cliente.get("/profesores/activos").json() == []
    assert len(cliente.get("/profesores").json()) == 1                     # sigue registrado
    cliente.post(f"/profesores/{id_profesor}/reactivacion")
    assert [p["id_profesor"] for p in cliente.get("/profesores/activos").json()] == [id_profesor]
    assert cliente.get(f"/profesores/{id_profesor}/plantillas").json() == []


def test_baja_de_tutor_con_jugadores_activos_responde_400(cliente, id_tutor):
    cliente.post("/jugadores", json=_jugador(id_tutor))
    respuesta = cliente.post(f"/tutores/{id_tutor}/baja")
    assert respuesta.status_code == 400 and "jugadores activos" in respuesta.json()["detalle"]
    assert cliente.get(f"/tutores/{id_tutor}/jugadores").json() == []


def test_error_de_infraestructura_responde_500_sin_exponer_detalles():
    def fabrica_rota(operacion):
        raise RuntimeError("SERVER=GIANY no responde")
    cliente = TestClient(crear_app(crear_servicios(fabrica_rota)), raise_server_exceptions=False)
    respuesta = cliente.get("/tutores")
    assert respuesta.status_code == 500
    assert "GIANY" not in respuesta.text
