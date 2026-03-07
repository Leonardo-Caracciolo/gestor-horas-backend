"""
routers/ceremonias.py — CRUD de ceremonias Scrum dentro de un sprint.

Endpoints:
    GET    /api/v1/sprints/{sprint_id}/ceremonias/      → Listar ceremonias
    POST   /api/v1/sprints/{sprint_id}/ceremonias/      → Crear ceremonia
    PUT    /api/v1/sprints/{sprint_id}/ceremonias/{id}  → Actualizar
    DELETE /api/v1/sprints/{sprint_id}/ceremonias/{id}  → Eliminar
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.sprint import Sprint, EstadoSprint
from app.models.ceremonia_scrum import CeremoniaSprint
from app.schemas.ceremonia import CeremoniaCreate, CeremoniaUpdate, CeremoniaResponse
from app.api.v1.deps import get_current_user
from app.models.usuario import Usuario

router = APIRouter()


def _get_sprint_or_404(db: Session, sprint_id: int) -> Sprint:
    s = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not s:
        raise HTTPException(status_code=404, detail=f"Sprint {sprint_id} no encontrado")
    return s


def _get_ceremonia_or_404(db: Session, sprint_id: int, ceremonia_id: int) -> CeremoniaSprint:
    c = db.query(CeremoniaSprint).filter(
        CeremoniaSprint.id == ceremonia_id,
        CeremoniaSprint.sprint_id == sprint_id,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Ceremonia {ceremonia_id} no encontrada en Sprint {sprint_id}")
    return c


def _to_response(c: CeremoniaSprint) -> CeremoniaResponse:
    return CeremoniaResponse(
        id=c.id, sprint_id=c.sprint_id, tipo=c.tipo, fecha=c.fecha,
        duracion_minutos=c.duracion_minutos, participantes=c.participantes,
        notas=c.notas, creado_en=c.creado_en,
        horas_persona=round(c.duracion_minutos / 60 * c.participantes, 2),
    )


@router.get("/", response_model=list[CeremoniaResponse])
def listar_ceremonias(
    sprint_id: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(get_current_user),
) -> list[CeremoniaResponse]:
    _get_sprint_or_404(db, sprint_id)
    ceremonias = db.query(CeremoniaSprint).filter(
        CeremoniaSprint.sprint_id == sprint_id
    ).order_by(CeremoniaSprint.fecha, CeremoniaSprint.tipo).all()
    return [_to_response(c) for c in ceremonias]


@router.post("/", response_model=CeremoniaResponse, status_code=201)
def crear_ceremonia(
    sprint_id: int,
    payload: CeremoniaCreate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(get_current_user),
) -> CeremoniaResponse:
    """
    Registra una ceremonia Scrum en el sprint.

    Raises:
        400: Si el sprint está cerrado.
        400: Si el sprint_id del payload no coincide con la URL.
    """
    sprint = _get_sprint_or_404(db, sprint_id)
    if sprint.estado == EstadoSprint.CERRADO:
        raise HTTPException(400, detail="No se pueden agregar ceremonias a un sprint cerrado")
    if payload.sprint_id != sprint_id:
        raise HTTPException(400, detail="sprint_id del payload no coincide con la URL")

    c = CeremoniaSprint(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return _to_response(c)


@router.put("/{ceremonia_id}", response_model=CeremoniaResponse)
def actualizar_ceremonia(
    sprint_id: int,
    ceremonia_id: int,
    payload: CeremoniaUpdate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(get_current_user),
) -> CeremoniaResponse:
    c = _get_ceremonia_or_404(db, sprint_id, ceremonia_id)
    for campo, valor in payload.model_dump(exclude_none=True).items():
        setattr(c, campo, valor)
    db.commit()
    db.refresh(c)
    return _to_response(c)


@router.delete("/{ceremonia_id}", status_code=204)
def eliminar_ceremonia(
    sprint_id: int,
    ceremonia_id: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(get_current_user),
) -> None:
    c = _get_ceremonia_or_404(db, sprint_id, ceremonia_id)
    db.delete(c)
    db.commit()
