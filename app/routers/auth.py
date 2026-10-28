from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut
from app.security import allowed_roles, current_user, create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication and staff"])


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))
    if not user or not user.active or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect login credentials")
    return {"access_token": create_token(user), "token_type": "bearer", "user": UserOut.model_validate(user)}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.get("/staff", response_model=list[UserOut])
def staff(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(User).order_by(User.name)).all()


@router.post("/staff", response_model=UserOut, status_code=201)
def add_staff(data: UserCreate, db: Session = Depends(get_db), _: User = Depends(allowed_roles("admin"))):
    email = data.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already exists")
    user = User(name=data.name, email=email, password_hash=hash_password(data.password), role=data.role, department=data.department)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
