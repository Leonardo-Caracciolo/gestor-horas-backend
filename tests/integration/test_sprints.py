"""
tests/integration/test_sprints.py — Tests de integración para sprints.
"""
import pytest
from datetime import date, timedelta
from app.models.proyecto import Proyecto, TipoProyecto


def auth(t): return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def proyecto_sprint(client, token_admin, sqlite_session_factory):
    db = sqlite_session_factory()
    p = Proyecto(nombre="Proyecto Sprints Test", tipo=TipoProyecto.PROYECTO,
                 id_proyecto_excel="SPNT-001")
    db.add(p)
    db.commit()
    pid = p.id
    db.close()
    return pid


LUNES = date(2025, 1, 6)   # Fecha fija para no depender de la semana actual


@pytest.mark.integration
class TestCRUDSprint:
    def test_crear_sprint(self, client, token_admin, proyecto_sprint):
        res = client.post("/api/v1/sprints/", json={
            "nombre": "Sprint 1",
            "fecha_inicio": str(LUNES),
            "fecha_fin": str(LUNES + timedelta(days=13)),
            "proyecto_id": proyecto_sprint,
        }, headers=auth(token_admin))
        assert res.status_code == 201
        data = res.json()
        assert data["nombre"] == "Sprint 1"
        assert data["estado"] == "Planificado"

    def test_fechas_invalidas_retorna_422(self, client, token_admin, proyecto_sprint):
        res = client.post("/api/v1/sprints/", json={
            "nombre": "Sprint Roto",
            "fecha_inicio": str(LUNES + timedelta(days=13)),
            "fecha_fin": str(LUNES),  # fecha_fin < fecha_inicio
            "proyecto_id": proyecto_sprint,
        }, headers=auth(token_admin))
        assert res.status_code == 422

    def test_listar_sprints(self, client, token_admin, proyecto_sprint):
        res = client.get(f"/api/v1/sprints/?proyecto_id={proyecto_sprint}",
                         headers=auth(token_admin))
        assert res.status_code == 200
        assert len(res.json()) >= 1

    def test_obtener_sprint(self, client, token_admin, proyecto_sprint):
        c = client.post("/api/v1/sprints/", json={
            "nombre": "Sprint Get",
            "fecha_inicio": str(LUNES + timedelta(weeks=4)),
            "fecha_fin": str(LUNES + timedelta(weeks=4, days=13)),
            "proyecto_id": proyecto_sprint,
        }, headers=auth(token_admin))
        sid = c.json()["id"]
        res = client.get(f"/api/v1/sprints/{sid}", headers=auth(token_admin))
        assert res.status_code == 200
        assert res.json()["id"] == sid

    def test_obtener_inexistente_retorna_404(self, client, token_admin):
        assert client.get("/api/v1/sprints/99999", headers=auth(token_admin)).status_code == 404


@pytest.mark.integration
class TestCicloVidaSprint:
    @pytest.fixture(scope="class")
    def sprint_planificado(self, client, token_admin, proyecto_sprint):
        res = client.post("/api/v1/sprints/", json={
            "nombre": "Sprint Ciclo",
            "fecha_inicio": str(LUNES + timedelta(weeks=8)),
            "fecha_fin": str(LUNES + timedelta(weeks=8, days=13)),
            "proyecto_id": proyecto_sprint,
        }, headers=auth(token_admin))
        assert res.status_code == 201
        return res.json()["id"]

    def test_activar_sprint(self, client, token_admin, sprint_planificado):
        res = client.post(f"/api/v1/sprints/{sprint_planificado}/activar",
                          headers=auth(token_admin))
        assert res.status_code == 200
        assert res.json()["estado"] == "Activo"

    def test_no_puede_activar_dos_veces(self, client, token_admin, proyecto_sprint):
        # Crear otro sprint planificado e intentar activarlo cuando ya hay uno activo
        c = client.post("/api/v1/sprints/", json={
            "nombre": "Sprint Conflicto",
            "fecha_inicio": str(LUNES + timedelta(weeks=12)),
            "fecha_fin": str(LUNES + timedelta(weeks=12, days=13)),
            "proyecto_id": proyecto_sprint,
        }, headers=auth(token_admin))
        sid2 = c.json()["id"]
        res = client.post(f"/api/v1/sprints/{sid2}/activar", headers=auth(token_admin))
        assert res.status_code == 400
        assert "activo" in res.json()["detail"].lower()

    def test_cerrar_sprint(self, client, token_admin, sprint_planificado):
        res = client.post(f"/api/v1/sprints/{sprint_planificado}/cerrar",
                          headers=auth(token_admin))
        assert res.status_code == 200
        assert res.json()["estado"] == "Cerrado"

    def test_no_puede_modificar_sprint_cerrado(self, client, token_admin, sprint_planificado):
        res = client.put(f"/api/v1/sprints/{sprint_planificado}",
                         json={"nombre": "Cambio Post-Cierre"},
                         headers=auth(token_admin))
        assert res.status_code == 400
        assert "cerrado" in res.json()["detail"].lower()
