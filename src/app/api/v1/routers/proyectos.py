"""
routers/proyectos.py — CRUD de proyectos + sincronización con ADO.

Endpoints:
    GET    /api/v1/proyectos/           → Listar proyectos (autenticado)
    POST   /api/v1/proyectos/           → Crear proyecto (admin_proyectos)
    GET    /api/v1/proyectos/{id}       → Obtener por ID (autenticado)
    PUT    /api/v1/proyectos/{id}       → Actualizar (admin_proyectos)
    DELETE /api/v1/proyectos/{id}       → Desactivar (admin_proyectos)
    POST   /api/v1/proyectos/{id}/sync-ado  → Sincronizar con ADO (admin_proyectos)
    GET    /api/v1/proyectos/{id}/items → Ítems ADO del proyecto (autenticado)
    GET    /api/v1/proyectos/{id}/items/arbol → Jerarquía anidada (autenticado)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.proyecto import Proyecto
from app.models.ado_item import AdoItem, TipoAdoItem
from app.schemas.proyecto import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse, ProyectoResumen, SyncAdoResponse
)
from app.schemas.ado_item import AdoItemResponse, AdoItemArbol
from app.api.v1.deps import get_current_user, require_permiso
from app.models.usuario import Usuario

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, proyecto_id: int) -> Proyecto:
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Proyecto {proyecto_id} no encontrado")
    return p


# ── CRUD ───────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[ProyectoResumen],
    summary="Listar proyectos",
)
def listar_proyectos(
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> list[Proyecto]:
    """Lista todos los proyectos. Por defecto solo los activos."""
    q = db.query(Proyecto)
    if solo_activos:
        q = q.filter(Proyecto.activo == True)
    return q.order_by(Proyecto.nombre).all()


@router.post(
    "/",
    response_model=ProyectoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto",
    dependencies=[Depends(require_permiso("admin_proyectos"))],
)
def crear_proyecto(
    payload: ProyectoCreate,
    db: Session = Depends(get_db),
) -> Proyecto:
    """
    Crea un nuevo proyecto.

    Raises:
        400: Si el id_proyecto_excel ya está en uso.
    """
    if db.query(Proyecto).filter(
        Proyecto.id_proyecto_excel == payload.id_proyecto_excel
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El código '{payload.id_proyecto_excel}' ya existe",
        )
    proyecto = Proyecto(**payload.model_dump())
    db.add(proyecto)
    db.commit()
    db.refresh(proyecto)
    return proyecto


@router.get(
    "/{proyecto_id}",
    response_model=ProyectoResponse,
    summary="Obtener proyecto por ID",
)
def obtener_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> Proyecto:
    return _get_or_404(db, proyecto_id)


@router.put(
    "/{proyecto_id}",
    response_model=ProyectoResponse,
    summary="Actualizar proyecto",
    dependencies=[Depends(require_permiso("admin_proyectos"))],
)
def actualizar_proyecto(
    proyecto_id: int,
    payload: ProyectoUpdate,
    db: Session = Depends(get_db),
) -> Proyecto:
    """Actualiza los campos proporcionados (PATCH semántico)."""
    proyecto = _get_or_404(db, proyecto_id)
    for campo, valor in payload.model_dump(exclude_none=True).items():
        setattr(proyecto, campo, valor)
    db.commit()
    db.refresh(proyecto)
    return proyecto


@router.delete(
    "/{proyecto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar proyecto",
    dependencies=[Depends(require_permiso("admin_proyectos"))],
)
def desactivar_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Desactiva un proyecto (soft delete)."""
    proyecto = _get_or_404(db, proyecto_id)
    proyecto.activo = False
    db.commit()


# ── Sincronización ADO ─────────────────────────────────────────────────────

@router.post(
    "/{proyecto_id}/sync-ado",
    response_model=SyncAdoResponse,
    summary="Sincronizar con Azure DevOps",
    dependencies=[Depends(require_permiso("admin_proyectos"))],
)
def sync_ado(
    proyecto_id: int,
    db: Session = Depends(get_db),
) -> SyncAdoResponse:
    """
    Dispara la sincronización de Work Items desde Azure DevOps.

    Requiere que el proyecto tenga `ado_project_name` configurado y
    que las variables ADO_ORGANIZATION_URL, ADO_PAT estén en .env.

    Raises:
        400: Si el proyecto no tiene ado_project_name.
        503: Si la conexión a ADO falla.
    """
    from app.services.ado_service import sync_proyecto_ado

    proyecto = _get_or_404(db, proyecto_id)
    if not proyecto.ado_project_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El proyecto no tiene ado_project_name configurado",
        )
    try:
        return sync_proyecto_ado(db, proyecto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error conectando a Azure DevOps: {e}",
        )


# ── Consulta de ítems ADO ──────────────────────────────────────────────────

@router.get(
    "/{proyecto_id}/items",
    response_model=list[AdoItemResponse],
    summary="Listar Work Items del proyecto",
)
def listar_items(
    proyecto_id: int,
    tipo: TipoAdoItem | None = Query(None, description="Filtrar por tipo"),
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> list[AdoItem]:
    """
    Retorna los Work Items sincronizados del proyecto.

    Args:
        tipo: Opcional. Filtra por Epic, Feature, User Story o Task.
        solo_activos: Si True (default), omite los marcados como inactivos.
    """
    _get_or_404(db, proyecto_id)
    q = db.query(AdoItem).filter(AdoItem.proyecto_id == proyecto_id)
    if tipo:
        q = q.filter(AdoItem.tipo == tipo)
    if solo_activos:
        q = q.filter(AdoItem.activo == True)
    return q.order_by(AdoItem.tipo, AdoItem.ado_id).all()


@router.get(
    "/{proyecto_id}/items/arbol",
    response_model=list[AdoItemArbol],
    summary="Jerarquía de Work Items (sólo Epics con hijos anidados)",
)
def items_arbol(
    proyecto_id: int,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> list[AdoItem]:
    """
    Retorna las Épicas del proyecto con Features → USs → Tasks anidados.
    Útil para el selector de tareas en la pantalla de carga de horas.
    """
    _get_or_404(db, proyecto_id)
    epicas = (
        db.query(AdoItem)
        .filter(
            AdoItem.proyecto_id == proyecto_id,
            AdoItem.tipo == TipoAdoItem.EPIC,
            AdoItem.activo == True,
        )
        .order_by(AdoItem.ado_id)
        .all()
    )
    return epicas
