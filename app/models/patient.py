from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import date, datetime

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String

from app.models.enums import Gender

if TYPE_CHECKING:
    from app.models.encounter import Encounter
    from app.models.wallet import WalletRecord


class PatientBase(SQLModel):
    hospital_id: str = Field(
        sa_column=Column(String(50), unique=True, nullable=False),
        description="e.g. LTH-2024-001",
    )
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    date_of_birth: date
    gender: Gender
    phone: str = Field(max_length=20)
    address: Optional[str] = Field(default=None)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20)
    chekk_wallet_id: Optional[str] = Field(default=None, max_length=100)
    insurance_id: Optional[str] = Field(default=None, max_length=50)


class Patient(PatientBase, table=True):
    __tablename__ = "patients"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    encounters: List["Encounter"] = Relationship(back_populates="patient")
    wallet_records: List["WalletRecord"] = Relationship(back_populates="patient")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class PatientCreate(SQLModel):
    hospital_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender
    phone: str
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    insurance_id: Optional[str] = None


class PatientRead(SQLModel):
    id: UUID
    hospital_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender
    phone: str
    address: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    chekk_wallet_id: Optional[str]
    created_at: datetime


class PatientQueueItem(SQLModel):
    """Lightweight shape for the daily patient queue."""
    id: UUID
    hospital_id: str
    first_name: str
    last_name: str
    age: int
    gender: Gender
    chief_complaint: Optional[str] = None   # Pulled from latest draft encounter
    waiting_time_minutes: Optional[int] = None
    priority: Optional[str] = None