"""initial

Revision ID: 4e4a9b27f305
Revises: 
Create Date: 2026-03-07 13:40:50.615583

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '4e4a9b27f305'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('feriados',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('fecha', sa.Date(), nullable=False),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('aplica_a_todos', sa.Boolean(), nullable=False),
    sa.Column('anio', sa.Integer(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('fecha')
    )
    op.create_table('permisos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('clave', sa.String(length=100), nullable=False),
    sa.Column('descripcion', sa.String(length=500), nullable=True),
    sa.Column('modulo', sa.String(length=100), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('clave')
    )
    op.create_table('proyectos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('tipo', sa.Enum('PROYECTO', 'OFICINA', name='tipo_proyecto'), nullable=False),
    sa.Column('id_proyecto_excel', sa.String(length=100), nullable=False),
    sa.Column('ado_project_name', sa.String(length=200), nullable=True),
    sa.Column('descripcion', sa.String(length=500), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id_proyecto_excel')
    )
    op.create_table('roles',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('descripcion', sa.String(length=500), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('es_sistema', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('rol_permisos',
    sa.Column('rol_id', sa.Integer(), nullable=False),
    sa.Column('permiso_id', sa.Integer(), nullable=False),
    sa.Column('asignado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['permiso_id'], ['permisos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['rol_id'], ['roles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('rol_id', 'permiso_id')
    )
    op.create_table('sprints',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('fecha_inicio', sa.Date(), nullable=False),
    sa.Column('fecha_fin', sa.Date(), nullable=False),
    sa.Column('estado', sa.Enum('PLANIFICADO', 'ACTIVO', 'CERRADO', name='estado_sprint'), nullable=False),
    sa.Column('proyecto_id', sa.Integer(), nullable=False),
    sa.Column('ado_sprint_id', sa.String(length=200), nullable=True),
    sa.Column('excel_generado', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('usuarios',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('rol_id', sa.Integer(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('primer_login', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('ultimo_login', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['rol_id'], ['roles.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('ado_items',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('ado_id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.Enum('EPIC', 'FEATURE', 'USER_STORY', 'TASK', name='tipo_ado_item'), nullable=False),
    sa.Column('titulo', sa.String(length=500), nullable=False),
    sa.Column('asignado_a', sa.String(length=200), nullable=True),
    sa.Column('estado', sa.String(length=100), nullable=True),
    sa.Column('proyecto_id', sa.Integer(), nullable=False),
    sa.Column('sprint_id', sa.Integer(), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('ultima_sync', sa.DateTime(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['ado_items.id']),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id']),
    sa.ForeignKeyConstraint(['sprint_id'], ['sprints.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ado_id')
    )
    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=True),
    sa.Column('accion', sa.String(length=50), nullable=False),
    sa.Column('tabla', sa.String(length=100), nullable=False),
    sa.Column('registro_id', sa.Integer(), nullable=True),
    sa.Column('valor_anterior', sa.String(length=4000), nullable=True),
    sa.Column('valor_nuevo', sa.String(length=4000), nullable=True),
    sa.Column('ip_address', sa.String(length=50), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ceremonias_sprint',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('sprint_id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.Enum('PLANNING', 'DAILY', 'REVIEW', 'RETRO', 'REFINEMENT', 'OTRO', name='tipo_ceremonia'), nullable=False),
    sa.Column('fecha', sa.Date(), nullable=False),
    sa.Column('duracion_minutos', sa.Integer(), nullable=False),
    sa.Column('participantes', sa.Integer(), nullable=False),
    sa.Column('notas', sa.String(length=500), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['sprint_id'], ['sprints.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('semanas',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('fecha_inicio', sa.Date(), nullable=False),
    sa.Column('fecha_fin', sa.Date(), nullable=False),
    sa.Column('estado', sa.Enum('ABIERTA', 'CERRADA', name='estado_semana'), nullable=False),
    sa.Column('sprint_id', sa.Integer(), nullable=True),
    sa.Column('excel_generado', sa.Boolean(), nullable=False),
    sa.Column('cerrado_en', sa.DateTime(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['sprint_id'], ['sprints.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('horas_planificadas_sprint',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('sprint_id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('ado_task_id', sa.Integer(), nullable=True),
    sa.Column('horas_estimadas', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['ado_task_id'], ['ado_items.id']),
    sa.ForeignKeyConstraint(['sprint_id'], ['sprints.id']),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('registros_horas',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('fecha', sa.Date(), nullable=False),
    sa.Column('proyecto_id', sa.Integer(), nullable=False),
    sa.Column('ado_task_id', sa.Integer(), nullable=True),
    sa.Column('descripcion', sa.String(length=1000), nullable=False),
    sa.Column('tarea_manual', sa.String(length=500), nullable=True),
    sa.Column('horas', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('estado', sa.Enum('BORRADOR', 'ENVIADO', 'APROBADO', 'RECHAZADO', name='estado_registro'), nullable=False),
    sa.Column('timer_inicio', sa.DateTime(), nullable=True),
    sa.Column('es_ceremonia', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['ado_task_id'], ['ado_items.id']),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id']),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tareas_favoritas',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('ado_item_id', sa.Integer(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['ado_item_id'], ['ado_items.id']),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('aprobaciones',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('registro_id', sa.Integer(), nullable=False),
    sa.Column('aprobador_id', sa.Integer(), nullable=False),
    sa.Column('estado', sa.Enum('APROBADO', 'RECHAZADO', name='estado_aprobacion'), nullable=False),
    sa.Column('comentario', sa.String(length=1000), nullable=True),
    sa.Column('resuelto_en', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['aprobador_id'], ['usuarios.id']),
    sa.ForeignKeyConstraint(['registro_id'], ['registros_horas.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('registro_id')
    )


def downgrade() -> None:
    op.drop_table('aprobaciones')
    op.drop_table('tareas_favoritas')
    op.drop_table('registros_horas')
    op.drop_table('horas_planificadas_sprint')
    op.drop_table('semanas')
    op.drop_table('ceremonias_sprint')
    op.drop_table('audit_log')
    op.drop_table('ado_items')
    op.drop_table('usuarios')
    op.drop_table('sprints')
    op.drop_table('rol_permisos')
    op.drop_table('roles')
    op.drop_table('proyectos')
    op.drop_table('permisos')
    op.drop_table('feriados')