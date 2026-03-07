"""
models/permiso.py — Modelos de Permiso y tabla de unión Rol-Permiso.

El sistema RBAC es completamente dinámico: los permisos se definen
en BD y se asignan/revogan a roles desde el panel de Admin.
"""
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class Permiso(Base):
    """
    Representa un permiso granular del sistema.

    Cada permiso controla una acción específica dentro de la app.

    Attributes:
        id: Identificador único.
        clave: Clave única en snake_case (ej: "ver_horas_equipo").
        descripcion: Descripción legible del permiso.
        modulo: Módulo al que pertenece (ej: "horas", "usuarios", "reportes").
        activo: Si el permiso está habilitado.

    Example:
        Permisos del sistema:
        - "ver_horas_equipo"     → Ver horas de todos los integrantes
        - "ver_horas_propias"    → Solo ver las propias horas
        - "aprobar_horas"        → Aprobar/rechazar horas del equipo
        - "exportar_excel"       → Generar y descargar el Excel oficial
        - "admin_usuarios"       → ABM de usuarios y roles
        - "admin_proyectos"      → ABM de proyectos
        - "admin_feriados"       → ABM de feriados
        - "cerrar_semana"        → Cerrar período semanal
        - "cerrar_sprint"        → Cerrar sprint
        - "ver_dashboard"        → Acceso al dashboard de Power BI
    """
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clave: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=True)
    modulo: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────
    roles: Mapped[list["RolPermiso"]] = relationship(
        "RolPermiso", back_populates="permiso", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Permiso clave={self.clave!r} modulo={self.modulo!r}>"


class RolPermiso(Base):
    """
    Tabla de unión entre Rol y Permiso.

    Permite asignar/revocar permisos a roles de forma dinámica.

    Attributes:
        rol_id: FK al rol.
        permiso_id: FK al permiso.
        asignado_en: Fecha de asignación del permiso al rol.
    """
    __tablename__ = "rol_permisos"

    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permiso_id: Mapped[int] = mapped_column(
        ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True
    )
    asignado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────
    rol: Mapped["Rol"] = relationship("Rol", back_populates="permisos")
    permiso: Mapped["Permiso"] = relationship("Permiso", back_populates="roles")

    def __repr__(self) -> str:
        return f"<RolPermiso rol_id={self.rol_id} permiso_id={self.permiso_id}>"
