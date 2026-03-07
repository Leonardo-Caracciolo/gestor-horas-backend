"""
models/ceremonia_scrum.py — Ceremonias Scrum registradas por sprint.
"""
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
import enum
from app.core.database import Base


class TipoCeremonia(str, enum.Enum):
    PLANNING = "Planning"
    DAILY = "Daily"
    REVIEW = "Review"
    RETRO = "Retro"
    REFINEMENT = "Refinement"
    OTRO = "Otro"


class CeremoniaSprint(Base):
    """
    Registra las ceremonias Scrum de un sprint con su duración real.

    Permite analizar cuánto tiempo del sprint se invirtió en ceremonias
    vs trabajo de desarrollo real en Power BI.

    Attributes:
        sprint_id: Sprint al que pertenece la ceremonia.
        tipo: Planning, Daily, Review, Retro, Refinement u Otro.
        fecha: Fecha en que se realizó la ceremonia.
        duracion_minutos: Duración real en minutos.
        participantes: Cantidad de participantes (para cálculo de horas-persona).
        notas: Notas opcionales sobre la ceremonia.
    """
    __tablename__ = "ceremonias_sprint"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sprint_id: Mapped[int] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[TipoCeremonia] = mapped_column(
        Enum(TipoCeremonia, name="tipo_ceremonia"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    duracion_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    participantes: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notas: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    sprint: Mapped["Sprint"] = relationship("Sprint", back_populates="ceremonias")
