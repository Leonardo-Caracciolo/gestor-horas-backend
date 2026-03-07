"""
models/sprint.py — Modelo de Sprint de Azure DevOps.
"""
from sqlalchemy import String, Boolean, DateTime, Date, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
import enum
from app.core.database import Base


class EstadoSprint(str, enum.Enum):
    PLANIFICADO = "Planificado"
    ACTIVO = "Activo"
    CERRADO = "Cerrado"


class Sprint(Base):
    """
    Representa un Sprint de dos semanas en Azure DevOps.

    Attributes:
        id: Identificador interno.
        nombre: Nombre del sprint (ej: "Sprint 23").
        fecha_inicio: Primer día del sprint (lunes).
        fecha_fin: Último día del sprint (viernes de la 2da semana).
        estado: Planificado / Activo / Cerrado.
        proyecto_id: FK al proyecto.
        ado_sprint_id: ID del iteration en Azure DevOps.
        excel_generado: Si ya se exportó el Excel de las 2 semanas.
    """
    __tablename__ = "sprints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[EstadoSprint] = mapped_column(
        Enum(EstadoSprint, name="estado_sprint"),
        default=EstadoSprint.PLANIFICADO,
        nullable=False
    )
    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False
    )
    ado_sprint_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    excel_generado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────
    proyecto: Mapped["Proyecto"] = relationship("Proyecto", back_populates="sprints")
    ado_items: Mapped[list["AdoItem"]] = relationship(
        "AdoItem", back_populates="sprint"
    )
    horas_planificadas: Mapped[list["HoraPlanificadaSprint"]] = relationship(
        "HoraPlanificadaSprint", back_populates="sprint", cascade="all, delete-orphan"
    )
    ceremonias: Mapped[list["CeremoniaSprint"]] = relationship(
        "CeremoniaSprint", back_populates="sprint", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Sprint nombre={self.nombre!r} estado={self.estado}>"
