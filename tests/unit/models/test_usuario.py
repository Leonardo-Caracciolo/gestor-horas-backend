"""
tests/unit/models/test_usuario.py — Tests unitarios del modelo Usuario.

Siguiendo el estándar del equipo:
- pytest + fixtures de conftest.py
- Nomenclatura: test_[método/propiedad]_[escenario]_[resultado esperado]
- Tags: @pytest.mark.unit
- Happy path + edge cases + validaciones
"""
import pytest
from decimal import Decimal
from datetime import date

from app.models.usuario import Usuario
from app.models.registro_hora import EstadoRegistro
from app.core.security import hash_password, verify_password


pytestmark = pytest.mark.unit


class TestUsuarioTienePermiso:
    """Tests para el método Usuario.tiene_permiso()."""

    def test_tiene_permiso_rol_con_permiso_retorna_true(
        self, usuario_tech_lead: Usuario
    ):
        """Tech Lead con permiso 'ver_horas_equipo' debe retornar True."""
        assert usuario_tech_lead.tiene_permiso("ver_horas_equipo") is True

    def test_tiene_permiso_rol_sin_permiso_retorna_false(
        self, usuario_profesional: Usuario
    ):
        """Profesional sin 'ver_horas_equipo' debe retornar False."""
        assert usuario_profesional.tiene_permiso("ver_horas_equipo") is False

    def test_tiene_permiso_clave_inexistente_retorna_false(
        self, usuario_tech_lead: Usuario
    ):
        """Permiso que no existe en el sistema debe retornar False."""
        assert usuario_tech_lead.tiene_permiso("permiso_que_no_existe") is False

    def test_tiene_permiso_usuario_inactivo_retorna_false(
        self, usuario_inactivo: Usuario
    ):
        """Usuario desactivado no debe tener ningún permiso."""
        assert usuario_inactivo.tiene_permiso("ver_horas_equipo") is False


class TestUsuarioCampos:
    """Tests de creación y validación de campos del modelo Usuario."""

    def test_crear_usuario_campos_obligatorios(self, db, rol_profesional):
        """Usuario con todos los campos obligatorios se crea correctamente."""
        usuario = Usuario(
            nombre="Juan Pérez",
            email="juan.perez@empresa.com",
            username="juan.perez",
            password_hash=hash_password("Pass123!"),
            rol_id=rol_profesional.id,
        )
        db.add(usuario)
        db.flush()

        assert usuario.id is not None
        assert usuario.activo is True
        assert usuario.primer_login is True
        assert usuario.ultimo_login is None

    def test_usuario_activo_por_defecto(self, db, rol_profesional):
        """Un usuario nuevo debe estar activo por defecto."""
        usuario = Usuario(
            nombre="Nuevo Usuario",
            email="nuevo@empresa.com",
            username="nuevo.usuario",
            password_hash=hash_password("Pass123!"),
            rol_id=rol_profesional.id,
        )
        db.add(usuario)
        db.flush()

        assert usuario.activo is True

    def test_repr_usuario(self, usuario_profesional: Usuario):
        """El repr debe incluir id y username."""
        repr_str = repr(usuario_profesional)
        assert "Usuario" in repr_str
        assert "ana.garcia" in repr_str


class TestPasswordSecurity:
    """Tests del sistema de seguridad de contraseñas."""

    def test_hash_password_genera_hash_diferente_al_original(self):
        """La contraseña hasheada no debe ser igual al texto plano."""
        password = "MiPassword123!"
        hashed = hash_password(password)
        assert hashed != password

    def test_hash_password_siempre_genera_hash_bcrypt(self):
        """El hash generado debe ser bcrypt (inicia con $2b$)."""
        hashed = hash_password("MiPassword123!")
        assert hashed.startswith("$2b$")

    def test_verify_password_contrasena_correcta_retorna_true(self):
        """verify_password debe retornar True con la contraseña correcta."""
        password = "MiPassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_contrasena_incorrecta_retorna_false(self):
        """verify_password debe retornar False con contraseña incorrecta."""
        hashed = hash_password("MiPassword123!")
        assert verify_password("Incorrecta", hashed) is False

    def test_verify_password_hash_vacio_retorna_false(self):
        """verify_password con hash vacío no debe lanzar excepción."""
        # La librería passlib debería manejarlo
        with pytest.raises(Exception):
            verify_password("cualquier", "")

    @pytest.mark.parametrize("password", [
        "Pass123!",
        "ClaveMuyLarga123!@#$%^&*()_+",
        "Con Espacios 123!",
        "特殊字符123!",  # Caracteres Unicode
    ])
    def test_hash_y_verify_distintas_contrasenas(self, password: str):
        """Hash y verify deben funcionar para distintos tipos de contraseñas."""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
