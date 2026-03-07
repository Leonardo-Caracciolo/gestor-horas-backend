"""
conftest.py — Fixtures compartidas entre todos los tests.

Siguiendo el estándar del equipo (docs_qa_guide):
- pytest descubre automáticamente este archivo.
- No necesitan ser importadas en los tests.
- scope="session" para fixtures costosas (BD, mocks globales).
- scope="function" para fixtures que deben resetearse entre tests.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from faker import Faker

from app.core.database import Base
from app.models.rol import Rol
from app.models.permiso import Permiso, RolPermiso
from app.models.usuario import Usuario
from app.models.proyecto import Proyecto, TipoProyecto
from app.models.sprint import Sprint, EstadoSprint
from app.models.ado_item import AdoItem, TipoAdoItem
from app.models.registro_hora import RegistroHora, EstadoRegistro
from app.models.feriado import Feriado
from app.models.semana import Semana, EstadoSemana
from app.core.security import hash_password

fake = Faker("es_MX")


# ─────────────────────────────────────────────────────────────────
# BASE DE DATOS EN MEMORIA (SQLite) para tests
# Se usa SQLite en lugar de SQL Server para tests unitarios e integración.
# Los tests de e2e usan la BD real de homologación.
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def engine_test():
    """
    Crea un engine SQLite en memoria para la sesión de tests completa.

    Scope session: se crea una sola vez por ejecución de pytest.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(engine_test) -> Session:
    """
    Provee una sesión de BD aislada para cada test.

    Usa transacciones con rollback para garantizar que cada test
    empiece con una BD limpia sin necesidad de truncar tablas.

    Yields:
        Session: Sesión de SQLAlchemy con rollback al finalizar.
    """
    connection = engine_test.connect()
    transaction = connection.begin()
    SessionTest = sessionmaker(bind=connection)
    session = SessionTest()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ─────────────────────────────────────────────────────────────────
# FIXTURES DE ROLES Y PERMISOS
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def permiso_ver_horas_equipo(db: Session) -> Permiso:
    permiso = Permiso(
        clave="ver_horas_equipo",
        descripcion="Ver horas de todos los integrantes",
        modulo="horas",
    )
    db.add(permiso)
    db.flush()
    return permiso


@pytest.fixture
def permiso_exportar_excel(db: Session) -> Permiso:
    permiso = Permiso(
        clave="exportar_excel",
        descripcion="Generar y descargar el Excel oficial",
        modulo="export",
    )
    db.add(permiso)
    db.flush()
    return permiso


@pytest.fixture
def rol_admin(db: Session) -> Rol:
    """Rol de administrador del sistema (protegido)."""
    rol = Rol(nombre="Admin", descripcion="Administrador del sistema", es_sistema=True)
    db.add(rol)
    db.flush()
    return rol


@pytest.fixture
def rol_tech_lead(db: Session, permiso_ver_horas_equipo, permiso_exportar_excel) -> Rol:
    """Rol Tech Lead con permisos de ver horas del equipo y exportar."""
    rol = Rol(nombre="Tech Lead", descripcion="Líder técnico del equipo")
    db.add(rol)
    db.flush()
    db.add(RolPermiso(rol_id=rol.id, permiso_id=permiso_ver_horas_equipo.id))
    db.add(RolPermiso(rol_id=rol.id, permiso_id=permiso_exportar_excel.id))
    db.flush()
    return rol


@pytest.fixture
def rol_profesional(db: Session) -> Rol:
    """Rol profesional: solo ve y carga sus propias horas."""
    rol = Rol(nombre="Profesional", descripcion="Integrante del equipo")
    db.add(rol)
    db.flush()
    return rol


# ─────────────────────────────────────────────────────────────────
# FIXTURES DE USUARIOS
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def usuario_tech_lead(db: Session, rol_tech_lead: Rol) -> Usuario:
    """Usuario Tech Lead con permisos de gestión del equipo."""
    usuario = Usuario(
        nombre="Carlos Rodríguez",
        email="carlos.rodriguez@empresa.com",
        username="carlos.rodriguez",
        password_hash=hash_password("Password123!"),
        rol_id=rol_tech_lead.id,
    )
    db.add(usuario)
    db.flush()
    return usuario


@pytest.fixture
def usuario_profesional(db: Session, rol_profesional: Rol) -> Usuario:
    """Usuario profesional estándar del equipo."""
    usuario = Usuario(
        nombre="Ana García",
        email="ana.garcia@empresa.com",
        username="ana.garcia",
        password_hash=hash_password("Password123!"),
        rol_id=rol_profesional.id,
    )
    db.add(usuario)
    db.flush()
    return usuario


@pytest.fixture
def usuario_inactivo(db: Session, rol_profesional: Rol) -> Usuario:
    """Usuario desactivado — no debe poder iniciar sesión."""
    usuario = Usuario(
        nombre="Pedro Inactivo",
        email="pedro.inactivo@empresa.com",
        username="pedro.inactivo",
        password_hash=hash_password("Password123!"),
        rol_id=rol_profesional.id,
        activo=False,
    )
    db.add(usuario)
    db.flush()
    return usuario


