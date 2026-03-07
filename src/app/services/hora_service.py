"""
services/hora_service.py — Validaciones y lógica de negocio para horas.

Centraliza todas las reglas de negocio del flujo de carga:
  - No cargar horas en feriados ni fines de semana
  - No superar 12 horas diarias por usuario
  - Solo editar/eliminar registros en estado Borrador
  - Semana cerrada no acepta nuevas imputaciones
  - Timer: solo un timer activo por usuario
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from app.models.registro_hora import RegistroHora, EstadoRegistro
from app.models.feriado import Feriado
from app.models.semana import Semana, EstadoSemana
from app.models.aprobacion import Aprobacion, EstadoAprobacion
from app.schemas.hora import RegistroHoraCreate, RegistroHoraUpdate, AprobacionRequest

logger = logging.getLogger(__name__)

MAX_HORAS_DIARIAS = Decimal("12.00")


# ── Validaciones de contexto ───────────────────────────────────────────────

def _validar_dia_habil(db: Session, fecha) -> None:
    """
    Verifica que la fecha sea un día hábil (no feriado, no fin de semana).

    Args:
        db: Sesión de BD.
        fecha: Fecha a validar.

    Raises:
        ValueError: Si la fecha cae en fin de semana o feriado.
    """
    # Fin de semana (weekday: 5=sábado, 6=domingo)
    if fecha.weekday() >= 5:
        raise ValueError(
            f"{fecha.strftime('%d/%m/%Y')} es fin de semana, no se pueden cargar horas"
        )

    # Feriado
    feriado = db.query(Feriado).filter(
        Feriado.fecha == fecha,
        Feriado.aplica_a_todos == True,
    ).first()
    if feriado:
        raise ValueError(
            f"{fecha.strftime('%d/%m/%Y')} es feriado: '{feriado.nombre}'"
        )


def _validar_semana_abierta(db: Session, fecha) -> None:
    """
    Verifica que la semana no esté cerrada para nuevas imputaciones.

    Si no existe semana para esa fecha, se considera abierta.

    Raises:
        ValueError: Si la semana está cerrada.
    """
    semana = db.query(Semana).filter(
        Semana.fecha_inicio <= fecha,
        Semana.fecha_fin >= fecha,
    ).first()
    if semana and semana.estado == EstadoSemana.CERRADA:
        raise ValueError(
            f"La semana del {semana.fecha_inicio} al {semana.fecha_fin} está cerrada"
        )


def _validar_limite_horas(
    db: Session, usuario_id: int, fecha, horas_nuevas: Decimal,
    excluir_id: int | None = None,
) -> None:
    """
    Verifica que el usuario no supere 12 horas diarias.

    Args:
        excluir_id: ID de registro a excluir (para ediciones).

    Raises:
        ValueError: Si sumar las horas nuevas supera MAX_HORAS_DIARIAS.
    """
    q = db.query(sqlfunc.sum(RegistroHora.horas)).filter(
        RegistroHora.usuario_id == usuario_id,
        RegistroHora.fecha == fecha,
        RegistroHora.estado != EstadoRegistro.RECHAZADO,
    )
    if excluir_id:
        q = q.filter(RegistroHora.id != excluir_id)

    total_actual = q.scalar() or Decimal("0.00")
    if total_actual + horas_nuevas > MAX_HORAS_DIARIAS:
        raise ValueError(
            f"Superaría el límite de {MAX_HORAS_DIARIAS}h diarias "
            f"(actuales: {total_actual}h, nuevas: {horas_nuevas}h)"
        )


# ── Operaciones principales ────────────────────────────────────────────────

def crear_registro(
    db: Session,
    usuario_id: int,
    payload: RegistroHoraCreate,
) -> RegistroHora:
    """
    Crea un nuevo registro de horas aplicando todas las validaciones.

    Validaciones:
        - Día hábil (no feriado, no fin de semana).
        - Semana abierta.
        - Límite diario de 12 horas.

    Args:
        db: Sesión de BD.
        usuario_id: ID del usuario autenticado.
        payload: Datos del registro a crear.

    Returns:
        El RegistroHora persistido en estado Borrador.

    Raises:
        ValueError: Si alguna validación falla.
    """
    _validar_dia_habil(db, payload.fecha)
    _validar_semana_abierta(db, payload.fecha)
    _validar_limite_horas(db, usuario_id, payload.fecha, payload.horas)

    registro = RegistroHora(
        usuario_id=usuario_id,
        fecha=payload.fecha,
        proyecto_id=payload.proyecto_id,
        ado_task_id=payload.ado_task_id,
        descripcion=payload.descripcion,
        tarea_manual=payload.tarea_manual,
        horas=payload.horas,
        es_ceremonia=payload.es_ceremonia,
        estado=EstadoRegistro.BORRADOR,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    logger.info(f"Registro creado id={registro.id} usuario={usuario_id}")
    return registro


def actualizar_registro(
    db: Session,
    registro: RegistroHora,
    payload: RegistroHoraUpdate,
) -> RegistroHora:
    """
    Actualiza un registro solo si está en estado Borrador.

    Raises:
        ValueError: Si el registro no está en Borrador.
        ValueError: Si el nuevo total de horas supera el límite.
    """
    if registro.estado != EstadoRegistro.BORRADOR:
        raise ValueError(
            f"Solo se pueden editar registros en Borrador (estado: {registro.estado})"
        )

    horas_nuevas = payload.horas if payload.horas is not None else registro.horas
    if payload.horas is not None:
        _validar_limite_horas(
            db, registro.usuario_id, registro.fecha, horas_nuevas,
            excluir_id=registro.id,
        )

    for campo, valor in payload.model_dump(exclude_none=True).items():
        setattr(registro, campo, valor)

    db.commit()
    db.refresh(registro)
    return registro


def eliminar_registro(db: Session, registro: RegistroHora) -> None:
    """
    Elimina un registro solo si está en estado Borrador.

    Raises:
        ValueError: Si el registro no está en Borrador.
    """
    if registro.estado != EstadoRegistro.BORRADOR:
        raise ValueError(
            f"Solo se pueden eliminar registros en Borrador (estado: {registro.estado})"
        )
    db.delete(registro)
    db.commit()


def enviar_registros(
    db: Session,
    usuario_id: int,
    fecha_inicio,
    fecha_fin,
) -> list[RegistroHora]:
    """
    Envía a aprobación todos los registros Borrador del usuario en el rango.

    Args:
        fecha_inicio / fecha_fin: Rango de fechas (típicamente una semana).

    Returns:
        Lista de registros cuyo estado cambió a Enviado.
    """
    registros = db.query(RegistroHora).filter(
        RegistroHora.usuario_id == usuario_id,
        RegistroHora.fecha >= fecha_inicio,
        RegistroHora.fecha <= fecha_fin,
        RegistroHora.estado == EstadoRegistro.BORRADOR,
    ).all()

    for r in registros:
        r.estado = EstadoRegistro.ENVIADO

    db.commit()
    logger.info(f"Usuario {usuario_id} envió {len(registros)} registros")
    return registros


def procesar_aprobacion(
    db: Session,
    registro: RegistroHora,
    aprobador_id: int,
    payload: AprobacionRequest,
) -> Aprobacion:
    """
    Aprueba o rechaza un registro de horas.

    Solo se pueden procesar registros en estado Enviado.

    Args:
        registro: El registro a procesar.
        aprobador_id: ID del usuario que aprueba/rechaza.
        payload: Decisión y comentario opcional.

    Returns:
        La Aprobacion creada.

    Raises:
        ValueError: Si el registro no está en estado Enviado.
    """
    if registro.estado != EstadoRegistro.ENVIADO:
        raise ValueError(
            f"Solo se pueden aprobar/rechazar registros Enviados (estado: {registro.estado})"
        )

    nuevo_estado_registro = (
        EstadoRegistro.APROBADO if payload.aprobar else EstadoRegistro.RECHAZADO
    )
    nuevo_estado_aprobacion = (
        EstadoAprobacion.APROBADO if payload.aprobar else EstadoAprobacion.RECHAZADO
    )

    registro.estado = nuevo_estado_registro

    aprobacion = Aprobacion(
        registro_id=registro.id,
        aprobador_id=aprobador_id,
        estado=nuevo_estado_aprobacion,
        comentario=payload.comentario,
    )
    db.add(aprobacion)
    db.commit()
    db.refresh(aprobacion)
    return aprobacion


# ── Timer ──────────────────────────────────────────────────────────────────

def iniciar_timer(
    db: Session,
    usuario_id: int,
    proyecto_id: int,
    descripcion: str,
    fecha,
    ado_task_id: int | None = None,
    tarea_manual: str | None = None,
) -> RegistroHora:
    """
    Inicia el timer para un nuevo registro.

    Solo puede haber un timer activo (timer_inicio != null) por usuario.

    Raises:
        ValueError: Si ya hay un timer activo.
        ValueError: Si la fecha no es hábil.
    """
    activo = db.query(RegistroHora).filter(
        RegistroHora.usuario_id == usuario_id,
        RegistroHora.timer_inicio != None,
    ).first()
    if activo:
        raise ValueError(
            f"Ya hay un timer activo para el registro id={activo.id}. "
            "Detené el timer anterior antes de iniciar uno nuevo."
        )

    _validar_dia_habil(db, fecha)
    _validar_semana_abierta(db, fecha)

    ahora = datetime.now(timezone.utc)
    registro = RegistroHora(
        usuario_id=usuario_id,
        fecha=fecha,
        proyecto_id=proyecto_id,
        ado_task_id=ado_task_id,
        descripcion=descripcion,
        tarea_manual=tarea_manual,
        horas=Decimal("0.00"),
        estado=EstadoRegistro.BORRADOR,
        timer_inicio=ahora,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def detener_timer(db: Session, registro: RegistroHora) -> RegistroHora:
    """
    Detiene el timer, calcula las horas transcurridas y las guarda.

    Las horas se calculan como (ahora - timer_inicio), redondeadas a 2 decimales.
    Mínimo registrable: 0.25h (15 min). Máximo: aplican las reglas de límite diario.

    Raises:
        ValueError: Si el registro no tiene timer activo.
        ValueError: Si las horas calculadas superan el límite diario.
    """
    if not registro.timer_inicio:
        raise ValueError("Este registro no tiene un timer activo")

    ahora = datetime.now(timezone.utc)
    inicio = registro.timer_inicio
    if inicio.tzinfo is None:
        from datetime import timezone as tz
        inicio = inicio.replace(tzinfo=tz.utc)

    delta_horas = Decimal(str(round((ahora - inicio).total_seconds() / 3600, 2)))
    delta_horas = max(delta_horas, Decimal("0.25"))  # mínimo 15 min

    _validar_limite_horas(
        db, registro.usuario_id, registro.fecha, delta_horas,
        excluir_id=registro.id,
    )

    registro.horas = delta_horas
    registro.timer_inicio = None
    db.commit()
    db.refresh(registro)
    return registro
