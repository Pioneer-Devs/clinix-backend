from datetime import date, datetime
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlmodel import Column, Field, Relationship, SQLModel

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
    solid_pod_url: Optional[str] = Field(default=None, max_length=255)
    solid_web_id: Optional[str] = Field(default=None, max_length=255)
    solid_token_id: Optional[str] = Field(default=None, max_length=255)
    solid_token_secret: Optional[str] = Field(default=None, max_length=255)
    insurance_id: Optional[str] = Field(default=None, max_length=50)


class Patient(PatientBase, table=True):
    __tablename__ = "patients"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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
