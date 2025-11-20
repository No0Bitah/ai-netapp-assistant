from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import UserCreate, UserOut, LoginPayload, TokenResponse
from app.models.models import User
from app.utility.security import hash_password, verify_password, create_token
from app.api import require_role

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

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    # 1) find user by email
    user = db.query(User).filter(User.email == payload.email and User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # 2) verify password
    if not verify_password(payload.password, user.pwd_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # 3) create JWT token
    token_data = {"sub": user.email, "role": user.role, "id": user.id}
    access_token = create_token(token_data)

    # 4) return token response
    return {"access_token":access_token, "role":user.role}

@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(require_role("viewer"))):
    return current_user