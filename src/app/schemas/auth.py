"""
schemas/auth.py — Schemas Pydantic para autenticación.
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Payload del endpoint POST /auth/login."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Respuesta del login con el JWT."""
    access_token: str
    token_type: str = "bearer"
    usuario_id: int
    username: str
    nombre: str
    rol: str
    permisos: list[str]
    primer_login: bool
