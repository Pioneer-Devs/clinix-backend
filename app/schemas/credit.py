from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.models.enums import CreditCategory

class ClinicalCreditRead(SQLModel):
    id: UUID
    student_id: UUID
    encounter_id: UUID
    category: CreditCategory
    points: int
    verified: bool
    signed_hash: Optional[str]
    created_at: datetime


class PortfolioSummary(SQLModel):
    total_encounters: int
    total_diagnoses: int
    diagnostic_accuracy: float
    total_credits: int
    clinical_hours: int
    competencies: dict
    verified_procedures: List[ClinicalCreditRead]


class PortfolioStats(SQLModel):
    credits: dict
    skills: dict
    activities: dict
    encounters: dict
