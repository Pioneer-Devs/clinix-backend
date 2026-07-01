from sqlmodel import SQLModel
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from app.models.enums import Gender

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
    created_at: datetime


class PatientSearchResult(PatientRead):
    age: int


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
