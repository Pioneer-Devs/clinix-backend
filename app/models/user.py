from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB

from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.encounter import Encounter
    from app.models.credit import ClinicalCredit
    from app.models.activity import Activity


class UserBase(SQLModel):
    email: str = Field(sa_column=Column(String(255), unique=True, nullable=False))
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    role: UserRole = Field(default=UserRole.student)
    year_of_study: Optional[int] = Field(default=None)          # Students only
    hospital: Optional[str] = Field(default=None, max_length=100)
    mdcn_reg_no: Optional[str] = Field(default=None, max_length=50)  # Supervisors only
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    student_encounters: List["Encounter"] = Relationship(
        back_populates="student",
        sa_relationship_kwargs={"foreign_keys": "Encounter.student_id"},
    )
    supervised_encounters: List["Encounter"] = Relationship(
        back_populates="supervisor",
        sa_relationship_kwargs={"foreign_keys": "Encounter.supervisor_id"},
    )
    credits: List["ClinicalCredit"] = Relationship(
        back_populates="student",
        sa_relationship_kwargs={"foreign_keys": "ClinicalCredit.student_id"},
    )
    activities: List["Activity"] = Relationship(back_populates="user")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


# ── Pydantic schemas (request / response) ─────────────────────────────────────

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