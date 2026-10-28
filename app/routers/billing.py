from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Bill, Payment, User
from app.schemas import BillIn, BillOut, PaymentIn
from app.security import allowed_roles
from app.helpers import require_patient

router = APIRouter(prefix="/bills", tags=["Billing"])


@router.get("", response_model=list[BillOut])
def list_bills(db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist"))):
    return db.scalars(select(Bill).order_by(Bill.id.desc()).limit(200)).all()


@router.post("", response_model=BillOut, status_code=201)
def create_bill(data: BillIn, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist"))):
    require_patient(db, data.patient_id)
    bill = Bill(**data.model_dump(), paid_amount=Decimal("0.00"))
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@router.post("/{bill_id}/payments", response_model=BillOut)
def add_payment(bill_id: int, data: PaymentIn, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist"))):
    # Row lock prevents two concurrent payments from exceeding the amount.
    bill = db.scalar(select(Bill).where(Bill.id == bill_id).with_for_update())
    if not bill:
        raise HTTPException(404, "Bill not found")
    if (bill.paid_amount or Decimal("0.00")) + data.amount > bill.amount:
        raise HTTPException(400, "Payment exceeds balance due")
    db.add(Payment(bill_id=bill.id, **data.model_dump()))
    bill.paid_amount = (bill.paid_amount or Decimal("0.00")) + data.amount
    db.commit()
    db.refresh(bill)
    return bill


@router.get("/{bill_id}/payments")
def payments(bill_id: int, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "receptionist"))):
    if not db.get(Bill, bill_id):
        raise HTTPException(404, "Bill not found")
    items = db.scalars(select(Payment).where(Payment.bill_id == bill_id).order_by(Payment.id)).all()
    return [{"id": p.id, "amount": p.amount, "method": p.method, "created_at": p.created_at} for p in items]
