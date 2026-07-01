from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import model_validator
from sqlmodel import SQLModel

from app.models.enums import UserRole


class UserCreate(SQLModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.student
    year_of_study: Optional[int] = None
    matric_number: Optional[str] = None
    hospital: Optional[str] = None
    mdcn_reg_no: Optional[str] = None

    @model_validator(mode="after")
    def validate_role_fields(self):
        if self.role == UserRole.student:
            if not self.year_of_study:
                raise ValueError("year_of_study is required for students")
            if not self.matric_number:
                raise ValueError("matric_number is required for students")
        elif self.role == UserRole.supervisor:
            if not self.mdcn_reg_no:
                raise ValueError("mdcn_reg_no is required for supervisors")
        return self


class UserRead(SQLModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    year_of_study: Optional[int]
    matric_number: Optional[str]
    hospital: Optional[str]
    mdcn_reg_no: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserPublic(SQLModel):
    """Minimal representation for embedding in other responses."""
    id: UUID
    first_name: str
    last_name: str
    role: UserRole
    hospital: Optional[str]


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(SQLModel):
    email: str
    code: str