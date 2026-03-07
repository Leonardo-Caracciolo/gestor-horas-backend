"""
schemas/ado_item.py — Schemas Pydantic para ítems de Azure DevOps.
"""
from pydantic import BaseModel
from datetime import datetime
from app.models.ado_item import TipoAdoItem


class AdoItemResponse(BaseModel):
    id: int
    ado_id: int
    tipo: TipoAdoItem
    titulo: str
    asignado_a: str | None = None
    estado: str | None = None
    proyecto_id: int
    sprint_id: int | None = None
    parent_id: int | None = None
    activo: bool
    ultima_sync: datetime | None = None

    model_config = {"from_attributes": True}


class AdoItemArbol(BaseModel):
    """AdoItem con sus hijos embebidos (para mostrar jerarquía)."""
    id: int
    ado_id: int
    tipo: TipoAdoItem
    titulo: str
    asignado_a: str | None = None
    estado: str | None = None
    hijos: list["AdoItemArbol"] = []

    model_config = {"from_attributes": True}


AdoItemArbol.model_rebuild()
