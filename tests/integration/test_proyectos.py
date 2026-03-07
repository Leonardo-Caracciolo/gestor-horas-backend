"""
tests/integration/test_proyectos.py — Tests de integración para proyectos.
Usa token_admin (tiene permiso admin_proyectos) del conftest.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.models.proyecto import Proyecto, TipoProyecto
from app.models.ado_item import AdoItem, TipoAdoItem


def auth(t): return {"Authorization": f"Bearer {t}"}


@pytest.mark.integration
class TestCRUDProyecto:
    def test_crear_proyecto(self, client, token_admin):
        res = client.post("/api/v1/proyectos/", json={
            "nombre": "CRM Nuevo", "tipo": "Proyecto",
            "id_proyecto_excel": "CRM-001", "ado_project_name": "CRM",
        }, headers=auth(token_admin))
        assert res.status_code == 201
        assert res.json()["id_proyecto_excel"] == "CRM-001"

    def test_codigo_excel_unico(self, client, token_admin):
        res = client.post("/api/v1/proyectos/", json={
            "nombre": "Dup", "tipo": "Proyecto",
            "id_proyecto_excel": "CRM-001",
        }, headers=auth(token_admin))
        assert res.status_code == 400

    def test_listar_proyectos_activos(self, client, token_admin):
        res = client.get("/api/v1/proyectos/", headers=auth(token_admin))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_obtener_proyecto(self, client, token_admin):
        c = client.post("/api/v1/proyectos/", json={
            "nombre": "Para obtener", "tipo": "Oficina",
            "id_proyecto_excel": "OF-GET-01",
        }, headers=auth(token_admin))
        pid = c.json()["id"]
        res = client.get(f"/api/v1/proyectos/{pid}", headers=auth(token_admin))
        assert res.status_code == 200
        assert res.json()["id"] == pid

    def test_obtener_inexistente_retorna_404(self, client, token_admin):
        assert client.get("/api/v1/proyectos/99999", headers=auth(token_admin)).status_code == 404

    def test_actualizar_proyecto(self, client, token_admin):
        c = client.post("/api/v1/proyectos/", json={
            "nombre": "Para actualizar", "tipo": "Proyecto",
            "id_proyecto_excel": "UPDT-001",
        }, headers=auth(token_admin))
        pid = c.json()["id"]
        res = client.put(f"/api/v1/proyectos/{pid}", json={"nombre": "Actualizado"},
                         headers=auth(token_admin))
        assert res.status_code == 200
        assert res.json()["nombre"] == "Actualizado"

    def test_desactivar_proyecto(self, client, token_admin):
        c = client.post("/api/v1/proyectos/", json={
            "nombre": "Para desactivar", "tipo": "Oficina",
            "id_proyecto_excel": "DEL-001",
        }, headers=auth(token_admin))
        pid = c.json()["id"]
        res = client.delete(f"/api/v1/proyectos/{pid}", headers=auth(token_admin))
        assert res.status_code == 204

    def test_sin_permiso_retorna_403(self, client, token_prof):
        res = client.post("/api/v1/proyectos/", json={
            "nombre": "Hack", "tipo": "Proyecto",
            "id_proyecto_excel": "HACK-001",
        }, headers=auth(token_prof))
        assert res.status_code == 403


@pytest.mark.integration
class TestSyncADO:
    def test_sync_sin_ado_project_name_retorna_400(self, client, token_admin):
        c = client.post("/api/v1/proyectos/", json={
            "nombre": "Sin ADO", "tipo": "Proyecto",
            "id_proyecto_excel": "NOADO-001",
        }, headers=auth(token_admin))
        pid = c.json()["id"]
        res = client.post(f"/api/v1/proyectos/{pid}/sync-ado", headers=auth(token_admin))
        assert res.status_code == 400

    def test_sync_ado_mocked(self, client, token_admin):
        """Sincronización exitosa con ADO mockeado."""
        c = client.post("/api/v1/proyectos/", json={
            "nombre": "Con ADO", "tipo": "Proyecto",
            "id_proyecto_excel": "ADO-MOCK-01",
            "ado_project_name": "MockProject",
        }, headers=auth(token_admin))
        pid = c.json()["id"]

        from app.schemas.proyecto import SyncAdoResponse
        mock_result = SyncAdoResponse(
            proyecto_id=pid, ado_project_name="MockProject",
            epicas=2, features=5, user_stories=10, tasks=20, total=37,
            mensaje="Sincronización completada: 37 ítems activos",
        )
        with patch("app.services.ado_service.sync_proyecto_ado", return_value=mock_result):
            res = client.post(f"/api/v1/proyectos/{pid}/sync-ado", headers=auth(token_admin))

        assert res.status_code == 200
        assert res.json()["total"] == 37
        assert res.json()["tasks"] == 20


@pytest.mark.integration
class TestItemsADO:
    @pytest.fixture(scope="class")
    def proyecto_con_items(self, client, token_admin, sqlite_session_factory):
        c = client.post("/api/v1/proyectos/", json={
            "nombre": "Proyecto Items", "tipo": "Proyecto",
            "id_proyecto_excel": "ITEMS-001",
        }, headers=auth(token_admin))
        pid = c.json()["id"]
        db = sqlite_session_factory()
        epica = AdoItem(ado_id=9001, tipo=TipoAdoItem.EPIC, titulo="Épica 1",
                        proyecto_id=pid, activo=True)
        db.add(epica)
        db.flush()
        task = AdoItem(ado_id=9002, tipo=TipoAdoItem.TASK, titulo="Task 1",
                       proyecto_id=pid, parent_id=epica.id, activo=True)
        db.add(task)
        db.commit()
        db.close()
        return pid

    def test_listar_items(self, client, token_admin, proyecto_con_items):
        res = client.get(f"/api/v1/proyectos/{proyecto_con_items}/items",
                         headers=auth(token_admin))
        assert res.status_code == 200
        assert len(res.json()) >= 2

    def test_filtrar_por_tipo(self, client, token_admin, proyecto_con_items):
        res = client.get(f"/api/v1/proyectos/{proyecto_con_items}/items?tipo=Task",
                         headers=auth(token_admin))
        assert res.status_code == 200
        assert all(i["tipo"] == "Task" for i in res.json())

    def test_arbol_retorna_epicas(self, client, token_admin, proyecto_con_items):
        res = client.get(f"/api/v1/proyectos/{proyecto_con_items}/items/arbol",
                         headers=auth(token_admin))
        assert res.status_code == 200
        assert all(e["tipo"] == "Epic" for e in res.json())
