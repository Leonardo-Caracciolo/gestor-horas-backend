"""
tests/integration/test_auth.py — Tests de POST /auth/login y GET /auth/me.
Usa las fixtures del conftest.py de integración.
"""


def _login(client, username="admin", password="Admin123!") -> str:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return resp.json()["access_token"]


class TestLogin:
    def test_login_exitoso_devuelve_token(self, client):
        resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["token_type"] == "bearer"
        assert data["username"] == "admin"
        assert data["nombre"] == "Admin Sistema"
        assert data["rol"] == "Admin"
        assert "admin_usuarios" in data["permisos"]
        assert "ver_horas_equipo" in data["permisos"]
        assert data["primer_login"] is False

    def test_login_profesional_sin_permisos(self, client):
        resp = client.post("/api/v1/auth/login", json={"username": "juan.perez", "password": "Juan123!"})
        assert resp.status_code == 200
        assert resp.json()["permisos"] == []
        assert resp.json()["primer_login"] is True

    def test_login_password_incorrecta_retorna_401(self, client):
        resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "incorrecta"})
        assert resp.status_code == 401
        assert "Credenciales incorrectas" in resp.json()["detail"]

    def test_login_usuario_inexistente_retorna_401(self, client):
        resp = client.post("/api/v1/auth/login", json={"username": "fantasma", "password": "cualquiera"})
        assert resp.status_code == 401
        assert "Credenciales incorrectas" in resp.json()["detail"]  # mismo msg — no enumera usuarios

    def test_login_usuario_inactivo_retorna_403(self, client):
        resp = client.post("/api/v1/auth/login", json={"username": "inactivo", "password": "Inactivo123!"})
        assert resp.status_code == 403
        assert "desactivado" in resp.json()["detail"].lower()

    def test_login_username_case_insensitive(self, client):
        resp = client.post("/api/v1/auth/login", json={"username": "ADMIN", "password": "Admin123!"})
        assert resp.status_code == 200

    def test_login_token_funciona_en_me(self, client):
        token = _login(client)
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "admin"


class TestMe:
    def test_me_sin_token_retorna_401(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_token_invalido_retorna_401(self, client):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer esto.no.es.jwt"})
        assert resp.status_code == 401

    def test_me_retorna_datos_del_usuario(self, client, token_admin):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_admin}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["email"] == "admin@empresa.com"
        assert data["rol"]["nombre"] == "Admin"

    def test_me_profesional_retorna_sus_datos(self, client, token_prof):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_prof}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "juan.perez"
