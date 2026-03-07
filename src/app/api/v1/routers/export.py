"""
routers/export.py — Export Excel semanal, cierre de semana y gestión de semanas.

Endpoints:
    GET    /api/v1/export/semanas/              → Listar semanas
    POST   /api/v1/export/semanas/              → Crear semana (admin)
    POST   /api/v1/export/semanas/{id}/cerrar   → Cerrar semana (cerrar_sprint)
    GET    /api/v1/export/semanas/{id}/excel    → Descargar Excel (exportar_excel)
    POST   /api/v1/export/teams/test            → Test de notificación Teams (admin)
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.semana import Semana, EstadoSemana
from app.schemas.semana import SemanaCreate, SemanaResponse
from app.api.v1.deps import get_current_user, require_permiso
from app.models.usuario import Usuario
from app.services.export_service import (
    generar_excel_semana, cerrar_semana, notificar_teams, notificar_semana_cerrada
)

router = APIRouter()


def _get_semana_or_404(db: Session, semana_id: int) -> Semana:
    s = db.query(Semana).filter(Semana.id == semana_id).first()
    if not s:
        raise HTTPException(status_code=404, detail=f"Semana {semana_id} no encontrada")
    return s


# ── Semanas ────────────────────────────────────────────────────────────────

@router.get(
    "/semanas/",
    response_model=list[SemanaResponse],
    summary="Listar semanas",
)
def listar_semanas(
    anio: int | None = Query(None),
    estado: EstadoSemana | None = Query(None),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(get_current_user),
) -> list[Semana]:
    q = db.query(Semana)
    if anio:
        q = q.filter(Semana.fecha_inicio >= date(anio, 1, 1),
                     Semana.fecha_inicio <= date(anio, 12, 31))
    if estado:
        q = q.filter(Semana.estado == estado)
    return q.order_by(Semana.fecha_inicio.desc()).all()


@router.post(
    "/semanas/",
    response_model=SemanaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear semana",
    dependencies=[Depends(require_permiso("admin_proyectos"))],
)
def crear_semana(
    payload: SemanaCreate,
    db: Session = Depends(get_db),
) -> Semana:
    semana = Semana(**payload.model_dump())
    db.add(semana)
    db.commit()
    db.refresh(semana)
    return semana


@router.post(
    "/semanas/{semana_id}/cerrar",
    response_model=SemanaResponse,
    summary="Cerrar semana",
    dependencies=[Depends(require_permiso("cerrar_sprint"))],
)
def cerrar_semana_endpoint(
    semana_id: int,
    db: Session = Depends(get_db),
    notificar: bool = Query(True, description="Enviar notificación Teams"),
) -> Semana:
    """
    Cierra la semana, bloqueando nuevas imputaciones.
    Opcionalmente envía notificación al canal de Teams.
    """
    semana = _get_semana_or_404(db, semana_id)
    try:
        semana = cerrar_semana(db, semana)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if notificar:
        notificar_semana_cerrada(db, semana)

    return semana


# ── Export Excel ───────────────────────────────────────────────────────────

@router.get(
    "/semanas/{semana_id}/excel",
    summary="Descargar Excel de la semana",
    responses={200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}}},
    dependencies=[Depends(require_permiso("exportar_excel"))],
)
def descargar_excel(
    semana_id: int,
    solo_aprobados: bool = Query(True),
    db: Session = Depends(get_db),
) -> Response:
    """
    Genera y descarga el Excel con las horas de la semana.

    Args:
        solo_aprobados: Si True (default) solo incluye registros Aprobados.
                        Si False, incluye también Enviados (para preview).
    """
    semana = _get_semana_or_404(db, semana_id)
    excel_bytes = generar_excel_semana(db, semana, solo_aprobados=solo_aprobados)

    # Marcar que el Excel fue generado
    semana.excel_generado = True
    db.commit()

    filename = f"horas_{semana.fecha_inicio.strftime('%Y%m%d')}_{semana.fecha_fin.strftime('%Y%m%d')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Teams ──────────────────────────────────────────────────────────────────

@router.post(
    "/teams/test",
    summary="Probar notificación Teams",
    dependencies=[Depends(require_permiso("admin_proyectos"))],
)
def test_teams(
    _u: Usuario = Depends(get_current_user),
) -> dict:
    """Envía un mensaje de prueba al canal de Teams configurado."""
    enviado = notificar_teams(
        titulo="🔔 Test de notificación",
        mensaje=f"Notificación de prueba enviada por **{_u.nombre}**.",
    )
    return {
        "enviado": enviado,
        "mensaje": "Notificación enviada" if enviado else "TEAMS_WEBHOOK_URL no configurado",
    }
