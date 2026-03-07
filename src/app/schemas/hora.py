"""
schemas/hora.py — Schemas Pydantic para carga de horas.
"""
from pydantic import BaseModel, field_validator, model_validator
from datetime import date, datetime
from decimal import Decimal
from app.models.registro_hora import EstadoRegistro


# ── Entrada ───────────────────────────────────────────────────────────────


class RegistroHoraCreate(BaseModel):
    """Payload para crear un registro de horas."""
    fecha: date
    proyecto_id: int
    descripcion: str
    horas: Decimal
    ado_task_id: int | None = None
    tarea_manual: str | None = None
    es_ceremonia: bool = False

    @field_validator("horas")
    @classmethod
    def horas_positivas(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Las horas deben ser mayor a 0")
        if v > 24:
            raise ValueError("No se pueden cargar más de 24 horas en un día")
        return round(v, 2)

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

    @model_validator(mode="after")
    def tarea_requerida(self) -> "RegistroHoraCreate":
        if not self.es_ceremonia and not self.ado_task_id and not self.tarea_manual:
            raise ValueError(
                "Se requiere ado_task_id o tarea_manual cuando no es una ceremonia"
            )
        return self


class RegistroHoraUpdate(BaseModel):
    """Payload para editar un registro en estado Borrador."""
    descripcion: str | None = None
    horas: Decimal | None = None
    ado_task_id: int | None = None
    tarea_manual: str | None = None

    @field_validator("horas")
    @classmethod
    def horas_positivas(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            if v <= 0:
                raise ValueError("Las horas deben ser mayor a 0")
            if v > 24:
                raise ValueError("No se pueden cargar más de 24 horas en un día")
            return round(v, 2)
        return v


class AprobacionRequest(BaseModel):
    """Payload para aprobar o rechazar un registro de horas."""
    aprobar: bool
    comentario: str | None = None

    @model_validator(mode="after")
    def comentario_requerido_si_rechaza(self) -> "AprobacionRequest":
        if not self.aprobar and not self.comentario:
            raise ValueError("Se requiere comentario al rechazar un registro")
        return self


# ── Salida ────────────────────────────────────────────────────────────────


class AprobacionResponse(BaseModel):
    id: int
    registro_id: int
    aprobador_id: int
    estado: str
    comentario: str | None = None
    resuelto_en: datetime

    model_config = {"from_attributes": True}


class RegistroHoraResponse(BaseModel):
    id: int
    usuario_id: int
    fecha: date
    proyecto_id: int
    ado_task_id: int | None = None
    descripcion: str
    tarea_manual: str | None = None
    horas: Decimal
    estado: EstadoRegistro
    timer_inicio: datetime | None = None
    es_ceremonia: bool
    creado_en: datetime
    actualizado_en: datetime
    aprobacion: AprobacionResponse | None = None

    model_config = {"from_attributes": True}


class ResumenDiario(BaseModel):
    """Resumen de horas por día (para la vista de la semana)."""
    fecha: date
    total_horas: Decimal
    registros: list[RegistroHoraResponse]


class TimerInicioResponse(BaseModel):
    registro_id: int
    timer_inicio: datetime
    mensaje: str


class TimerStopResponse(BaseModel):
    registro_id: int
    horas: Decimal
    mensaje: str
