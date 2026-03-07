"""
schemas/ceremonia.py — Schemas Pydantic para ceremonias Scrum.
"""
from pydantic import BaseModel, field_validator
from datetime import date, datetime
from app.models.ceremonia_scrum import TipoCeremonia


class CeremoniaCreate(BaseModel):
    sprint_id: int
    tipo: TipoCeremonia
    fecha: date
    duracion_minutos: int
    participantes: int = 1
    notas: str | None = None

    @field_validator("duracion_minutos")
    @classmethod
    def duracion_positiva(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("La duración debe ser mayor a 0 minutos")
        return v

    @field_validator("participantes")
    @classmethod
    def participantes_positivos(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Debe haber al menos 1 participante")
        return v


class CeremoniaUpdate(BaseModel):
    duracion_minutos: int | None = None
    participantes: int | None = None
    notas: str | None = None


class CeremoniaResponse(BaseModel):
    id: int
    sprint_id: int
    tipo: TipoCeremonia
    fecha: date
    duracion_minutos: int
    participantes: int
    notas: str | None = None
    creado_en: datetime
    horas_persona: float  # duracion_minutos/60 * participantes

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_horas(cls, obj) -> "CeremoniaResponse":
        data = {c: getattr(obj, c) for c in obj.__table__.columns.keys()}
        data["horas_persona"] = round(obj.duracion_minutos / 60 * obj.participantes, 2)
        return cls(**data)
