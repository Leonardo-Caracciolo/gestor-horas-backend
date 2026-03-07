"""
api/v1/deps.py — Dependencias FastAPI reutilizables.

Uso en routers:
    @router.get("/algo")
    def mi_endpoint(
        usuario: Usuario = Depends(get_current_user),
        _: None = Depends(require_permiso("ver_horas_equipo")),
    ):
        ...
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Dependencia que extrae y valida el usuario del JWT.

    Raises:
        401: Si el token es inválido, expiró o el usuario no existe.
        403: Si el usuario está desactivado.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    username: str | None = payload.get("sub")
    if not username:
        raise credentials_error

    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if usuario is None:
        raise credentials_error

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    return usuario


def require_permiso(clave: str):
    """
    Dependencia factory que verifica un permiso específico.

    Args:
        clave: Clave del permiso requerido (ej: "ver_horas_equipo").

    Returns:
        Dependencia FastAPI que lanza 403 si el usuario no tiene el permiso.

    Usage:
        @router.get("/horas")
        def listar_horas(
            _: None = Depends(require_permiso("ver_horas_equipo")),
            usuario: Usuario = Depends(get_current_user),
        ):
            ...
    """
    def _check(usuario: Usuario = Depends(get_current_user)) -> None:
        if not usuario.tiene_permiso(clave):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido: '{clave}'",
            )
    return _check
