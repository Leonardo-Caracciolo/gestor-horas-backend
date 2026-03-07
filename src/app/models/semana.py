"""
models/semana.py — Semana laboral para cierre y exportación de Excel.
"""
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
import enum
from app.core.database import Base


class EstadoSemana(str, enum.Enum):
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class Semana(Base):
    """
    Representa una semana laboral (Lunes a Viernes).

    Es el período de cierre para el Excel oficial semanal.

    Attributes:
        fecha_inicio: Lunes de la semana.
        fecha_fin: Viernes de la semana.
        estado: Abierta (se pueden cargar horas) / Cerrada.
        excel_generado: Si ya se exportó el Excel de esta semana.
        sprint_id: Sprint al que pertenece esta semana.
    """
    __tablename__ = "semanas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[EstadoSemana] = mapped_column(
        Enum(EstadoSemana, name="estado_semana"),
        default=EstadoSemana.ABIERTA,
        nullable=False
    )
    sprint_id: Mapped[int | None] = mapped_column(
        ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True
    )
    excel_generado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cerrado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    sprint: Mapped["Sprint | None"] = relationship("Sprint")
