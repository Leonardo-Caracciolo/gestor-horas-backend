"""
models/aprobacion.py — Aprobación o rechazo de un registro de horas.
"""
from sqlalchemy import String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from app.core.database import Base


class EstadoAprobacion(str, enum.Enum):
    APROBADO = "Aprobado"
    RECHAZADO = "Rechazado"


class Aprobacion(Base):
    """
    Registra la decisión del Tech Lead o Gerente sobre un registro de horas.

    Attributes:
        registro_id: FK al registro de horas (1:1).
        aprobador_id: FK al usuario que aprobó/rechazó.
        estado: Aprobado o Rechazado.
        comentario: Motivo del rechazo (obligatorio si se rechaza).
        resuelto_en: Fecha y hora de la decisión.
    """
    __tablename__ = "aprobaciones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    registro_id: Mapped[int] = mapped_column(
        ForeignKey("registros_horas.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    aprobador_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    estado: Mapped[EstadoAprobacion] = mapped_column(
        Enum(EstadoAprobacion, name="estado_aprobacion"), nullable=False
    )
    comentario: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    resuelto_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    registro: Mapped["RegistroHora"] = relationship(
        "RegistroHora", back_populates="aprobacion"
    )
    aprobador: Mapped["Usuario"] = relationship(
        "Usuario",
        foreign_keys=[aprobador_id],
        back_populates="aprobaciones_realizadas"
    )


# ─────────────────────────────────────────────────────────────────────────────


class TareaFavorita(Base):
    """
    Tasks de ADO marcadas como favoritas por un usuario.

    Al cargar horas, las tareas favoritas aparecen primero
    sin necesidad de navegar la jerarquía Épica→Feature→US→Task.
    """
    __tablename__ = "tareas_favoritas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    ado_item_id: Mapped[int] = mapped_column(
        ForeignKey("ado_items.id", ondelete="CASCADE"), nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="tareas_favoritas")
    ado_item: Mapped["AdoItem"] = relationship("AdoItem")


# ─────────────────────────────────────────────────────────────────────────────


class AuditLog(Base):
    """
    Registro de auditoría de todas las acciones relevantes del sistema.

    Registra quién hizo qué y cuándo, con el valor anterior y nuevo.
    Útil para resolver disputas sobre horas registradas.

    Attributes:
        usuario_id: Quién realizó la acción.
        accion: Tipo de acción (ej: "CREATE", "UPDATE", "DELETE", "APPROVE").
        tabla: Tabla afectada (ej: "registros_horas").
        registro_id: ID del registro afectado.
        valor_anterior: JSON con el valor antes del cambio.
        valor_nuevo: JSON con el valor después del cambio.
        ip_address: IP desde donde se realizó la acción.
        creado_en: Timestamp de la acción.
    """
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    tabla: Mapped[str] = mapped_column(String(100), nullable=False)
    registro_id: Mapped[int | None] = mapped_column(nullable=True)
    valor_anterior: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    valor_nuevo: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    usuario: Mapped["Usuario | None"] = relationship(
        "Usuario", back_populates="audit_logs"
    )
