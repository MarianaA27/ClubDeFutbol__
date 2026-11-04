"""La API REST de extremo a extremo contra SQL Server real (TestClient + servicios reales)."""
import pytest
from fastapi.testclient import TestClient

from paladinesfc.presentacion.api import crear_app
from tests.integracion import base_prueba as bp

pytestmark = pytest.mark.integracion


def test_flujo_del_mvp_por_http_contra_sql_server(servicios, base):
    cliente = TestClient(crear_app(servicios))
    id_tutor = cliente.post("/tutores", json={
        "nombres": "Carlos", "apellidos": "Pérez", "documento": "11111", "telefono": "3001111111",
        "email": "carlos@correo.com", "direccion": "Calle 10"}).json()["id"]
    respuesta = cliente.post("/jugadores", json={
        "nombres": "Samuel", "apellidos": "Rojas", "documento": "1020304050",
        "fecha_nacimiento": "2015-05-10", "fecha_ingreso": "2024-02-01", "talla_uniforme": "S",
        "eps": "Sura", "id_tutor": id_tutor, "parentesco": "Padre"})
    assert respuesta.status_code == 201, respuesta.text
    id_jugador = respuesta.json()["id"]

    assert cliente.get("/jugadores", params={"documento": "1020304050"}).json()[0]["eps"] == "Sura"
    assert cliente.post(f"/jugadores/{id_jugador}/baja").json()["estado"] == "inactivo"
    assert bp.contar(base, "MOROSIDAD", "id_jugador = ?", (id_jugador,)) == 1   # historial intacto
    assert cliente.post("/tutores", json={
        "nombres": "Otro", "apellidos": "Tutor", "documento": "11111", "telefono": "3009999999",
        "email": "o@correo.com", "direccion": "Calle 1"}).status_code == 400
