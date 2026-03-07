"""
schemas/semana.py — Schemas Pydantic para gestión de semanas.
"""
from pydantic import BaseModel, model_validator
from datetime import date, datetime
from app.models.semana import EstadoSemana


class SemanaCreate(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    sprint_id: int | None = None

    @model_validator(mode="after")
    def fechas_validas(self) -> "SemanaCreate":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin debe ser >= fecha_inicio")
        return self


class CerrarSemanaRequest(BaseModel):
    """Payload para cerrar una semana y bloquear imputaciones."""
    semana_id: int


class SemanaResponse(BaseModel):
    id: int
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoSemana
    sprint_id: int | None = None
    excel_generado: bool
    cerrado_en: datetime | None = None
    creado_en: datetime

    model_config = {"from_attributes": True}