# ─────────────────────────────────────────────────────────────────
# FIXTURES DE PROYECTOS
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def proyecto_activo(db: Session) -> Proyecto:
    """Proyecto de tipo Proyecto activo con ADO configurado."""
    proyecto = Proyecto(
        nombre="Proyecto Alpha",
        tipo=TipoProyecto.PROYECTO,
        id_proyecto_excel="PRJ-001",
        ado_project_name="alpha-devops",
    )
    db.add(proyecto)
    db.flush()
    return proyecto


@pytest.fixture
def proyecto_oficina(db: Session) -> Proyecto:
    """Proyecto de tipo Oficina para tareas administrativas."""
    proyecto = Proyecto(
        nombre="Oficina General",
        tipo=TipoProyecto.OFICINA,
        id_proyecto_excel="OFC-001",
    )
    db.add(proyecto)
    db.flush()
    return proyecto


# ─────────────────────────────────────────────────────────────────
# FIXTURES DE SPRINTS Y ADO ITEMS
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sprint_activo(db: Session, proyecto_activo: Proyecto) -> Sprint:
    """Sprint activo de 2 semanas."""
    sprint = Sprint(
        nombre="Sprint 23",
        fecha_inicio=date(2025, 1, 6),
        fecha_fin=date(2025, 1, 17),
        estado=EstadoSprint.ACTIVO,
        proyecto_id=proyecto_activo.id,
        ado_sprint_id="alpha-devops\\Sprint 23",
    )
    db.add(sprint)
    db.flush()
    return sprint


@pytest.fixture
def ado_task_valida(db: Session, proyecto_activo: Proyecto, sprint_activo: Sprint) -> AdoItem:
    """Task de ADO válida asignada al sprint activo."""
    task = AdoItem(
        ado_id=1001,
        tipo=TipoAdoItem.TASK,
        titulo="Implementar endpoint de carga de horas",
        asignado_a="ana.garcia@empresa.com",
        estado="Active",
        proyecto_id=proyecto_activo.id,
        sprint_id=sprint_activo.id,
    )
    db.add(task)
    db.flush()
    return task


# ─────────────────────────────────────────────────────────────────
# FIXTURES DE REGISTROS DE HORAS
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def registro_hora_valido(
    db: Session,
    usuario_profesional: Usuario,
    proyecto_activo: Proyecto,
    ado_task_valida: AdoItem,
) -> RegistroHora:
    """Registro de horas válido en estado Borrador."""
    registro = RegistroHora(
        usuario_id=usuario_profesional.id,
        fecha=date(2025, 1, 6),
        proyecto_id=proyecto_activo.id,
        ado_task_id=ado_task_valida.id,
        descripcion="Implementación del endpoint POST /horas",
        horas=Decimal("4.00"),
        estado=EstadoRegistro.BORRADOR,
    )
    db.add(registro)
    db.flush()
    return registro


@pytest.fixture
def registro_hora_aprobado(
    db: Session,
    usuario_profesional: Usuario,
    proyecto_activo: Proyecto,
) -> RegistroHora:
    """Registro de horas ya aprobado."""
    registro = RegistroHora(
        usuario_id=usuario_profesional.id,
        fecha=date(2025, 1, 7),
        proyecto_id=proyecto_activo.id,
        descripcion="Code review y documentación",
        tarea_manual="Code Review",
        horas=Decimal("2.50"),
        estado=EstadoRegistro.APROBADO,
    )
    db.add(registro)
    db.flush()
    return registro


# ─────────────────────────────────────────────────────────────────
# FIXTURES DE FERIADOS
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def feriado_mexico(db: Session) -> Feriado:
    """Feriado nacional de México."""
    feriado = Feriado(
        fecha=date(2025, 2, 3),
        nombre="Día de la Constitución",
        aplica_a_todos=True,
        anio=2025,
    )
    db.add(feriado)
    db.flush()
    return feriado


# ─────────────────────────────────────────────────────────────────
# MOCKS DE SERVICIOS EXTERNOS
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def ado_client_mock():
    """
    Mock del cliente de Azure DevOps.

    Simula la respuesta de la API de ADO sin conexión real.
    Se usa en todos los tests que involucran sincronización con ADO.
    """
    mock = MagicMock()
    mock.get_work_items.return_value = [
        {
            "id": 1001,
            "fields": {
                "System.WorkItemType": "Task",
                "System.Title": "Implementar endpoint de carga de horas",
                "System.AssignedTo": {"uniqueName": "ana.garcia@empresa.com"},
                "System.State": "Active",
                "System.IterationPath": "alpha-devops\\Sprint 23",
            }
        }
    ]
    mock.get_sprints.return_value = [
        {
            "id": "sprint-23-guid",
            "name": "Sprint 23",
            "attributes": {
                "startDate": "2025-01-06T00:00:00Z",
                "finishDate": "2025-01-17T00:00:00Z",
            }
        }
    ]
    return mock


@pytest.fixture(scope="session")
def teams_webhook_mock():
    """
    Mock del cliente HTTP para Teams Webhooks.

    Evita enviar notificaciones reales durante los tests.
    """
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        yield mock_post
