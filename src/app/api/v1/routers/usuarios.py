"""
routers/usuarios.py — CRUD de usuarios.

Endpoints:
    GET    /api/v1/usuarios/              → Lista todos (requiere: admin_usuarios)
    POST   /api/v1/usuarios/              → Crear usuario (requiere: admin_usuarios)
    GET    /api/v1/usuarios/{id}          → Obtener por ID (requiere: admin_usuarios)
    PUT    /api/v1/usuarios/{id}          → Actualizar (requiere: admin_usuarios)
    DELETE /api/v1/usuarios/{id}          → Desactivar (requiere: admin_usuarios)
    POST   /api/v1/usuarios/me/password   → Cambiar propia contraseña (cualquier usuario)
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioResumen,
    CambiarPasswordRequest,
)
from app.api.v1.deps import get_current_user, require_permiso

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, usuario_id: int) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Usuario {usuario_id} no encontrado")
    return usuario


def _validar_rol(db: Session, rol_id: int) -> Rol:
    rol = db.query(Rol).filter(Rol.id == rol_id, Rol.activo == True).first()
    if not rol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Rol {rol_id} no existe o está inactivo")
    return rol


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[UsuarioResumen],
    summary="Listar todos los usuarios",
    dependencies=[Depends(require_permiso("admin_usuarios"))],
)
def listar_usuarios(
    solo_activos: bool = True,
    db: Session = Depends(get_db),
) -> list[Usuario]:
    """
    Lista todos los usuarios del sistema.

    Args:
        solo_activos: Si True (default), filtra solo usuarios activos.
    """
    query = db.query(Usuario)
    if solo_activos:
        query = query.filter(Usuario.activo == True)
    return query.order_by(Usuario.nombre).all()


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    dependencies=[Depends(require_permiso("admin_usuarios"))],
)
def crear_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Crea un usuario nuevo en el sistema.

    - Verifica que el email y username sean únicos.
    - Hashea la contraseña con bcrypt.
    - `primer_login` queda en True para forzar cambio de contraseña.

    Raises:
        400: Si el email o username ya están en uso.
        400: Si el rol_id no existe o está inactivo.
    """
    # Verificar unicidad
    if db.query(Usuario).filter(Usuario.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"El email '{payload.email}' ya está en uso")
    if db.query(Usuario).filter(Usuario.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"El username '{payload.username}' ya está en uso")

    _validar_rol(db, payload.rol_id)

    usuario = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        rol_id=payload.rol_id,
        primer_login=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Obtener usuario por ID",
    dependencies=[Depends(require_permiso("admin_usuarios"))],
)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
) -> Usuario:
    """Retorna los datos de un usuario por su ID."""
    return _get_or_404(db, usuario_id)


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Actualizar usuario",
    dependencies=[Depends(require_permiso("admin_usuarios"))],
)
def actualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Actualiza nombre, email, rol o estado activo de un usuario.

    Solo se modifican los campos que vengan en el payload (PATCH semántico).

    Raises:
        400: Si el nuevo email ya está en uso por otro usuario.
        400: Si el rol_id no existe o está inactivo.
        404: Si el usuario no existe.
    """
    usuario = _get_or_404(db, usuario_id)

    if payload.nombre is not None:
        usuario.nombre = payload.nombre

    if payload.email is not None:
        existente = db.query(Usuario).filter(
            Usuario.email == payload.email,
            Usuario.id != usuario_id,
        ).first()
        if existente:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"El email '{payload.email}' ya está en uso")
        usuario.email = payload.email

    if payload.rol_id is not None:
        _validar_rol(db, payload.rol_id)
        usuario.rol_id = payload.rol_id

    if payload.activo is not None:
        usuario.activo = payload.activo

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar usuario",
    dependencies=[Depends(require_permiso("admin_usuarios"))],
)
def desactivar_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Desactiva un usuario (soft delete — no se borra de la BD).

    Raises:
        400: Si el usuario intenta desactivarse a sí mismo.
        404: Si el usuario no existe.
    """
    usuario = _get_or_404(db, usuario_id)

    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No podés desactivarte a vos mismo",
        )

    usuario.activo = False
    db.commit()


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cambiar contraseña propia",
)
def cambiar_password(
    payload: CambiarPasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Permite al usuario autenticado cambiar su propia contraseña.

    - Verifica que la contraseña actual sea correcta.
    - Actualiza `primer_login` a False al completar el cambio.

    Raises:
        400: Si la contraseña actual es incorrecta.
    """
    if not verify_password(payload.password_actual, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )

    current_user.password_hash = hash_password(payload.password_nuevo)
    current_user.primer_login = False
    db.commit()
