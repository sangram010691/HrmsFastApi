"""Create fake practice users and examples. Run: python -m app.seed"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from app.database import Base, engine, SessionLocal
from app.models import User, Patient, Appointment, InventoryItem, Bed
from app.security import hash_password


def seed():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(User.id).limit(1)):
            print("Users already exist. Seed skipped to avoid duplicates.")
            return
        accounts = [
            ("Admin", "admin@demo.test", "admin", "Administration"),
            ("Dr Asha", "doctor@demo.test", "doctor", "General Medicine"),
            ("Reception", "reception@demo.test", "receptionist", "Front Desk"),
            ("Nurse Raj", "nurse@demo.test", "nurse", "Ward A"),
            ("Lab Tech", "lab@demo.test", "lab", "Pathology"),
        ]
        for name, email, role, department in accounts:
            db.add(User(name=name, email=email, role=role, department=department,
                        password_hash=hash_password("Practice123!")))
        db.flush()
        doctor = db.scalar(select(User).where(User.role == "doctor"))
        p1 = Patient(full_name="Demo Patient One", date_of_birth=date(1994, 5, 13), sex="Female", phone="0000000000", address="Fictional training address", blood_group="O+")
        p2 = Patient(full_name="Demo Patient Two", date_of_birth=date(1987, 11, 2), sex="Male", phone="0000000001", address="Fictional training address", blood_group="B+")
        db.add_all([p1, p2])
        db.flush()
        db.add(Appointment(patient_id=p1.id, doctor_id=doctor.id, scheduled_at=datetime.now(timezone.utc) + timedelta(days=1), reason="Sample checkup"))
        db.add_all([
            InventoryItem(name="Disposable Gloves (box)", sku="DEMO-GLV", quantity=30, reorder_level=10, unit_price=Decimal("245.00")),
            InventoryItem(name="Masks (pack)", sku="DEMO-MSK", quantity=4, reorder_level=10, unit_price=Decimal("110.00")),
            Bed(ward="General A", bed_number="A-01"), Bed(ward="General A", bed_number="A-02"),
        ])
        db.commit()
        print("Created 5 fake demo accounts, 2 fake patients, 1 appointment, 2 stock items, 2 beds.")
        print("Demo password for each account: Practice123!  (FOR LOCAL PRACTICE ONLY)")


if __name__ == "__main__":
    seed()
