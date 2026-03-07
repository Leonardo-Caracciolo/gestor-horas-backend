"""
tests/integration/test_horas.py — Tests de integración para carga de horas.
Usa los usuarios/roles/permisos sembrados en conftest (admin / juan.perez).
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.models.proyecto import Proyecto, TipoProyecto
from app.models.feriado import Feriado


# ── Fixtures ───────────────────────────────────────────────────────────────

LUNES = date.today() - timedelta(days=date.today().weekday())
MARTES = LUNES + timedelta(days=1)
MIERCOLES = LUNES + timedelta(days=2)
JUEVES = LUNES + timedelta(days=3)
VIERNES = LUNES + timedelta(days=4)


@pytest.fixture(scope="module")
def proyecto_test(client, sqlite_session_factory):
    db = sqlite_session_factory()
    p = Proyecto(nombre="Proyecto Horas Test", tipo=TipoProyecto.PROYECTO,
                 id_proyecto_excel="HORA-TEST-01")
    db.add(p)
    db.commit()
    pid = p.id
    db.close()
    return pid


def auth(token): return {"Authorization": f"Bearer {token}"}


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestCrearRegistro:
    def test_crear_registro_valido(self, client, token_prof, proyecto_test):
        res = client.post("/api/v1/horas/", json={
            "fecha": str(LUNES),
            "proyecto_id": proyecto_test,
            "descripcion": "Trabajo en feature X",
            "horas": "2.00",
            "tarea_manual": "Feature X",
        }, headers=auth(token_prof))
        assert res.status_code == 201
        assert res.json()["estado"] == "Borrador"
        assert Decimal(res.json()["horas"]) == Decimal("2.00")

    def test_crear_en_feriado_retorna_400(self, client, token_prof, proyecto_test, sqlite_session_factory):
        # Usa un lunes lejano para evitar colisión con otros tests
        feriado_fecha = LUNES + timedelta(weeks=4)
        db = sqlite_session_factory()
        if not db.query(Feriado).filter_by(fecha=feriado_fecha).first():
            db.add(Feriado(fecha=feriado_fecha, nombre="Feriado Test Horas",
                           aplica_a_todos=True, anio=feriado_fecha.year))
            db.commit()
        db.close()

        res = client.post("/api/v1/horas/", json={
            "fecha": str(feriado_fecha),
            "proyecto_id": proyecto_test,
            "descripcion": "Test feriado",
            "horas": "1.00",
            "tarea_manual": "Task X",
        }, headers=auth(token_prof))
        assert res.status_code == 400
        assert "feriado" in res.json()["detail"].lower()

    def test_crear_en_fin_de_semana_retorna_400(self, client, token_prof, proyecto_test):
        sabado = LUNES + timedelta(days=5)
        res = client.post("/api/v1/horas/", json={
            "fecha": str(sabado),
            "proyecto_id": proyecto_test,
            "descripcion": "Test sabado",
            "horas": "1.00",
            "tarea_manual": "Task X",
        }, headers=auth(token_prof))
        assert res.status_code == 400
        assert "fin de semana" in res.json()["detail"].lower()

    def test_crear_sin_tarea_ni_ceremonia_retorna_422(self, client, token_prof, proyecto_test):
        res = client.post("/api/v1/horas/", json={
            "fecha": str(MARTES),
            "proyecto_id": proyecto_test,
            "descripcion": "Sin tarea",
            "horas": "1.00",
        }, headers=auth(token_prof))
        assert res.status_code == 422


@pytest.mark.integration
class TestEditarEliminarRegistro:
    def _crear(self, client, token, pid, horas="1.00", desc="Registro test", dia=None):
        d = dia or MARTES
        res = client.post("/api/v1/horas/", json={
            "fecha": str(d),
            "proyecto_id": pid,
            "descripcion": desc,
            "horas": horas,
            "tarea_manual": "Task test",
        }, headers=auth(token))
        assert res.status_code == 201, res.json()
        return res.json()["id"]

    def test_editar_borrador(self, client, token_prof, proyecto_test):
        rid = self._crear(client, token_prof, proyecto_test, dia=JUEVES)
        res = client.put(f"/api/v1/horas/{rid}",
                         json={"descripcion": "Descripción actualizada"},
                         headers=auth(token_prof))
        assert res.status_code == 200
        assert res.json()["descripcion"] == "Descripción actualizada"

    def test_eliminar_borrador(self, client, token_prof, proyecto_test):
        rid = self._crear(client, token_prof, proyecto_test,
                          desc="Para eliminar", dia=VIERNES, horas="0.50")
        res = client.delete(f"/api/v1/horas/{rid}", headers=auth(token_prof))
        assert res.status_code == 204

    def test_no_puede_editar_ajeno(self, client, token_admin, token_prof, proyecto_test):
        # admin crea un registro
        rid = self._crear(client, token_admin, proyecto_test, dia=LUNES + timedelta(weeks=1))
        # prof intenta editarlo → 403
        res = client.put(f"/api/v1/horas/{rid}", json={"descripcion": "Hack"},
                         headers=auth(token_prof))
        assert res.status_code == 403


@pytest.mark.integration
class TestFlujoAprobacion:
    def _crear_y_enviar(self, client, token_prof, proyecto_test, dia):
        res = client.post("/api/v1/horas/", json={
            "fecha": str(dia),
            "proyecto_id": proyecto_test,
            "descripcion": "Para aprobar",
            "horas": "1.00",
            "tarea_manual": "Task aprobación",
        }, headers=auth(token_prof))
        assert res.status_code == 201, res.json()
        rid = res.json()["id"]
        semana = dia - timedelta(days=dia.weekday())
        client.post("/api/v1/horas/enviar", json={
            "fecha_inicio": str(semana),
            "fecha_fin": str(semana + timedelta(days=4)),
        }, headers=auth(token_prof))
        return rid

    def test_aprobar_registro(self, client, token_prof, token_admin, proyecto_test):
        rid = self._crear_y_enviar(client, token_prof, proyecto_test,
                                   dia=LUNES + timedelta(weeks=2))
        res = client.post(f"/api/v1/horas/{rid}/aprobar",
                          json={"aprobar": True}, headers=auth(token_admin))
        assert res.status_code == 200
        assert res.json()["estado"] == "Aprobado"

    def test_rechazar_requiere_comentario(self, client, token_admin):
        # Validación Pydantic: aprobar=False sin comentario → 422
        res = client.post("/api/v1/horas/99999/aprobar",
                          json={"aprobar": False}, headers=auth(token_admin))
        assert res.status_code == 422

    def test_no_puede_editar_enviado(self, client, token_prof, proyecto_test):
        rid = self._crear_y_enviar(client, token_prof, proyecto_test,
                                   dia=LUNES + timedelta(weeks=3))
        res = client.put(f"/api/v1/horas/{rid}", json={"descripcion": "Cambio"},
                         headers=auth(token_prof))
        assert res.status_code == 400
        assert "Borrador" in res.json()["detail"]


@pytest.mark.integration
class TestTimer:
    def test_ciclo_completo_timer(self, client, token_prof, proyecto_test):
        semana_timer = LUNES + timedelta(weeks=5)
        res = client.post("/api/v1/horas/timer/iniciar", json={
            "fecha": str(semana_timer),
            "proyecto_id": proyecto_test,
            "descripcion": "Timer test",
            "tarea_manual": "Task timer",
        }, headers=auth(token_prof))
        assert res.status_code == 201
        rid = res.json()["registro_id"]

        res = client.post(f"/api/v1/horas/{rid}/timer/detener", headers=auth(token_prof))
        assert res.status_code == 200
        assert Decimal(res.json()["horas"]) >= Decimal("0.25")

    def test_no_puede_haber_dos_timers(self, client, token_prof, proyecto_test):
        semana_timer2 = LUNES + timedelta(weeks=6)
        res1 = client.post("/api/v1/horas/timer/iniciar", json={
            "fecha": str(semana_timer2),
            "proyecto_id": proyecto_test,
            "descripcion": "Timer 1",
            "tarea_manual": "Task A",
        }, headers=auth(token_prof))
        assert res1.status_code == 201

        res2 = client.post("/api/v1/horas/timer/iniciar", json={
            "fecha": str(semana_timer2),
            "proyecto_id": proyecto_test,
            "descripcion": "Timer 2",
            "tarea_manual": "Task B",
        }, headers=auth(token_prof))
        assert res2.status_code == 400
        assert "timer activo" in res2.json()["detail"].lower()

        # Limpiar
        client.post(f"/api/v1/horas/{res1.json()['registro_id']}/timer/detener",
                    headers=auth(token_prof))


@pytest.mark.integration
class TestResumenSemana:
    def test_semana_retorna_5_dias(self, client, token_prof):
        res = client.get(f"/api/v1/horas/semana?fecha_ref={LUNES}", headers=auth(token_prof))
        assert res.status_code == 200
        assert len(res.json()) == 5

    def test_semana_incluye_registros_del_dia(self, client, token_prof):
        res = client.get(f"/api/v1/horas/semana?fecha_ref={LUNES}", headers=auth(token_prof))
        lunes_data = next(d for d in res.json() if d["fecha"] == str(LUNES))
        assert lunes_data["total_horas"] is not None
