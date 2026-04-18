import sys
sys.path.insert(0, 'src')

from app.core.database import SessionLocal
from app.models.proyecto import Proyecto, TipoProyecto

db = SessionLocal()

proyectos = [
    Proyecto(
        nombre="Oficina",
        tipo=TipoProyecto.OFICINA,
        id_proyecto_excel="OFICINA",
        descripcion="Horas internas: reuniones, capacitaciones, admin",
    ),
    Proyecto(
        nombre="BPS Tax Tech Agile",
        tipo=TipoProyecto.PROYECTO,
        id_proyecto_excel="BPS-TAX",
        ado_project_name="BPS_Tax_Tech_Agile",
        descripcion="Proyecto principal del equipo",
    ),
]

for p in proyectos:
    db.add(p)

db.commit()
print("Proyectos creados:")
for p in proyectos:
    print(f"  [{p.id}] {p.nombre} ({p.tipo})")

db.close()