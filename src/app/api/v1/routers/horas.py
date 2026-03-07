"""
routers/horas.py — Carga, edición y flujo de aprobación de horas.

Endpoints:
    GET    /api/v1/horas/                     → Listar registros del usuario autenticado
    POST   /api/v1/horas/                     → Crear registro (cualquier usuario)
    GET    /api/v1/horas/semana               → Resumen de la semana actual
    GET    /api/v1/horas/{id}                 → Obtener registro por ID
    PUT    /api/v1/horas/{id}                 → Editar (solo Borrador, solo propietario)
    DELETE /api/v1/horas/{id}                 → Eliminar (solo Borrador, solo propietario)
    POST   /api/v1/horas/enviar               → Enviar semana a aprobación
    POST   /api/v1/horas/{id}/aprobar         → Aprobar/rechazar (aprobar_horas)
    POST   /api/v1/horas/timer/iniciar        → Iniciar timer
    POST   /api/v1/horas/{id}/timer/detener   → Detener timer
    GET    /api/v1/horas/equipo               → Ver horas del equipo (ver_horas_equipo)
"""
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.registro_hora import RegistroHora, EstadoRegistro
from app.models.usuario import Usuario
from app.schemas.hora import (
    RegistroHoraCreate, RegistroHoraUpdate, RegistroHoraResponse,
    ResumenDiario, AprobacionRequest, AprobacionResponse,
    TimerInicioResponse, TimerStopResponse,
)
from app.api.v1.deps import get_current_user, require_permiso
from app.services import hora_service

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, registro_id: int) -> RegistroHora:
    r = db.query(RegistroHora).filter(RegistroHora.id == registro_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Registro {registro_id} no encontrado")
    return r


def _verificar_propietario(registro: RegistroHora, usuario: Usuario) -> None:
    """Verifica que el registro pertenezca al usuario (o que tenga permiso de equipo)."""
    if registro.usuario_id != usuario.id and not usuario.tiene_permiso("ver_horas_equipo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permiso para acceder a este registro",
        )


def _lunes_semana(ref: date) -> date:
    """Retorna el lunes de la semana que contiene `ref`."""
    return ref - timedelta(days=ref.weekday())


# ── CRUD básico ────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[RegistroHoraResponse],
    summary="Listar registros propios",
)
def listar_registros(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    estado: EstadoRegistro | None = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[RegistroHora]:
    """Lista los registros del usuario autenticado con filtros opcionales."""
    q = db.query(RegistroHora).filter(RegistroHora.usuario_id == usuario.id)
    if fecha_desde:
        q = q.filter(RegistroHora.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(RegistroHora.fecha <= fecha_hasta)
    if estado:
        q = q.filter(RegistroHora.estado == estado)
    return q.order_by(RegistroHora.fecha.desc()).all()


@router.post(
    "/",
    response_model=RegistroHoraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear registro de horas",
)
def crear_registro(
    payload: RegistroHoraCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> RegistroHora:
    """
    Crea un nuevo registro de horas para el usuario autenticado.

    Raises:
        400: Feriado, fin de semana, semana cerrada, o límite diario superado.
    """
    try:
        return hora_service.crear_registro(db, usuario.id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/semana",
    response_model=list[ResumenDiario],
    summary="Resumen de la semana actual",
)
def semana_actual(
    fecha_ref: date | None = Query(None, description="Fecha de referencia (default: hoy)"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[ResumenDiario]:
    """
    Retorna un resumen día a día de la semana que contiene `fecha_ref`.
    Incluye todos los registros de cada día (Lunes a Viernes).
    """
    ref = fecha_ref or date.today()
    lunes = _lunes_semana(ref)
    viernes = lunes + timedelta(days=4)

    registros = db.query(RegistroHora).filter(
        RegistroHora.usuario_id == usuario.id,
        RegistroHora.fecha >= lunes,
        RegistroHora.fecha <= viernes,
    ).order_by(RegistroHora.fecha, RegistroHora.id).all()

    # Agrupar por día
    por_dia: dict[date, list[RegistroHora]] = {}
    for i in range(5):
        por_dia[lunes + timedelta(days=i)] = []
    for r in registros:
        por_dia.setdefault(r.fecha, []).append(r)

    return [
        ResumenDiario(
            fecha=d,
            total_horas=sum((r.horas for r in rs), Decimal("0.00")),
            registros=rs,
        )
        for d, rs in sorted(por_dia.items())
    ]


@router.get(
    "/equipo",
    response_model=list[RegistroHoraResponse],
    summary="Ver horas del equipo",
    dependencies=[Depends(require_permiso("ver_horas_equipo"))],
)
def horas_equipo(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    usuario_id: int | None = Query(None),
    estado: EstadoRegistro | None = Query(None),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(get_current_user),
) -> list[RegistroHora]:
    """Vista de Tech Lead / Gerente: horas de todo el equipo con filtros."""
    q = db.query(RegistroHora)
    if usuario_id:
        q = q.filter(RegistroHora.usuario_id == usuario_id)
    if fecha_desde:
        q = q.filter(RegistroHora.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(RegistroHora.fecha <= fecha_hasta)
    if estado:
        q = q.filter(RegistroHora.estado == estado)
    return q.order_by(RegistroHora.fecha.desc(), RegistroHora.usuario_id).all()


@router.get(
    "/{registro_id}",
    response_model=RegistroHoraResponse,
    summary="Obtener registro por ID",
)
def obtener_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> RegistroHora:
    registro = _get_or_404(db, registro_id)
    _verificar_propietario(registro, usuario)
    return registro


@router.put(
    "/{registro_id}",
    response_model=RegistroHoraResponse,
    summary="Editar registro (solo Borrador)",
)
def editar_registro(
    registro_id: int,
    payload: RegistroHoraUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> RegistroHora:
    """
    Edita un registro en estado Borrador.

    Raises:
        403: Si no es el propietario.
        400: Si no está en Borrador.
    """
    registro = _get_or_404(db, registro_id)
    if registro.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="No podés editar registros ajenos")
    try:
        return hora_service.actualizar_registro(db, registro, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{registro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar registro (solo Borrador)",
)
def eliminar_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> None:
    registro = _get_or_404(db, registro_id)
    if registro.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="No podés eliminar registros ajenos")
    try:
        hora_service.eliminar_registro(db, registro)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Envío ──────────────────────────────────────────────────────────────────

class EnviarRequest:
    pass

from pydantic import BaseModel as _BM

class EnviarSemanaRequest(_BM):
    fecha_inicio: date
    fecha_fin: date


@router.post(
    "/enviar",
    response_model=list[RegistroHoraResponse],
    summary="Enviar semana a aprobación",
)
def enviar_semana(
    payload: EnviarSemanaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[RegistroHora]:
    """
    Envía todos los registros Borrador del rango de fechas a estado Enviado.

    Returns:
        Lista de registros ahora en estado Enviado.
    """
    return hora_service.enviar_registros(
        db, usuario.id, payload.fecha_inicio, payload.fecha_fin
    )


# ── Aprobación ─────────────────────────────────────────────────────────────

@router.post(
    "/{registro_id}/aprobar",
    response_model=AprobacionResponse,
    summary="Aprobar o rechazar registro",
    dependencies=[Depends(require_permiso("aprobar_horas"))],
)
def aprobar_registro(
    registro_id: int,
    payload: AprobacionRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> object:
    """
    Aprueba o rechaza un registro de horas en estado Enviado.

    Raises:
        400: Si el registro no está en estado Enviado.
        422: Si se rechaza sin comentario.
    """
    registro = _get_or_404(db, registro_id)
    try:
        return hora_service.procesar_aprobacion(db, registro, usuario.id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Timer ──────────────────────────────────────────────────────────────────

class TimerIniciarRequest(_BM):
    fecha: date
    proyecto_id: int
    descripcion: str
    ado_task_id: int | None = None
    tarea_manual: str | None = None


@router.post(
    "/timer/iniciar",
    response_model=TimerInicioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar timer",
)
def iniciar_timer(
    payload: TimerIniciarRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> TimerInicioResponse:
    """
    Inicia un timer para la tarea especificada.

    Solo puede haber un timer activo por usuario a la vez.

    Raises:
        400: Si ya hay un timer activo.
        400: Si la fecha no es hábil.
    """
    try:
        registro = hora_service.iniciar_timer(
            db,
            usuario_id=usuario.id,
            proyecto_id=payload.proyecto_id,
            descripcion=payload.descripcion,
            fecha=payload.fecha,
            ado_task_id=payload.ado_task_id,
            tarea_manual=payload.tarea_manual,
        )
        return TimerInicioResponse(
            registro_id=registro.id,
            timer_inicio=registro.timer_inicio,
            mensaje="Timer iniciado",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{registro_id}/timer/detener",
    response_model=TimerStopResponse,
    summary="Detener timer",
)
def detener_timer(
    registro_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> TimerStopResponse:
    """
    Detiene el timer activo y calcula las horas transcurridas.

    Las horas se redondean a 2 decimales con mínimo 0.25h (15 min).

    Raises:
        403: Si el registro no pertenece al usuario.
        400: Si el registro no tiene timer activo.
        400: Si las horas calculadas superan el límite diario.
    """
    registro = _get_or_404(db, registro_id)
    if registro.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="No podés detener timers ajenos")
    try:
        registro = hora_service.detener_timer(db, registro)
        return TimerStopResponse(
            registro_id=registro.id,
            horas=registro.horas,
            mensaje=f"Timer detenido. Horas registradas: {registro.horas}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
