from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel

from app.models.enums import Severity, EncounterStatus

class EncounterCreate(SQLModel):
    patient_id: UUID
    chief_complaint: str
    duration: Optional[str] = None
    severity: Optional[Severity] = None
    associated_symptoms: List[str] = []
    consent_obtained: bool = False


class EncounterPreAIDiagnosis(SQLModel):
    """Student submits their own diagnosis before seeing AI results."""
    preliminary_diagnosis: str


class EncounterUpdate(SQLModel):
    """PATCH — any fields may be provided."""
    vitals: Optional[Dict[str, Any]] = None
    exam_notes: Optional[str] = None
    working_diagnosis: Optional[str] = None
    investigations: Optional[List[str]] = None
    treatment_plan: Optional[str] = None
    follow_up: Optional[str] = None
    severity: Optional[Severity] = None
    associated_symptoms: Optional[List[str]] = None


class SupervisorReview(SQLModel):
    approved: bool
    notes: Optional[str] = None


class EncounterRead(SQLModel):
    id: UUID
    patient_id: UUID
    student_id: UUID
    supervisor_id: Optional[UUID]
    status: EncounterStatus
    chief_complaint: str
    duration: Optional[str]
    severity: Optional[Severity]
    associated_symptoms: List[Any]
    consent_obtained: bool
    ai_diagnosis: Optional[str]
    ai_confidence: Optional[float]
    ai_differential: Optional[List[Any]]
    ai_actions_triggered: Optional[List[Any]]
    vitals: Optional[Dict[str, Any]]
    exam_notes: Optional[str]
    working_diagnosis: Optional[str]
    investigations: Optional[List[Any]]
    treatment_plan: Optional[str]
    follow_up: Optional[str]
    supervisor_notes: Optional[str]
    supervisor_verified: bool
    verified_at: Optional[datetime]
    credits_provisional: int
    credits_earned: int
    credit_breakdown: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime]