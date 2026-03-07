"""
schemas/feriado.py — Schemas Pydantic para ABM de feriados.
"""
from pydantic import BaseModel, field_validator
from datetime import date, datetime


class FeriadoCreate(BaseModel):
    fecha: date
    nombre: str
    aplica_a_todos: bool = True

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre del feriado no puede estar vacío")
        return v.strip()


class FeriadoUpdate(BaseModel):
    nombre: str | None = None
    aplica_a_todos: bool | None = None


class FeriadoResponse(BaseModel):
    id: int
    fecha: date
    nombre: str
    aplica_a_todos: bool
    anio: int
    creado_en: datetime

    model_config = {"from_attributes": True}
