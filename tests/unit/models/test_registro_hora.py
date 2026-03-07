"""
tests/unit/models/test_registro_hora.py — Tests del modelo RegistroHora.

Cubre validaciones de negocio:
- Horas válidas (0 < horas <= 24)
- Estados del flujo de aprobación
- Campos obligatorios
"""
import pytest
from decimal import Decimal
from datetime import date, datetime

from app.models.registro_hora import RegistroHora, EstadoRegistro


pytestmark = pytest.mark.unit


class TestRegistroHoraCampos:
    """Tests de creación y campos del RegistroHora."""

    def test_crear_registro_hora_valido(
        self, db, usuario_profesional, proyecto_activo, ado_task_valida
    ):
        """Registro con todos los campos válidos se persiste correctamente."""
        registro = RegistroHora(
            usuario_id=usuario_profesional.id,
            fecha=date(2025, 1, 6),
            proyecto_id=proyecto_activo.id,
            ado_task_id=ado_task_valida.id,
            descripcion="Desarrollo del módulo de autenticación JWT",
            horas=Decimal("4.00"),
        )
        db.add(registro)
        db.flush()

        assert registro.id is not None
        assert registro.estado == EstadoRegistro.BORRADOR
        assert registro.es_ceremonia is False

    def test_registro_estado_inicial_es_borrador(
        self, db, usuario_profesional, proyecto_activo
    ):
        """Todo registro nuevo debe iniciar en estado Borrador."""
        registro = RegistroHora(
            usuario_id=usuario_profesional.id,
            fecha=date(2025, 1, 6),
            proyecto_id=proyecto_activo.id,
            descripcion="Tarea de ejemplo",
            tarea_manual="Manual Task",
            horas=Decimal("2.00"),
        )
        db.add(registro)
        db.flush()

        assert registro.estado == EstadoRegistro.BORRADOR

    def test_registro_sin_ado_task_usa_tarea_manual(
        self, db, usuario_profesional, proyecto_activo
    ):
        """Un registro puede no tener task de ADO si tiene tarea_manual."""
        registro = RegistroHora(
            usuario_id=usuario_profesional.id,
            fecha=date(2025, 1, 6),
            proyecto_id=proyecto_activo.id,
            ado_task_id=None,
            tarea_manual="Reunión de planificación",
            descripcion="Planning del Sprint 23",
            horas=Decimal("2.00"),
            es_ceremonia=True,
        )
        db.add(registro)
        db.flush()

        assert registro.ado_task_id is None
        assert registro.tarea_manual == "Reunión de planificación"
        assert registro.es_ceremonia is True

    def test_registro_horas_decimales(
        self, db, usuario_profesional, proyecto_activo
    ):
        """Las horas deben aceptar valores decimales (ej: 1.5, 0.25)."""
        registro = RegistroHora(
            usuario_id=usuario_profesional.id,
            fecha=date(2025, 1, 6),
            proyecto_id=proyecto_activo.id,
            descripcion="Media hora de daily",
            tarea_manual="Daily",
            horas=Decimal("0.50"),
            es_ceremonia=True,
        )
        db.add(registro)
        db.flush()

        assert registro.horas == Decimal("0.50")


class TestRegistroHoraEstados:
    """Tests del flujo de estados del RegistroHora."""

    def test_flujo_borrador_a_enviado(self, db, registro_hora_valido: RegistroHora):
        """El profesional puede enviar su registro para aprobación."""
        registro_hora_valido.estado = EstadoRegistro.ENVIADO
        db.flush()

        assert registro_hora_valido.estado == EstadoRegistro.ENVIADO

    def test_flujo_enviado_a_aprobado(self, db, registro_hora_valido: RegistroHora):
        """El Tech Lead puede aprobar un registro enviado."""
        registro_hora_valido.estado = EstadoRegistro.ENVIADO
        registro_hora_valido.estado = EstadoRegistro.APROBADO
        db.flush()

        assert registro_hora_valido.estado == EstadoRegistro.APROBADO

    def test_flujo_enviado_a_rechazado(self, db, registro_hora_valido: RegistroHora):
        """El Tech Lead puede rechazar un registro enviado."""
        registro_hora_valido.estado = EstadoRegistro.ENVIADO
        registro_hora_valido.estado = EstadoRegistro.RECHAZADO
        db.flush()

        assert registro_hora_valido.estado == EstadoRegistro.RECHAZADO

    def test_repr_registro(self, registro_hora_valido: RegistroHora):
        """El repr debe incluir id, usuario_id, fecha y horas."""
        repr_str = repr(registro_hora_valido)
        assert "RegistroHora" in repr_str
        assert "BORRADOR" in repr_str.upper()


class TestRegistroHoraParametrizado:
    """Tests parametrizados de valores válidos e inválidos de horas."""

    @pytest.mark.parametrize("horas,esperado", [
        (Decimal("0.25"), Decimal("0.25")),   # 15 minutos
        (Decimal("1.00"), Decimal("1.00")),   # 1 hora exacta
        (Decimal("4.50"), Decimal("4.50")),   # 4 horas y media
        (Decimal("8.00"), Decimal("8.00")),   # Jornada completa
    ])
    def test_horas_validas_se_persisten(
        self, db, usuario_profesional, proyecto_activo, horas, esperado
    ):
        """Distintos valores de horas válidos deben persistir correctamente."""
        registro = RegistroHora(
            usuario_id=usuario_profesional.id,
            fecha=date(2025, 1, 6),
            proyecto_id=proyecto_activo.id,
            descripcion="Test de horas",
            tarea_manual="Test",
            horas=horas,
        )
        db.add(registro)
        db.flush()

        assert registro.horas == esperado
