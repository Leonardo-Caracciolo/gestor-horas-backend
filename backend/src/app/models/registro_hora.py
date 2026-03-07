"""
models/registro_hora.py — Modelo central de registro de horas.

Es la tabla más importante del sistema. Cada fila representa
las horas que un profesional imputó a una tarea en un día específico.
"""
from sqlalchemy import String, Numeric, Boolean, DateTime, Date, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
from decimal import Decimal
import enum
from app.core.database import Base


class EstadoRegistro(str, enum.Enum):
    """
    Estado del registro de horas en el flujo de aprobación.

    Values:
        BORRADOR: El profesional está cargando, aún no enviado.
        ENVIADO: Enviado para aprobación del Tech Lead / Gerente.
        APROBADO: Aprobado, incluido en el Excel oficial.
        RECHAZADO: Devuelto con comentario para corrección.
    """
    BORRADOR = "Borrador"
    ENVIADO = "Enviado"
    APROBADO = "Aprobado"
    RECHAZADO = "Rechazado"


class RegistroHora(Base):
    """
    Registro de horas trabajadas por un profesional en un día.

    Cada fila equivale a una fila del Excel oficial con el formato:
    Día | Mes | Año | Nombre | Tipo | ID Proyecto | Descripción | Tarea | Horas

    Attributes:
        id: Identificador único.
        usuario_id: FK al profesional que cargó las horas.
        fecha: Día en que se trabajaron las horas.
        proyecto_id: FK al proyecto (determina Tipo e ID Proyecto del Excel).
        ado_task_id: FK a la tarea de ADO (puede ser null para tareas manuales).
        descripcion: Descripción del trabajo realizado (columna Descripción).
        tarea_manual: Nombre de la tarea si no viene de ADO.
        horas: Horas insumidas (hasta 2 decimales, ej: 1.5).
        estado: Borrador / Enviado / Aprobado / Rechazado.
        timer_inicio: Si se usó el timer, momento de inicio.
        es_ceremonia: Si es una ceremonia Scrum (no viene de ADO).

    Relationships:
        usuario: Profesional que cargó las horas.
        proyecto: Proyecto al que se imputan.
        ado_task: Tarea de Azure DevOps.
        aprobacion: Aprobación o rechazo del Tech Lead.
    """
    __tablename__ = "registros_horas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyectos.id", ondelete="RESTRICT"), nullable=False
    )
    ado_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("ado_items.id", ondelete="SET NULL"), nullable=True
    )
    descripcion: Mapped[str] = mapped_column(String(1000), nullable=False)
    tarea_manual: Mapped[str | None] = mapped_column(String(500), nullable=True)
    horas: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    estado: Mapped[EstadoRegistro] = mapped_column(
        Enum(EstadoRegistro, name="estado_registro"),
        default=EstadoRegistro.BORRADOR,
        nullable=False
    )
    timer_inicio: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    es_ceremonia: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────
    usuario: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="registros_horas"
    )
    proyecto: Mapped["Proyecto"] = relationship(
        "Proyecto", back_populates="registros_horas"
    )
    ado_task: Mapped["AdoItem | None"] = relationship(
        "AdoItem", back_populates="registros_horas"
    )
    aprobacion: Mapped["Aprobacion | None"] = relationship(
        "Aprobacion", back_populates="registro", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<RegistroHora id={self.id} usuario_id={self.usuario_id} "
            f"fecha={self.fecha} horas={self.horas} estado={self.estado}>"
        )
