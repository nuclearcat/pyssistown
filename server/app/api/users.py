from __future__ import annotations

from hashlib import sha256
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import User, UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


def hash_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()


@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)) -> User:
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(email=user.email, password_hash=hash_password(user.password))
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: int, session: Session = Depends(get_session)) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
