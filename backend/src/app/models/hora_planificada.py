"""
models/hora_planificada.py — Horas planificadas por usuario en un sprint.
"""
from sqlalchemy import Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from app.core.database import Base


class HoraPlanificadaSprint(Base):
    """
    Horas estimadas por usuario y tarea al inicio de cada sprint.
    Permite comparar planificado vs ejecutado en Power BI.
    """
    __tablename__ = "horas_planificadas_sprint"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sprint_id: Mapped[int] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    ado_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("ado_items.id", ondelete="SET NULL"), nullable=True
    )
    horas_estimadas: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    sprint: Mapped["Sprint"] = relationship("Sprint", back_populates="horas_planificadas")
    usuario: Mapped["Usuario"] = relationship("Usuario")
    ado_task: Mapped["AdoItem | None"] = relationship("AdoItem")
