"""
models/ado_item.py — Jerarquía de ítems de Azure DevOps (Épica→Feature→US→Task).

Se sincronizan automáticamente desde ADO via Dagster (job nocturno).
"""
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from app.core.database import Base


class TipoAdoItem(str, enum.Enum):
    """Tipo de ítem en la jerarquía de Azure DevOps."""
    EPIC = "Epic"
    FEATURE = "Feature"
    USER_STORY = "User Story"
    TASK = "Task"


class AdoItem(Base):
    """
    Representa un ítem de Azure DevOps (Epic, Feature, User Story o Task).

    La jerarquía se mantiene via parent_id (autorreferencia).
    Solo los Tasks son seleccionables al cargar horas.

    Attributes:
        id: Identificador interno.
        ado_id: ID numérico en Azure DevOps (Work Item ID).
        tipo: Epic, Feature, User Story o Task.
        titulo: Título del Work Item.
        asignado_a: Email del integrante asignado en ADO.
        proyecto_id: FK al proyecto correspondiente.
        sprint_id: FK al sprint al que pertenece.
        parent_id: FK al ítem padre (autorreferencia).
        estado: Estado en ADO (Active, Resolved, Closed, etc.).
        activo: Si el ítem está vigente (no fue eliminado en ADO).
        ultima_sync: Última vez que se sincronizó desde ADO.

    Relationships:
        proyecto: Proyecto al que pertenece.
        sprint: Sprint al que fue asignado.
        padre: Ítem padre (Feature de una US, US de una Task).
        hijos: Ítems hijos.
        registros_horas: Registros de horas contra esta tarea.
    """
    __tablename__ = "ado_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ado_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    tipo: Mapped[TipoAdoItem] = mapped_column(
        Enum(TipoAdoItem, name="tipo_ado_item"), nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    asignado_a: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False
    )
    sprint_id: Mapped[int | None] = mapped_column(
        ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("ado_items.id", ondelete="SET NULL"), nullable=True
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultima_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────
    proyecto: Mapped["Proyecto"] = relationship("Proyecto", back_populates="ado_items")
    sprint: Mapped["Sprint | None"] = relationship("Sprint", back_populates="ado_items")
    padre: Mapped["AdoItem | None"] = relationship(
        "AdoItem", remote_side="AdoItem.id", back_populates="hijos"
    )
    hijos: Mapped[list["AdoItem"]] = relationship(
        "AdoItem", back_populates="padre"
    )
    registros_horas: Mapped[list["RegistroHora"]] = relationship(
        "RegistroHora", back_populates="ado_task"
    )

    def __repr__(self) -> str:
        return f"<AdoItem ado_id={self.ado_id} tipo={self.tipo} titulo={self.titulo[:40]!r}>"
