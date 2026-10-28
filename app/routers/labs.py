from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import LabOrder, User
from app.schemas import LabIn, LabOut, LabResult
from app.security import allowed_roles
from app.helpers import require_patient, require_doctor, only_own_doctor

router = APIRouter(prefix="/labs", tags=["Lab orders"])


@router.get("", response_model=list[LabOut])
def list_orders(db: Session = Depends(get_db), user: User = Depends(allowed_roles("admin", "doctor", "nurse", "lab"))):
    q = select(LabOrder)
    if user.role == "doctor":
        q = q.where(LabOrder.doctor_id == user.id)
    return db.scalars(q.order_by(LabOrder.id.desc()).limit(200)).all()


@router.post("", response_model=LabOut, status_code=201)
def create_order(data: LabIn, db: Session = Depends(get_db), user: User = Depends(allowed_roles("admin", "doctor"))):
    require_patient(db, data.patient_id)
    require_doctor(db, data.doctor_id)
    only_own_doctor(user, data.doctor_id)
    item = LabOrder(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{order_id}/result", response_model=LabOut)
def record_result(order_id: int, data: LabResult, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "lab"))):
    item = db.get(LabOrder, order_id)
    if not item:
        raise HTTPException(404, "Lab order not found")
    item.result = data.result
    item.status = "completed"
    db.commit()
    db.refresh(item)
    return item
