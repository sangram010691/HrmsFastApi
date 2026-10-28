from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Patient, User
from app.schemas import PatientIn, PatientOut
from app.security import current_user, allowed_roles
from app.helpers import require_patient

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=list[PatientOut])
def list_patients(search: str = Query("", max_length=100), db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = select(Patient)
    if search:
        query = query.where(or_(Patient.full_name.ilike(f"%{search}%"), Patient.phone.ilike(f"%{search}%")))
    return db.scalars(query.order_by(Patient.id.desc()).limit(200)).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    return require_patient(db, patient_id)


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(data: PatientIn, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist", "nurse"))):
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, data: PatientIn, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist", "nurse"))):
    patient = require_patient(db, patient_id)
    for name, value in data.model_dump().items():
        setattr(patient, name, value)
    db.commit()
    db.refresh(patient)
    return patient
