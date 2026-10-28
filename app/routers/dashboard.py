from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Patient, Appointment, Bill, InventoryItem, Bed, LabOrder
from app.security import current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db), _: User = Depends(current_user)):
    def count(table):
        return db.scalar(select(func.count()).select_from(table)) or 0
    outstanding = db.scalar(select(func.coalesce(func.sum(Bill.amount - Bill.paid_amount), 0))) or Decimal("0")
    return {
        "patients": count(Patient),
        "staff": count(User),
        "appointments": count(Appointment),
        "pending_labs": db.scalar(select(func.count()).select_from(LabOrder).where(LabOrder.status == "ordered")) or 0,
        "occupied_beds": db.scalar(select(func.count()).select_from(Bed).where(Bed.patient_id.is_not(None))) or 0,
        "low_stock": db.scalar(select(func.count()).select_from(InventoryItem).where(InventoryItem.quantity <= InventoryItem.reorder_level)) or 0,
        # Billing aggregates are visible only to admin/reception roles.
        "outstanding_balance": str(outstanding) if _.role in ("admin", "receptionist") else None,
    }
