"""
tests/integration/test_feriados.py — Tests de integración para feriados.
Usa token_admin del conftest (rol Admin tiene permiso admin_feriados).
"""
import pytest


def auth(token): return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestFeriados:
    FECHA = "2024-09-16"   # Independencia MX (año pasado, sin riesgo de colisión)

    def test_crear_feriado(self, client, token_admin):
        res = client.post("/api/v1/feriados/", json={
            "fecha": self.FECHA,
            "nombre": "Día de la Independencia",
        }, headers=auth(token_admin))
        assert res.status_code == 201
        data = res.json()
        assert data["nombre"] == "Día de la Independencia"
        assert data["anio"] == 2024

    def test_crear_feriado_duplicado_retorna_400(self, client, token_admin):
        res = client.post("/api/v1/feriados/", json={
            "fecha": self.FECHA,
            "nombre": "Duplicado",
        }, headers=auth(token_admin))
        assert res.status_code == 400

    def test_listar_feriados_por_año(self, client, token_admin):
        res = client.get("/api/v1/feriados/?anio=2024", headers=auth(token_admin))
        assert res.status_code == 200
        assert any(f["nombre"] == "Día de la Independencia" for f in res.json())

    def test_actualizar_feriado(self, client, token_admin):
        res = client.post("/api/v1/feriados/", json={
            "fecha": "2024-11-02",
            "nombre": "Día de Muertos original",
        }, headers=auth(token_admin))
        fid = res.json()["id"]
        res = client.put(f"/api/v1/feriados/{fid}",
                         json={"nombre": "Día de Muertos"},
                         headers=auth(token_admin))
        assert res.status_code == 200
        assert res.json()["nombre"] == "Día de Muertos"

    def test_eliminar_feriado(self, client, token_admin):
        res = client.post("/api/v1/feriados/", json={
            "fecha": "2024-12-25",
            "nombre": "Navidad",
        }, headers=auth(token_admin))
        fid = res.json()["id"]
        res = client.delete(f"/api/v1/feriados/{fid}", headers=auth(token_admin))
        assert res.status_code == 204

    def test_sin_permiso_retorna_403(self, client, token_prof):
        res = client.post("/api/v1/feriados/", json={
            "fecha": "2024-01-01",
            "nombre": "Año Nuevo",
        }, headers=auth(token_prof))
        assert res.status_code == 403
