import sys
sys.path.insert(0, 'src')

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.rol import Rol
from app.models.permiso import Permiso, RolPermiso
from app.models.usuario import Usuario

db = SessionLocal()

permisos = [
    Permiso(clave="admin_usuarios",   descripcion="ABM usuarios",     modulo="usuarios"),
    Permiso(clave="admin_proyectos",  descripcion="ABM proyectos",    modulo="proyectos"),
    Permiso(clave="ver_horas_equipo", descripcion="Ver horas equipo", modulo="horas"),
    Permiso(clave="aprobar_horas",    descripcion="Aprobar horas",    modulo="horas"),
    Permiso(clave="cerrar_sprint",    descripcion="Cerrar sprint",    modulo="sprints"),
    Permiso(clave="exportar_excel",   descripcion="Exportar Excel",   modulo="export"),
    Permiso(clave="admin_feriados",   descripcion="ABM feriados",     modulo="feriados"),
]
for p in permisos:
    db.add(p)
db.flush()

rol = Rol(nombre="Admin", descripcion="Administrador", es_sistema=True)
db.add(rol)
db.flush()

for p in permisos:
    db.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))

admin = Usuario(
    nombre="Administrador",
    email="admin@empresa.com",
    username="admin",
    password_hash=hash_password("Admin123!"),
    rol_id=rol.id,
    primer_login=False,
)
db.add(admin)
db.commit()
print("Listo! Usuario admin creado.")
db.close()