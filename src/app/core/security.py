"""
core/security.py — Utilidades de seguridad: hashing de contraseñas y JWT.
"""
import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from app.core.config import get_settings

settings = get_settings()


def _normalize(password: str) -> bytes:
    """Normaliza la contraseña a bytes con SHA-256 (evita límite de 72 bytes de bcrypt)."""
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    """
    Genera el hash bcrypt de una contraseña en texto plano.

    Args:
        password: Contraseña en texto plano.

    Returns:
        str: Hash bcrypt listo para almacenar en BD.

    Example:
        >>> hash = hash_password("MiPassword123!")
        >>> hash.startswith("$2b$")
        True
    """
    return bcrypt.hashpw(_normalize(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash.

    Args:
        plain_password: Contraseña ingresada por el usuario.
        hashed_password: Hash almacenado en BD.

    Returns:
        bool: True si la contraseña es correcta.

    Example:
        >>> h = hash_password("MiPassword123!")
        >>> verify_password("MiPassword123!", h)
        True
        >>> verify_password("Incorrecta", h)
        False
    """
    return bcrypt.checkpw(_normalize(plain_password), hashed_password.encode("utf-8"))


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    extra_claims: dict | None = None,
) -> str:
    """
    Crea un token JWT de acceso.

    Args:
        subject: Identificador del usuario (ej: username o user_id).
        expires_delta: Tiempo de expiración. Si es None, usa el valor
                       configurado en ACCESS_TOKEN_EXPIRE_MINUTES.
        extra_claims: Claims adicionales a incluir en el payload JWT.

    Returns:
        str: Token JWT firmado.

    Example:
        >>> token = create_access_token(subject="juan.perez")
        >>> isinstance(token, str)
        True
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": str(subject), "exp": expire, "iat": datetime.now(timezone.utc)}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decodifica y valida un token JWT.

    Args:
        token: Token JWT a decodificar.

    Returns:
        dict: Payload del token si es válido.
        None: Si el token es inválido o expiró.

    Example:
        >>> token = create_access_token(subject="juan.perez")
        >>> payload = decode_access_token(token)
        >>> payload["sub"]
        'juan.perez'
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
