"""
routers/sprints.py — CRUD de sprints.

Endpoints:
    GET    /api/v1/sprints/             → Listar (autenticado, filtro por proyecto)
    POST   /api/v1/sprints/             → Crear (admin_proyectos)
    GET    /api/v1/sprints/{id}         → Obtener por ID (autenticado)
    PUT    /api/v1/sprints/{id}         → Actualizar (admin_proyectos)
    POST   /api/v1/sprints/{id}/activar → Activar sprint (admin_proyectos)
    POST   /api/v1/sprints/{id}/cerrar  → Cerrar sprint (cerrar_sprint)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.sprint import Sprint, EstadoSprint
from app.models.proyecto import Proyecto
from app.schemas.sprint import SprintCreate, SprintUpdate, SprintResponse, SprintResumen
from app.api.v1.deps import get_current_user, require_permiso
from app.models.usuario import Usuario

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, sprint_id: int) -> Sprint:
    s = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Sprint {sprint_id} no encontrado")
    return s


def _validar_proyecto(db: Session, proyecto_id: int) -> Proyecto:
    p = db.query(Proyecto).filter(
        Proyecto.id == proyecto_id, Proyecto.activo == True
    ).first()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proyecto {proyecto_id} no existe o está inactivo",
        )
    return p


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[SprintResumen],
    summary="Listar sprints",
)
def listar_sprints(
    proyecto_id: int | None = Query(None, description="Filtrar por proyecto"),
    estado: EstadoSprint | None = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> list[Sprint]:
    """Lista sprints, opcionalmente filtrados por proyecto y/o estado."""
    q = db.query(Sprint)
    if proyecto_id is not None:
        q = q.filter(Sprint.proyecto_id == proyecto_id)
    if estado is not None:
        q = q.filter(Sprint.estado == estado)
    return q.order_by(Sprint.fecha_inicio.desc()).all()


@router.post(
    "/",
    response_model=SprintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear sprint",
    dependencies=[Depends(require_permiso("admin_proyectos"))],
)
def crear_sprint(
    payload: SprintCreate,
    db: Session = Depends(get_db),
) -> Sprint:
    """
    Crea un nuevo sprint para un proyecto.

    Raises:
        400: Si el proyecto no existe o está inactivo.
        400: Si ya existe un sprint activo para el mismo proyecto.
    """
    _validar_proyecto(db, payload.proyecto_id)

    sprint = Sprint(**payload.model_dump())
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.get(
    "/{sprint_id}",
    response_model=SprintResponse,
    summary="Obtener sprint por ID",
)
def obtener_sprint(
    sprint_id: int,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> Sprint:
    return _get_or_404(db, sprint_id)


@router.put(
    "/{sprint_id}",
    response_model=SprintResponse,
    summary="Actualizar sprint",
    dependencies=[Depends(require_permiso("admin_proyectos"))],
)
def actualizar_sprint(
    sprint_id: int,
    payload: SprintUpdate,
    db: Session = Depends(get_db),
) -> Sprint:
    """
    Actualiza los campos proporcionados del sprint.

    Raises:
        400: Si el sprint está cerrado (no se puede modificar).
    """
    sprint = _get_or_404(db, sprint_id)

    if sprint.estado == EstadoSprint.CERRADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar un sprint cerrado",
        )

    for campo, valor in payload.model_dump(exclude_none=True).items():
        setattr(sprint, campo, valor)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.post(
    "/{sprint_id}/activar",
    response_model=SprintResponse,
    summary="Activar sprint",
    dependencies=[Depends(require_permiso("admin_proyectos"))],
)
def activar_sprint(
    sprint_id: int,
    db: Session = Depends(get_db),
) -> Sprint:
    """
    Activa un sprint (Planificado → Activo).

    Solo puede haber un sprint activo por proyecto a la vez.

    Raises:
        400: Si el sprint no está en estado Planificado.
        400: Si el proyecto ya tiene otro sprint activo.
    """
    sprint = _get_or_404(db, sprint_id)

    if sprint.estado != EstadoSprint.PLANIFICADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se pueden activar sprints Planificados (estado actual: {sprint.estado})",
        )

    activo = db.query(Sprint).filter(
        Sprint.proyecto_id == sprint.proyecto_id,
        Sprint.estado == EstadoSprint.ACTIVO,
        Sprint.id != sprint_id,
    ).first()
    if activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un sprint activo: '{activo.nombre}'",
        )

    sprint.estado = EstadoSprint.ACTIVO
    db.commit()
    db.refresh(sprint)
    return sprint


@router.post(
    "/{sprint_id}/cerrar",
    response_model=SprintResponse,
    summary="Cerrar sprint",
    dependencies=[Depends(require_permiso("cerrar_sprint"))],
)
def cerrar_sprint(
    sprint_id: int,
    db: Session = Depends(get_db),
) -> Sprint:
    """
    Cierra un sprint (Activo → Cerrado).

    Un sprint cerrado no se puede reabrir ni modificar.

    Raises:
        400: Si el sprint no está activo.
    """
    sprint = _get_or_404(db, sprint_id)

    if sprint.estado != EstadoSprint.ACTIVO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se pueden cerrar sprints Activos (estado actual: {sprint.estado})",
        )

    sprint.estado = EstadoSprint.CERRADO
    db.commit()
    db.refresh(sprint)
    return sprint
