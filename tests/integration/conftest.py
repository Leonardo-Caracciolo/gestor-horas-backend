"""
tests/integration/conftest.py — Fixtures compartidos para integración.

Un solo ENGINE SQLite StaticPool, scope=session en todo.
Siembra datos base (admin, profesional, inactivo) una sola vez.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa — registra todos los modelos en Base.metadata

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app as fastapi_app
from app.models.rol import Rol
from app.models.permiso import Permiso, RolPermiso
from app.models.usuario import Usuario

# ── Engine único para toda la sesión de pytest ─────────────────────────────
ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(ENGINE)
_SF = sessionmaker(bind=ENGINE, expire_on_commit=False, autoflush=False)


def _seed() -> None:
    """Siembra roles, permisos y usuarios base si aún no existen."""
    s = _SF()
    try:
        if s.query(Rol).filter_by(nombre="Admin").first():
            return

        p_admin   = Permiso(clave="admin_usuarios",   descripcion="ABM usuarios",     modulo="usuarios")
        p_horas   = Permiso(clave="ver_horas_equipo", descripcion="Ver horas equipo", modulo="horas")
        p_aprobar = Permiso(clave="aprobar_horas",    descripcion="Aprobar horas",    modulo="horas")
        p_proy    = Permiso(clave="admin_proyectos",  descripcion="ABM proyectos",    modulo="proyectos")
        p_fer     = Permiso(clave="admin_feriados",   descripcion="ABM feriados",     modulo="feriados")
        p_cerrar  = Permiso(clave="cerrar_sprint",    descripcion="Cerrar sprint",    modulo="sprints")
        p_export  = Permiso(clave="exportar_excel",   descripcion="Exportar Excel",   modulo="export")
        s.add_all([p_admin, p_horas, p_aprobar, p_proy, p_fer, p_cerrar, p_export])
        s.flush()

        r_admin = Rol(nombre="Admin",       descripcion="Administrador", es_sistema=True)
        r_prof  = Rol(nombre="Profesional", descripcion="Integrante")
        s.add_all([r_admin, r_prof])
        s.flush()

        for p in [p_admin, p_horas, p_aprobar, p_proy, p_fer, p_cerrar, p_export]:
            s.add(RolPermiso(rol_id=r_admin.id, permiso_id=p.id))

        s.add_all([
            Usuario(nombre="Admin Sistema", email="admin@empresa.com",
                    username="admin", password_hash=hash_password("Admin123!"),
                    rol_id=r_admin.id, primer_login=False),
            Usuario(nombre="Juan Perez", email="juan.perez@empresa.com",
                    username="juan.perez", password_hash=hash_password("Juan123!"),
                    rol_id=r_prof.id),
            Usuario(nombre="Inactivo", email="inactivo@empresa.com",
                    username="inactivo", password_hash=hash_password("Inactivo123!"),
                    rol_id=r_prof.id, activo=False),
        ])
        s.commit()
    finally:
        s.close()


_seed()


# ── Fixtures session-scoped ────────────────────────────────────────────────

@pytest.fixture(scope="session")
def sqlite_session_factory():
    """Sessionmaker vinculado al ENGINE SQLite compartido."""
    return _SF


@pytest.fixture(scope="session")
def client():
    """TestClient con override de get_db. Scope=session."""
    def override_get_db():
        db = _SF()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app, raise_server_exceptions=True) as c:
        yield c
    fastapi_app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="session")
def token_admin(client):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"})
    assert resp.status_code == 200, f"Login admin falló: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def token_prof(client):
    resp = client.post("/api/v1/auth/login", json={"username": "juan.perez", "password": "Juan123!"})
    assert resp.status_code == 200, f"Login prof falló: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def rol_prof_id():
    s = _SF()
    r = s.query(Rol).filter_by(nombre="Profesional").first()
    rid = r.id
    s.close()
    return rid
