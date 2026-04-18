"""
limpiar_horas.py — Borra registros de horas (con confirmación interactiva).

Uso desde la raíz del proyecto:
    python limpiar_horas.py              # borra TODO con confirmación
    python limpiar_horas.py --usuario 1  # borra solo del usuario id=1
    python limpiar_horas.py --yes        # sin confirmación (ojo)
    python limpiar_horas.py --dry-run    # solo cuenta, no borra
"""
import argparse
import sys
from pathlib import Path

# Permitir correr desde la raíz del repo
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.core.database import SessionLocal
from app.models.registro_hora import RegistroHora
from app.models.aprobacion import Aprobacion


def main():
    parser = argparse.ArgumentParser(description="Limpiar registros de horas")
    parser.add_argument("--usuario", type=int, help="Solo registros de este usuario_id")
    parser.add_argument("--yes", action="store_true", help="No pedir confirmación")
    parser.add_argument("--dry-run", action="store_true", help="Solo contar, no borrar")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # Contar
        q_reg = db.query(RegistroHora)
        if args.usuario:
            q_reg = q_reg.filter(RegistroHora.usuario_id == args.usuario)

        total_reg = q_reg.count()

        # Aprobaciones asociadas
        registro_ids = [r.id for r in q_reg.all()]
        if registro_ids:
            total_aprob = db.query(Aprobacion).filter(
                Aprobacion.registro_id.in_(registro_ids)
            ).count()
        else:
            total_aprob = 0

        scope = f"del usuario {args.usuario}" if args.usuario else "TODOS los usuarios"
        print(f"\nA borrar ({scope}):")
        print(f"  - {total_reg} registros de horas")
        print(f"  - {total_aprob} aprobaciones asociadas")

        if total_reg == 0:
            print("\nNo hay nada que borrar.")
            return

        if args.dry_run:
            print("\n[dry-run] No se borró nada.")
            return

        if not args.yes:
            resp = input("\n¿Confirmás? (escribí 'borrar' para continuar): ").strip()
            if resp.lower() != "borrar":
                print("Cancelado.")
                return

        # Borrar (orden: aprobaciones primero por la FK)
        if registro_ids:
            db.query(Aprobacion).filter(
                Aprobacion.registro_id.in_(registro_ids)
            ).delete(synchronize_session=False)

        if args.usuario:
            db.query(RegistroHora).filter(
                RegistroHora.usuario_id == args.usuario
            ).delete(synchronize_session=False)
        else:
            db.query(RegistroHora).delete(synchronize_session=False)

        db.commit()
        print(f"\n✓ Borrados {total_reg} registros y {total_aprob} aprobaciones.")

    finally:
        db.close()


if __name__ == "__main__":
    main()