from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Appointment, User
from app.schemas import AppointmentIn, AppointmentOut, AppointmentStatus
from app.security import current_user, allowed_roles
from app.helpers import require_patient, require_doctor

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("", response_model=list[AppointmentOut])
def list_appointments(db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = select(Appointment)
    if user.role == "doctor":
        q = q.where(Appointment.doctor_id == user.id)
    return db.scalars(q.order_by(Appointment.scheduled_at.desc()).limit(200)).all()


@router.post("", response_model=AppointmentOut, status_code=201)
def create_appointment(data: AppointmentIn, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist"))):
    require_patient(db, data.patient_id)
    require_doctor(db, data.doctor_id)
    if data.scheduled_at.tzinfo is None:
        raise HTTPException(422, "Provide a date/time with timezone")
    when = data.scheduled_at.astimezone(timezone.utc)
    clash = db.scalar(select(Appointment).where(Appointment.doctor_id == data.doctor_id,
                        Appointment.scheduled_at == when, Appointment.status == "scheduled"))
    if clash:
        raise HTTPException(409, "Doctor already has an appointment at that time")
    record = Appointment(**{**data.model_dump(), "scheduled_at": when})
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{appointment_id}/status", response_model=AppointmentOut)
def update_status(appointment_id: int, data: AppointmentStatus, db: Session = Depends(get_db), user: User = Depends(allowed_roles("admin", "receptionist", "doctor"))):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    if user.role == "doctor" and appointment.doctor_id != user.id:
        raise HTTPException(403, "Not your appointment")
    if appointment.status != "scheduled" and data.status == "scheduled":
        raise HTTPException(400, "Closed appointments cannot be reopened in this training version")
    appointment.status = data.status
    db.commit()
    db.refresh(appointment)
    return appointment
