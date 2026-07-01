from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel

from app.models.enums import UserRole


class UserCreate(SQLModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.student
    year_of_study: Optional[int] = None
    hospital: Optional[str] = None
    mdcn_reg_no: Optional[str] = None


class UserRead(SQLModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    year_of_study: Optional[int]
    hospital: Optional[str]
    mdcn_reg_no: Optional[str]
    is_active: bool
    created_at: datetime


class UserPublic(SQLModel):
    """Minimal representation for embedding in other responses."""
    id: UUID
    first_name: str
    last_name: str
    role: UserRole
    hospital: Optional[str]