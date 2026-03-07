"""
schemas/proyecto.py — Schemas Pydantic para ABM de proyectos.
"""
from pydantic import BaseModel, field_validator
from datetime import datetime
from app.models.proyecto import TipoProyecto


class ProyectoCreate(BaseModel):
    nombre: str
    tipo: TipoProyecto
    id_proyecto_excel: str
    ado_project_name: str | None = None
    descripcion: str | None = None

    @field_validator("id_proyecto_excel")
    @classmethod
    def excel_id_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("id_proyecto_excel no puede estar vacío")
        return v.strip().upper()


class ProyectoUpdate(BaseModel):
    nombre: str | None = None
    ado_project_name: str | None = None
    descripcion: str | None = None
    activo: bool | None = None


class ProyectoResponse(BaseModel):
    id: int
    nombre: str
    tipo: TipoProyecto
    id_proyecto_excel: str
    ado_project_name: str | None = None
    descripcion: str | None = None
    activo: bool
    creado_en: datetime

    model_config = {"from_attributes": True}


class ProyectoResumen(BaseModel):
    id: int
    nombre: str
    tipo: TipoProyecto
    id_proyecto_excel: str
    activo: bool

    model_config = {"from_attributes": True}


class SyncAdoResponse(BaseModel):
    """Resultado de una sincronización con Azure DevOps."""
    proyecto_id: int
    ado_project_name: str
    epicas: int
    features: int
    user_stories: int
    tasks: int
    total: int
    mensaje: str
