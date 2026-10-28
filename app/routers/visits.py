from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Visit
from app.schemas import VisitIn, VisitOut
from app.security import allowed_roles
from app.helpers import require_patient, require_doctor, only_own_doctor

router = APIRouter(prefix="/visits", tags=["Clinical visits"])


@router.get("", response_model=list[VisitOut])
def list_visits(db: Session = Depends(get_db), user: User = Depends(allowed_roles("admin", "doctor", "nurse"))):
    q = select(Visit)
    if user.role == "doctor":
        q = q.where(Visit.doctor_id == user.id)
    return db.scalars(q.order_by(Visit.id.desc()).limit(200)).all()


@router.post("", response_model=VisitOut, status_code=201)
def create_visit(data: VisitIn, db: Session = Depends(get_db), user: User = Depends(allowed_roles("admin", "doctor"))):
    require_patient(db, data.patient_id)
    require_doctor(db, data.doctor_id)
    only_own_doctor(user, data.doctor_id)
    visit = Visit(**data.model_dump())
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit
