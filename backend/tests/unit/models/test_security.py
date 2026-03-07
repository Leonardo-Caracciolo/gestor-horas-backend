"""
tests/unit/models/test_security.py — Tests unitarios del módulo de seguridad JWT.

Cubre:
- Creación y decodificación de tokens
- Expiración de tokens
- Tokens inválidos
"""
import pytest
import time
from datetime import timedelta

from app.core.security import create_access_token, decode_access_token


pytestmark = pytest.mark.unit


class TestCreateAccessToken:
    """Tests de creación de tokens JWT."""

    def test_create_token_retorna_string(self):
        """create_access_token debe retornar una cadena no vacía."""
        token = create_access_token(subject="juan.perez")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_contiene_subject(self):
        """El payload del token debe contener el subject correcto."""
        token = create_access_token(subject="ana.garcia")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "ana.garcia"

    def test_create_token_con_claims_extra(self):
        """Los claims adicionales deben incluirse en el payload."""
        token = create_access_token(
            subject="carlos",
            extra_claims={"rol": "Tech Lead", "user_id": 42}
        )
        payload = decode_access_token(token)
        assert payload["rol"] == "Tech Lead"
        assert payload["user_id"] == 42

    def test_create_token_con_expiracion_personalizada(self):
        """Un token con expiración personalizada debe decodificarse correctamente."""
        token = create_access_token(
            subject="test", expires_delta=timedelta(hours=1)
        )
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "test"


class TestDecodeAccessToken:
    """Tests de decodificación y validación de tokens."""

    def test_decode_token_valido(self):
        """Un token válido debe decodificarse sin errores."""
        token = create_access_token(subject="usuario_test")
        payload = decode_access_token(token)
        assert payload is not None

    def test_decode_token_invalido_retorna_none(self):
        """Un token malformado debe retornar None sin lanzar excepción."""
        resultado = decode_access_token("esto.no.es.un.jwt")
        assert resultado is None

    def test_decode_token_vacio_retorna_none(self):
        """Un token vacío debe retornar None."""
        resultado = decode_access_token("")
        assert resultado is None

    def test_decode_token_expirado_retorna_none(self):
        """Un token ya expirado debe retornar None."""
        token = create_access_token(
            subject="usuario_test",
            expires_delta=timedelta(seconds=-1)  # Expirado hace 1 segundo
        )
        resultado = decode_access_token(token)
        assert resultado is None

    def test_decode_token_firmado_con_otra_clave_retorna_none(self):
        """Token firmado con una clave diferente debe fallar la validación."""
        from jose import jwt
        import datetime

        token_falso = jwt.encode(
            {"sub": "hacker", "exp": datetime.datetime.utcnow() + timedelta(hours=1)},
            "clave-secreta-incorrecta",
            algorithm="HS256"
        )
        resultado = decode_access_token(token_falso)
        assert resultado is None
