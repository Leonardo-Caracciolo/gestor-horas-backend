"""
tests/integration/test_usuarios.py — Tests CRUD de usuarios.
Usa las fixtures del conftest.py de integración.
"""
from app.core.security import hash_password
from app.models.usuario import Usuario


def auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestListarUsuarios:
    def test_admin_puede_listar(self, client, token_admin):
        resp = client.get("/api/v1/usuarios/", headers=auth(token_admin))
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_profesional_sin_permiso_retorna_403(self, client, token_prof):
        resp = client.get("/api/v1/usuarios/", headers=auth(token_prof))
        assert resp.status_code == 403

    def test_sin_token_retorna_401(self, client):
        assert client.get("/api/v1/usuarios/").status_code == 401

    def test_solo_activos_no_incluye_inactivos(self, client, token_admin):
        resp = client.get("/api/v1/usuarios/", headers=auth(token_admin))
        usernames = [u["username"] for u in resp.json()]
        assert "inactivo" not in usernames

    def test_incluir_inactivos(self, client, token_admin):
        resp = client.get("/api/v1/usuarios/?solo_activos=false", headers=auth(token_admin))
        assert resp.status_code == 200
        inactivos = [u for u in resp.json() if not u["activo"]]
        assert len(inactivos) >= 1


class TestCrearUsuario:
    def test_admin_crea_usuario(self, client, token_admin,  rol_prof_id):
        resp = client.post("/api/v1/usuarios/", headers=auth(token_admin), json={
            "nombre": "Nuevo Usuario",
            "email": "nuevousr@empresa.com",
            "username": "nuevousr",
            "password": "Nuevo123!",
            "rol_id": rol_prof_id,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "nuevousr"
        assert data["primer_login"] is True
        assert "password_hash" not in data

    def test_email_duplicado_retorna_400(self, client, token_admin,  rol_prof_id):
        resp = client.post("/api/v1/usuarios/", headers=auth(token_admin), json={
            "nombre": "Dup",
            "email": "admin@empresa.com",  # ya existe
            "username": "dup_email",
            "password": "Dup12345!",
            "rol_id": rol_prof_id,
        })
        assert resp.status_code == 400
        assert "email" in resp.json()["detail"].lower()

    def test_username_duplicado_retorna_400(self, client, token_admin,  rol_prof_id):
        resp = client.post("/api/v1/usuarios/", headers=auth(token_admin), json={
            "nombre": "Dup",
            "email": "dup_user@empresa.com",
            "username": "admin",  # ya existe
            "password": "Dup12345!",
            "rol_id": rol_prof_id,
        })
        assert resp.status_code == 400
        assert "username" in resp.json()["detail"].lower()

    def test_password_corta_retorna_422(self, client, token_admin,  rol_prof_id):
        resp = client.post("/api/v1/usuarios/", headers=auth(token_admin), json={
            "nombre": "Corto",
            "email": "corto@empresa.com",
            "username": "corto",
            "password": "123",  # < 8 chars
            "rol_id": rol_prof_id,
        })
        assert resp.status_code == 422

    def test_rol_inexistente_retorna_400(self, client, token_admin):
        resp = client.post("/api/v1/usuarios/", headers=auth(token_admin), json={
            "nombre": "Sin Rol",
            "email": "sinrol@empresa.com",
            "username": "sinrol",
            "password": "SinRol123!",
            "rol_id": 9999,
        })
        assert resp.status_code == 400


class TestObtenerActualizarDesactivar:
    def _crear(self, client, token_admin, rol_id, suffix) -> dict:
        resp = client.post("/api/v1/usuarios/", headers=auth(token_admin), json={
            "nombre": f"Temp {suffix}",
            "email": f"{suffix}@empresa.com",
            "username": suffix,
            "password": "Temp1234!",
            "rol_id": rol_id,
        })
        assert resp.status_code == 201
        return resp.json()

    def test_obtener_id_inexistente_retorna_404(self, client, token_admin):
        assert client.get("/api/v1/usuarios/99999", headers=auth(token_admin)).status_code == 404

    def test_actualizar_nombre(self, client, token_admin,  rol_prof_id):
        u = self._crear(client, token_admin, rol_prof_id, "upd_nombre")
        resp = client.put(f"/api/v1/usuarios/{u['id']}", headers=auth(token_admin),
                          json={"nombre": "Nombre Actualizado"})
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Nombre Actualizado"

    def test_actualizar_solo_campos_enviados(self, client, token_admin,  rol_prof_id):
        """PUT es PATCH semántico: no toca campos no enviados."""
        u = self._crear(client, token_admin, rol_prof_id, "upd_patch")
        email_original = u["email"]
        resp = client.put(f"/api/v1/usuarios/{u['id']}", headers=auth(token_admin),
                          json={"nombre": "Solo Nombre"})
        assert resp.json()["email"] == email_original

    def test_desactivar_usuario(self, client, token_admin,  rol_prof_id):
        u = self._crear(client, token_admin, rol_prof_id, "del_user")
        resp = client.delete(f"/api/v1/usuarios/{u['id']}", headers=auth(token_admin))
        assert resp.status_code == 204
        # No aparece en lista de activos
        ids = [x["id"] for x in client.get("/api/v1/usuarios/", headers=auth(token_admin)).json()]
        assert u["id"] not in ids

    def test_no_puede_desactivarse_a_si_mismo(self, client, token_admin):
        me = client.get("/api/v1/auth/me", headers=auth(token_admin)).json()
        assert client.delete(f"/api/v1/usuarios/{me['id']}", headers=auth(token_admin)).status_code == 400


class TestCambiarPassword:
    def test_cambiar_password_correcta(self, client, sqlite_session_factory, rol_prof_id):
        # Crear usuario fresco directamente en BD
        db = sqlite_session_factory()
        u = Usuario(
            nombre="Cambio Pass", email="cambiopass@empresa.com", username="cambiopass",
            password_hash=hash_password("Original1!"),
            rol_id=rol_prof_id, primer_login=True,
        )
        db.add(u)
        db.commit()
        db.close()

        token = client.post("/api/v1/auth/login",
                            json={"username": "cambiopass", "password": "Original1!"}).json()["access_token"]
        resp = client.post("/api/v1/usuarios/me/password",
                           headers=auth(token),
                           json={"password_actual": "Original1!", "password_nuevo": "Nueva1234!"})
        assert resp.status_code == 204

        # Login con nueva password
        nuevo = client.post("/api/v1/auth/login",
                            json={"username": "cambiopass", "password": "Nueva1234!"})
        assert nuevo.status_code == 200
        assert nuevo.json()["primer_login"] is False

    def test_cambiar_password_actual_incorrecta_retorna_400(self, client, token_prof):
        resp = client.post("/api/v1/usuarios/me/password",
                           headers=auth(token_prof),
                           json={"password_actual": "INCORRECTA", "password_nuevo": "Nueva1234!"})
        assert resp.status_code == 400

    def test_cambiar_password_nueva_corta_retorna_422(self, client, token_prof):
        resp = client.post("/api/v1/usuarios/me/password",
                           headers=auth(token_prof),
                           json={"password_actual": "Juan123!", "password_nuevo": "123"})
        assert resp.status_code == 422
