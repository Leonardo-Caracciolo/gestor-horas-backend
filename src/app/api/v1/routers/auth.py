"""
routers/auth.py — Endpoints de autenticación.

Endpoints:
    POST /api/v1/auth/login  → Login con username/password, retorna JWT
    GET  /api/v1/auth/me     → Datos del usuario autenticado
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.usuario import UsuarioResponse
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login de usuario",
    description="Autentica con username y password. Retorna un JWT Bearer.",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Autentica un usuario y retorna un token JWT.

    - Busca el usuario por username.
    - Verifica la contraseña con bcrypt.
    - Actualiza `ultimo_login`.
    - Retorna el token con los permisos del rol.

    Raises:
        401: Si el username no existe o la contraseña es incorrecta.
        403: Si el usuario está desactivado.
    """
    # Buscar usuario
    usuario = db.query(Usuario).filter(
        Usuario.username == payload.username.lower()
    ).first()

    # Mismo mensaje para username inexistente y contraseña incorrecta
    # (evita enumerar usuarios válidos)
    if not usuario or not verify_password(payload.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado. Contactá al administrador.",
        )

    # Actualizar último login
    usuario.ultimo_login = datetime.now(timezone.utc)
    db.commit()

    # Construir lista de permisos del rol
    permisos = [
        rp.permiso.clave
        for rp in usuario.rol.permisos
        if rp.permiso.activo
    ] if usuario.rol else []

    # Generar JWT con claims del usuario
    token = create_access_token(
        subject=usuario.username,
        extra_claims={
            "usuario_id": usuario.id,
            "rol": usuario.rol.nombre if usuario.rol else None,
            "permisos": permisos,
        },
    )

    return TokenResponse(
        access_token=token,
        usuario_id=usuario.id,
        username=usuario.username,
        nombre=usuario.nombre,
        rol=usuario.rol.nombre if usuario.rol else "",
        permisos=permisos,
        primer_login=usuario.primer_login,
    )


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Datos del usuario autenticado",
)
def me(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Retorna los datos del usuario dueño del token JWT actual."""
    return usuario
