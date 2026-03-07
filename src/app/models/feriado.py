"""
models/feriado.py — Feriados nacionales de México.
"""
from sqlalchemy import String, Boolean, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from app.core.database import Base


class Feriado(Base):
    """
    Feriados nacionales de México cargados manualmente por el Admin.

    La app no pedirá horas en estos días. Se pueden definir feriados
    por equipo si algún integrante trabaja en modalidad diferente.

    Attributes:
        id: Identificador.
        fecha: Fecha del feriado.
        nombre: Descripción del feriado (ej: "Día de la Revolución").
        aplica_a_todos: Si aplica a todo el equipo o solo a algunos.
        anio: Año del feriado (para filtrar por año fácilmente).
    """
    __tablename__ = "feriados"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    aplica_a_todos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    anio: Mapped[int] = mapped_column(nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
