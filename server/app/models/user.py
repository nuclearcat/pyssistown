from __future__ import annotations

from datetime import datetime
from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password_hash: str


class UserRead(UserBase):
    id: int


class UserCreate(SQLModel):
    email: str
    password: str
