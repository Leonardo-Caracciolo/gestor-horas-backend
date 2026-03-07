"""
models/rol.py — Modelo de Rol para el sistema RBAC dinámico.
"""
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class Rol(Base):
    """
    Representa un rol en el sistema de control de acceso RBAC.

    Los roles agrupan permisos y se asignan a usuarios.
    Son completamente dinámicos: se pueden crear/modificar/eliminar
    desde el panel de administración sin tocar código.

    Attributes:
        id: Identificador único del rol.
        nombre: Nombre del rol (ej: "Admin", "Tech Lead", "Profesional").
        descripcion: Descripción de las responsabilidades del rol.
        activo: Si el rol está habilitado en el sistema.
        es_sistema: Roles protegidos que no pueden eliminarse (Admin).
        creado_en: Fecha y hora de creación.

    Relationships:
        permisos: Lista de permisos asociados via RolPermiso.
        usuarios: Lista de usuarios con este rol.
    """
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    es_sistema: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────
    permisos: Mapped[list["RolPermiso"]] = relationship(
        "RolPermiso", back_populates="rol", cascade="all, delete-orphan"
    )
    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario", back_populates="rol"
    )

    def __repr__(self) -> str:
        return f"<Rol id={self.id} nombre={self.nombre!r}>"
