from typing import Optional, List, Any, Dict, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Text, Numeric
from sqlalchemy.dialects.postgresql import JSONB

from app.models.enums import EncounterStatus, Severity

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.patient import Patient
    from app.models.credit import ClinicalCredit
    from app.models.wallet import WalletRecord
    from app.models.skill_log import ActionSkillLog


class Encounter(SQLModel, table=True):
    __tablename__ = "encounters"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign keys
    student_id: UUID = Field(foreign_key="users.id", index=True)
    patient_id: UUID = Field(foreign_key="patients.id", index=True)
    supervisor_id: Optional[UUID] = Field(default=None, foreign_key="users.id")

    # Status
    status: EncounterStatus = Field(default=EncounterStatus.draft, index=True)

    # ── Chief Complaint & History ─────────────────────────────────────────────
    chief_complaint: str = Field(sa_column=Column(Text, nullable=False))
    duration: Optional[str] = Field(default=None, max_length=50)
    severity: Optional[Severity] = Field(default=None)
    # List[str] — stored as JSONB e.g. ["fever", "headache", "chills"]
    associated_symptoms: Optional[List[Any]] = Field(
        default=[], sa_column=Column(JSONB, default=list)
    )

    # ── Patient Consent ───────────────────────────────────────────────────────
    consent_obtained: bool = Field(default=False)
    consent_timestamp: Optional[datetime] = Field(default=None)

    # ── AI Analysis ───────────────────────────────────────────────────────────
    ai_diagnosis: Optional[str] = Field(default=None)
    # Decimal 0.00–1.00 stored as Numeric for precision
    ai_confidence: Optional[float] = Field(
        default=None, sa_column=Column(Numeric(3, 2))
    )
    # List[{condition, probability}]
    ai_differential: Optional[List[Any]] = Field(
        default=[], sa_column=Column(JSONB, default=list)
    )
    # List[{skill, actions}]
    ai_actions_triggered: Optional[List[Any]] = Field(
        default=[], sa_column=Column(JSONB, default=list)
    )

    # ── Student Pre-AI Diagnosis (anti-gaming) ────────────────────────────────
    # Student must commit a preliminary diagnosis BEFORE viewing AI results.
    # This prevents credit farming by rubber-stamping AI suggestions.
    student_pre_ai_diagnosis: Optional[str] = Field(default=None, sa_column=Column(Text))
    student_pre_ai_timestamp: Optional[datetime] = Field(default=None)

    # ── Physical Exam ─────────────────────────────────────────────────────────
    # {temperature, blood_pressure, pulse, spo2, respiratory_rate, weight, height}
    vitals: Optional[Dict[str, Any]] = Field(
        default={}, sa_column=Column(JSONB, default=dict)
    )
    exam_notes: Optional[str] = Field(default=None, sa_column=Column(Text))

    # ── Assessment & Plan ─────────────────────────────────────────────────────
    working_diagnosis: Optional[str] = Field(default=None, sa_column=Column(Text))
    # List[str]
    investigations: Optional[List[Any]] = Field(
        default=[], sa_column=Column(JSONB, default=list)
    )
    treatment_plan: Optional[str] = Field(default=None, sa_column=Column(Text))
    follow_up: Optional[str] = Field(default=None, max_length=50)

    # ── Supervisor Review ─────────────────────────────────────────────────────
    supervisor_notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    supervisor_verified: bool = Field(default=False)
    verified_at: Optional[datetime] = Field(default=None)

    # ── Credits (provisional until supervisor verifies) ────────────────────────
    credits_provisional: int = Field(default=0)
    credits_earned: int = Field(default=0)       # Set only after supervisor approval
    # {history_taking: 2, physical_exam: 2, diagnosis: 2, treatment: 2, communication: 1}
    credit_breakdown: Optional[Dict[str, Any]] = Field(
        default={}, sa_column=Column(JSONB, default=dict)
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    finalized_at: Optional[datetime] = Field(default=None)

    # Relationships
    student: Optional["User"] = Relationship(
        back_populates="student_encounters",
        sa_relationship_kwargs={"foreign_keys": "Encounter.student_id"},
    )
    supervisor: Optional["User"] = Relationship(
        back_populates="supervised_encounters",
        sa_relationship_kwargs={"foreign_keys": "Encounter.supervisor_id"},
    )
    patient: Optional["Patient"] = Relationship(back_populates="encounters")
    credits: List["ClinicalCredit"] = Relationship(back_populates="encounter")
    wallet_records: List["WalletRecord"] = Relationship(back_populates="encounter")
    skill_logs: List["ActionSkillLog"] = Relationship(back_populates="encounter")


# ── Pydantic schemas ───────────────────────────────────────────────────────────

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