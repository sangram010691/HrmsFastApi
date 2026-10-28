from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import InventoryItem, User
from app.schemas import InventoryIn, InventoryOut, StockChange
from app.security import current_user, allowed_roles

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=list[InventoryOut])
def list_items(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(InventoryItem).order_by(InventoryItem.name).limit(300)).all()


@router.post("", response_model=InventoryOut, status_code=201)
def add_item(data: InventoryIn, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin"))):
    item = InventoryItem(**data.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "SKU already exists")
    db.refresh(item)
    return item


@router.patch("/{item_id}/stock", response_model=InventoryOut)
def update_stock(item_id: int, data: StockChange, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin", "nurse"))):
    item = db.scalar(select(InventoryItem).where(InventoryItem.id == item_id).with_for_update())
    if not item:
        raise HTTPException(404, "Item not found")
    if item.quantity + data.change < 0:
        raise HTTPException(400, "Stock cannot become negative")
    item.quantity += data.change
    db.commit()
    db.refresh(item)
    return item
