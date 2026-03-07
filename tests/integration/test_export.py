"""
tests/integration/test_export.py — Tests de export Excel y semanas.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch
from app.models.proyecto import Proyecto, TipoProyecto
from app.models.registro_hora import RegistroHora, EstadoRegistro
from app.models.semana import Semana, EstadoSemana


def auth(t): return {"Authorization": f"Bearer {t}"}


LUNES_EXP = date(2025, 3, 10)   # Semana fija para tests de export


@pytest.fixture(scope="module")
def setup_export(client, token_admin, sqlite_session_factory):
    db = sqlite_session_factory()
    p = Proyecto(nombre="Proyecto Export", tipo=TipoProyecto.PROYECTO,
                 id_proyecto_excel="EXP-001")
    db.add(p)
    db.flush()

    semana = Semana(fecha_inicio=LUNES_EXP,
                    fecha_fin=LUNES_EXP + timedelta(days=4))
    db.add(semana)
    db.flush()

    # Un registro aprobado para que el Excel tenga datos
    from app.models.usuario import Usuario
    usuario = db.query(Usuario).filter_by(username="juan.perez").first()
    reg = RegistroHora(
        usuario_id=usuario.id, fecha=LUNES_EXP,
        proyecto_id=p.id, descripcion="Trabajo export test",
        tarea_manual="Task Export", horas="4.00",
        estado=EstadoRegistro.APROBADO,
    )
    db.add(reg)
    db.commit()
    ids = {"semana_id": semana.id, "proyecto_id": p.id}
    db.close()
    return ids


@pytest.mark.integration
class TestSemanas:
    def test_crear_semana(self, client, token_admin):
        lunes = date(2025, 4, 7)
        res = client.post("/api/v1/export/semanas/", json={
            "fecha_inicio": str(lunes),
            "fecha_fin": str(lunes + timedelta(days=4)),
        }, headers=auth(token_admin))
        assert res.status_code == 201
        assert res.json()["estado"] == "Abierta"

    def test_listar_semanas(self, client, token_admin, setup_export):
        res = client.get("/api/v1/export/semanas/?anio=2025", headers=auth(token_admin))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_cerrar_semana(self, client, token_admin, setup_export):
        sid = setup_export["semana_id"]
        with patch("app.api.v1.routers.export.notificar_semana_cerrada"):
            res = client.post(f"/api/v1/export/semanas/{sid}/cerrar?notificar=false",
                              headers=auth(token_admin))
        assert res.status_code == 200
        assert res.json()["estado"] == "Cerrada"

    def test_cerrar_semana_ya_cerrada_retorna_400(self, client, token_admin, setup_export):
        sid = setup_export["semana_id"]
        res = client.post(f"/api/v1/export/semanas/{sid}/cerrar?notificar=false",
                          headers=auth(token_admin))
        assert res.status_code == 400
        assert "cerrada" in res.json()["detail"].lower()


@pytest.mark.integration
class TestExcelDownload:
    def test_descargar_excel_retorna_xlsx(self, client, token_admin, setup_export):
        sid = setup_export["semana_id"]
        res = client.get(f"/api/v1/export/semanas/{sid}/excel", headers=auth(token_admin))
        assert res.status_code == 200
        assert "spreadsheetml" in res.headers["content-type"]
        assert res.content[:4] == b"PK\x03\x04"  # magic bytes de ZIP/XLSX

    def test_excel_preview_incluye_enviados(self, client, token_admin, setup_export):
        sid = setup_export["semana_id"]
        res = client.get(f"/api/v1/export/semanas/{sid}/excel?solo_aprobados=false",
                         headers=auth(token_admin))
        assert res.status_code == 200

    def test_sin_permiso_retorna_403(self, client, token_prof, setup_export):
        sid = setup_export["semana_id"]
        res = client.get(f"/api/v1/export/semanas/{sid}/excel", headers=auth(token_prof))
        assert res.status_code == 403


@pytest.mark.integration
class TestTeams:
    def test_teams_test_sin_webhook(self, client, token_admin):
        """Sin TEAMS_WEBHOOK_URL configurado, retorna enviado=False sin error."""
        res = client.post("/api/v1/export/teams/test", headers=auth(token_admin))
        assert res.status_code == 200
        assert res.json()["enviado"] is False

    def test_teams_test_con_webhook_mockeado(self, client, token_admin):
        with patch("app.services.export_service.notificar_teams", return_value=True):
            res = client.post("/api/v1/export/teams/test", headers=auth(token_admin))
        assert res.status_code == 200
