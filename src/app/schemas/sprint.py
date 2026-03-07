"""
schemas/sprint.py — Schemas Pydantic para ABM de sprints.
"""
from pydantic import BaseModel, model_validator
from datetime import date, datetime
from app.models.sprint import EstadoSprint


class SprintCreate(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    proyecto_id: int
    ado_sprint_id: str | None = None

    @model_validator(mode="after")
    def fechas_validas(self) -> "SprintCreate":
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return self


class SprintUpdate(BaseModel):
    nombre: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    estado: EstadoSprint | None = None
    ado_sprint_id: str | None = None


class SprintResponse(BaseModel):
    id: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoSprint
    proyecto_id: int
    ado_sprint_id: str | None = None
    excel_generado: bool
    creado_en: datetime

    model_config = {"from_attributes": True}


class SprintResumen(BaseModel):
    id: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoSprint
    proyecto_id: int

    model_config = {"from_attributes": True}
