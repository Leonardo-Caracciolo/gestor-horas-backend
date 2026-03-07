"""
routers/feriados.py — ABM de feriados nacionales.

Endpoints:
    GET    /api/v1/feriados/        → Listar feriados (autenticado, filtro por año)
    POST   /api/v1/feriados/        → Crear feriado (admin_feriados)
    PUT    /api/v1/feriados/{id}    → Actualizar feriado (admin_feriados)
    DELETE /api/v1/feriados/{id}    → Eliminar feriado (admin_feriados)
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.feriado import Feriado
from app.schemas.feriado import FeriadoCreate, FeriadoUpdate, FeriadoResponse
from app.api.v1.deps import get_current_user, require_permiso
from app.models.usuario import Usuario

router = APIRouter()


def _get_or_404(db: Session, feriado_id: int) -> Feriado:
    f = db.query(Feriado).filter(Feriado.id == feriado_id).first()
    if not f:
        raise HTTPException(status_code=404, detail=f"Feriado {feriado_id} no encontrado")
    return f


@router.get(
    "/",
    response_model=list[FeriadoResponse],
    summary="Listar feriados",
)
def listar_feriados(
    anio: int | None = Query(None, description="Filtrar por año"),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(get_current_user),
) -> list[Feriado]:
    """Lista feriados, opcionalmente filtrados por año."""
    q = db.query(Feriado)
    if anio:
        q = q.filter(Feriado.anio == anio)
    return q.order_by(Feriado.fecha).all()


@router.post(
    "/",
    response_model=FeriadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear feriado",
    dependencies=[Depends(require_permiso("admin_feriados"))],
)
def crear_feriado(
    payload: FeriadoCreate,
    db: Session = Depends(get_db),
) -> Feriado:
    """
    Crea un feriado.

    Raises:
        400: Si ya existe un feriado para esa fecha.
    """
    if db.query(Feriado).filter(Feriado.fecha == payload.fecha).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un feriado para el {payload.fecha}",
        )
    feriado = Feriado(
        fecha=payload.fecha,
        nombre=payload.nombre,
        aplica_a_todos=payload.aplica_a_todos,
        anio=payload.fecha.year,
    )
    db.add(feriado)
    db.commit()
    db.refresh(feriado)
    return feriado


@router.put(
    "/{feriado_id}",
    response_model=FeriadoResponse,
    summary="Actualizar feriado",
    dependencies=[Depends(require_permiso("admin_feriados"))],
)
def actualizar_feriado(
    feriado_id: int,
    payload: FeriadoUpdate,
    db: Session = Depends(get_db),
) -> Feriado:
    feriado = _get_or_404(db, feriado_id)
    for campo, valor in payload.model_dump(exclude_none=True).items():
        setattr(feriado, campo, valor)
    db.commit()
    db.refresh(feriado)
    return feriado


@router.delete(
    "/{feriado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar feriado",
    dependencies=[Depends(require_permiso("admin_feriados"))],
)
def eliminar_feriado(feriado_id: int, db: Session = Depends(get_db)) -> None:
    feriado = _get_or_404(db, feriado_id)
    db.delete(feriado)
    db.commit()
