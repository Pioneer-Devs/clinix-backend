from typing import Optional, List, Any, Dict, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Text, Numeric, JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.models.enums import EncounterStatus, Severity

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.patient import Patient
    from app.models.credit import ClinicalCredit
    from app.models.wallet import WalletRecord
    from app.models.skill_log import ActionSkillLog

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


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
        default=[], sa_column=Column(JSON_TYPE, default=list)
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
        default=[], sa_column=Column(JSON_TYPE, default=list)
    )
    # List[{skill, actions}]
    ai_actions_triggered: Optional[List[Any]] = Field(
        default=[], sa_column=Column(JSON_TYPE, default=list)
    )

    # ── Student Pre-AI Diagnosis (anti-gaming) ────────────────────────────────
    # Student must commit a preliminary diagnosis BEFORE viewing AI results.
    # This prevents credit farming by rubber-stamping AI suggestions.
    student_pre_ai_diagnosis: Optional[str] = Field(default=None, sa_column=Column(Text))
    student_pre_ai_timestamp: Optional[datetime] = Field(default=None)

    # ── Physical Exam ─────────────────────────────────────────────────────────
    # {temperature, blood_pressure, pulse, spo2, respiratory_rate, weight, height}
    vitals: Optional[Dict[str, Any]] = Field(
        default={}, sa_column=Column(JSON_TYPE, default=dict)
    )
    exam_notes: Optional[str] = Field(default=None, sa_column=Column(Text))

    # ── Assessment & Plan ─────────────────────────────────────────────────────
    working_diagnosis: Optional[str] = Field(default=None, sa_column=Column(Text))
    # List[str]
    investigations: Optional[List[Any]] = Field(
        default=[], sa_column=Column(JSON_TYPE, default=list)
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
        default={}, sa_column=Column(JSON_TYPE, default=dict)
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
