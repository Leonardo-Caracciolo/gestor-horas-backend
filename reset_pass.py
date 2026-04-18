import sys
sys.path.insert(0, 'src')

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.usuario import Usuario

db = SessionLocal()
usuario = db.query(Usuario).filter(Usuario.username == 'admin').first()
usuario.password_hash = hash_password('Admin123!')
db.commit()
print('Contraseña reseteada a Admin123!')
db.close()