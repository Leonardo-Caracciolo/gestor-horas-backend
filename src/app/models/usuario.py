"""
models/usuario.py — Modelo de Usuario del sistema.
"""
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class Usuario(Base):
    """
    Representa un integrante del equipo de tecnología.

    Attributes:
        id: Identificador único.
        nombre: Nombre completo (aparece en el Excel oficial).
        email: Email corporativo, usado también como username.
        username: Nombre de usuario para login.
        password_hash: Hash bcrypt de la contraseña.
        rol_id: FK al rol asignado.
        activo: Si el usuario puede iniciar sesión.
        primer_login: True si aún no cambió la contraseña inicial.
        creado_en: Fecha de creación del usuario.
        ultimo_login: Fecha del último acceso.

    Relationships:
        rol: Rol del usuario con sus permisos.
        registros_horas: Todos los registros de horas del usuario.
        tareas_favoritas: Tasks de ADO marcadas como favoritas.
    """
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    primer_login: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── Relationships ──────────────────────────────────────────
    rol: Mapped["Rol"] = relationship("Rol", back_populates="usuarios")
    registros_horas: Mapped[list["RegistroHora"]] = relationship(
        "RegistroHora", back_populates="usuario"
    )
    tareas_favoritas: Mapped[list["TareaFavorita"]] = relationship(
        "TareaFavorita", back_populates="usuario", cascade="all, delete-orphan"
    )
    aprobaciones_realizadas: Mapped[list["Aprobacion"]] = relationship(
        "Aprobacion", foreign_keys="Aprobacion.aprobador_id", back_populates="aprobador"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="usuario"
    )

    def tiene_permiso(self, clave: str) -> bool:
        """
        Verifica si el usuario tiene un permiso específico.

        Args:
            clave: Clave del permiso a verificar (ej: "ver_horas_equipo").

        Returns:
            bool: True si el rol del usuario tiene el permiso activo.

        Example:
            >>> usuario.tiene_permiso("exportar_excel")
            True
        """
        if not self.rol or not self.rol.activo:
            return False
        return any(
            rp.permiso.clave == clave and rp.permiso.activo
            for rp in self.rol.permisos
        )

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} username={self.username!r}>"
