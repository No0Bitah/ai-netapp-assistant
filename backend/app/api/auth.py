from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import UserCreate, UserOut
from app.models.models import User
from app.utility.security import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # 1) check if email exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # 2) hash password
    pwd_hash = hash_password(payload.password)

    # 3) create user
    user = User(email=payload.email, pwd_hash=pwd_hash, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)

    # 4) return safe response (no password)
    return user
