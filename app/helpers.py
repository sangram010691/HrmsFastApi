from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Patient, User


def require_patient(db: Session, patient_id: int):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


def require_doctor(db: Session, doctor_id: int):
    doctor = db.get(User, doctor_id)
    if not doctor or not doctor.active or doctor.role != "doctor":
        raise HTTPException(400, "Select an active doctor")
    return doctor


def only_own_doctor(current: User, doctor_id: int):
    if current.role == "doctor" and current.id != doctor_id:
        raise HTTPException(403, "Doctors can only create records under their own account")
