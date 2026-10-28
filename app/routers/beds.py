from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Bed, User
from app.schemas import BedIn, BedOut, BedAssignment
from app.security import allowed_roles
from app.helpers import require_patient

router = APIRouter(prefix="/beds", tags=["Bed management"])


@router.get("", response_model=list[BedOut])
def list_beds(db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist", "nurse", "doctor"))):
    return db.scalars(select(Bed).order_by(Bed.ward, Bed.bed_number).limit(300)).all()


@router.post("", response_model=BedOut, status_code=201)
def create_bed(data: BedIn, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin"))):
    bed = Bed(**data.model_dump())
    db.add(bed)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bed already exists in this ward")
    db.refresh(bed)
    return bed


@router.patch("/{bed_id}/admit", response_model=BedOut)
def admit(bed_id: int, data: BedAssignment, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist", "nurse"))):
    require_patient(db, data.patient_id)
    bed = db.scalar(select(Bed).where(Bed.id == bed_id).with_for_update())
    if not bed:
        raise HTTPException(404, "Bed not found")
    if bed.patient_id is not None:
        raise HTTPException(409, "Bed already occupied")
    other = db.scalar(select(Bed).where(Bed.patient_id == data.patient_id))
    if other:
        raise HTTPException(409, "Patient already assigned to a bed")
    bed.patient_id = data.patient_id
    db.commit()
    db.refresh(bed)
    return bed


@router.patch("/{bed_id}/discharge", response_model=BedOut)
def discharge(bed_id: int, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist", "nurse"))):
    bed = db.get(Bed, bed_id)
    if not bed:
        raise HTTPException(404, "Bed not found")
    if bed.patient_id is None:
        raise HTTPException(400, "Bed is already empty")
    bed.patient_id = None
    db.commit()
    db.refresh(bed)
    return bed
