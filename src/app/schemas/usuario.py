"""
schemas/usuario.py — Schemas Pydantic para el ABM de usuarios.
"""
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


# ── Schemas de entrada ────────────────────────────────────────────────────


class UsuarioCreate(BaseModel):
    """Payload para crear un usuario nuevo."""
    nombre: str
    email: EmailStr
    username: str
    password: str
    rol_id: int

    @field_validator("password")
    @classmethod
    def password_minimo(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v

    @field_validator("username")
    @classmethod
    def username_sin_espacios(cls, v: str) -> str:
        if " " in v:
            raise ValueError("El username no puede tener espacios")
        return v.lower()


class UsuarioUpdate(BaseModel):
    """Payload para actualizar datos de un usuario (todos opcionales)."""
    nombre: str | None = None
    email: EmailStr | None = None
    rol_id: int | None = None
    activo: bool | None = None


class CambiarPasswordRequest(BaseModel):
    """Payload para que el usuario cambie su propia contraseña."""
    password_actual: str
    password_nuevo: str

    @field_validator("password_nuevo")
    @classmethod
    def password_minimo(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


# ── Schemas de salida ─────────────────────────────────────────────────────


class RolResumen(BaseModel):
    """Rol simplificado para incluir en la respuesta de usuario."""
    id: int
    nombre: str

    model_config = {"from_attributes": True}


class UsuarioResponse(BaseModel):
    """Representación pública de un usuario (sin password_hash)."""
    id: int
    nombre: str
    email: str
    username: str
    rol_id: int
    rol: RolResumen | None = None
    activo: bool
    primer_login: bool
    creado_en: datetime
    ultimo_login: datetime | None = None

    model_config = {"from_attributes": True}


class UsuarioResumen(BaseModel):
    """Versión compacta para listas."""
    id: int
    nombre: str
    username: str
    email: str
    activo: bool
    rol: RolResumen | None = None

    model_config = {"from_attributes": True}
