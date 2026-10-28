"""JWT sign/verify and Argon2 password hashing."""
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.settings import settings

hash_tool = PasswordHash.recommended()
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(raw: str) -> str:
    return hash_tool.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return hash_tool.verify(raw, hashed)


def create_token(user: User) -> str:
    payload = {"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.token_expire_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(data["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise error
    user = db.get(User, user_id)
    if not user or not user.active:
        raise error
    return user


def allowed_roles(*roles):
    """Use this on each protected route: Depends(allowed_roles('admin', ...))."""
    def checker(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "You do not have permission for this action")
        return user
    return checker
