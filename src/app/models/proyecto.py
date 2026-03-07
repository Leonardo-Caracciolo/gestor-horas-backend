"""
models/proyecto.py — Modelo de Proyecto.
"""
from sqlalchemy import String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from app.core.database import Base


class TipoProyecto(str, enum.Enum):
    """
    Tipo de proyecto según el campo 'Tipo' del Excel oficial.

    Values:
        PROYECTO: Trabajo en un proyecto de desarrollo.
        OFICINA: Tareas administrativas, reuniones internas, etc.
    """
    PROYECTO = "Proyecto"
    OFICINA = "Oficina"


class Proyecto(Base):
    """
    Representa un proyecto o centro de costo para imputación de horas.

    Attributes:
        id: Identificador interno.
        nombre: Nombre descriptivo del proyecto.
        tipo: "Proyecto" u "Oficina" (campo Tipo del Excel).
        id_proyecto_excel: Código que aparece en el Excel oficial.
        ado_project_name: Nombre del proyecto en Azure DevOps.
        activo: Si se puede imputar horas contra este proyecto.

    Relationships:
        sprints: Sprints asociados a este proyecto.
        registros_horas: Registros de horas imputados.
    """
    __tablename__ = "proyectos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[TipoProyecto] = mapped_column(
        Enum(TipoProyecto, name="tipo_proyecto"), nullable=False
    )
    id_proyecto_excel: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    ado_project_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────
    sprints: Mapped[list["Sprint"]] = relationship("Sprint", back_populates="proyecto")
    ado_items: Mapped[list["AdoItem"]] = relationship(
        "AdoItem", back_populates="proyecto"
    )
    registros_horas: Mapped[list["RegistroHora"]] = relationship(
        "RegistroHora", back_populates="proyecto"
    )

    def __repr__(self) -> str:
        return f"<Proyecto id={self.id} nombre={self.nombre!r} tipo={self.tipo}>"
