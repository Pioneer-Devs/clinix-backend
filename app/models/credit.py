from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

from app.models.enums import CreditCategory

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.encounter import Encounter


class ClinicalCredit(SQLModel, table=True):
    __tablename__ = "clinical_credits"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign keys
    student_id: UUID = Field(foreign_key="users.id", index=True)
    encounter_id: UUID = Field(foreign_key="encounters.id", index=True)
    supervisor_id: Optional[UUID] = Field(default=None, foreign_key="users.id")

    category: CreditCategory
    points: int

    # Verification
    verified: bool = Field(default=False)
    # SHA-256 HMAC over (student_id + encounter_id + category + points + supervisor_id)
    signed_hash: Optional[str] = Field(default=None, max_length=255)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    student: Optional["User"] = Relationship(
        back_populates="credits",
        sa_relationship_kwargs={"foreign_keys": "ClinicalCredit.student_id"},
    )
    encounter: Optional["Encounter"] = Relationship(back_populates="credits")


# ── Credit calculation logic ───────────────────────────────────────────────────

CREDIT_RULES: dict[CreditCategory, int] = {
    CreditCategory.history_taking: 2,   # Complete history documented
    CreditCategory.physical_exam: 2,    # Vitals + exam notes present
    CreditCategory.diagnosis: 2,        # Student pre-AI diagnosis submitted + supervisor agrees
    CreditCategory.treatment: 2,        # Treatment plan appropriate per supervisor
    CreditCategory.communication: 1,    # Optional patient satisfaction
}


def calculate_provisional_credits(encounter) -> dict[str, int]:
    """
    Calculates provisional credits for an encounter before supervisor review.
    Credits are PROVISIONAL here — only confirmed after supervisor approval.
    """
    breakdown: dict[str, int] = {}

    if encounter.chief_complaint and len(encounter.chief_complaint) > 20:
        breakdown[CreditCategory.history_taking.value] = CREDIT_RULES[CreditCategory.history_taking]

    if encounter.vitals and encounter.exam_notes:
        breakdown[CreditCategory.physical_exam.value] = CREDIT_RULES[CreditCategory.physical_exam]

    # Only award diagnosis credit if student submitted a pre-AI diagnosis
    if encounter.student_pre_ai_diagnosis and encounter.working_diagnosis:
        breakdown[CreditCategory.diagnosis.value] = CREDIT_RULES[CreditCategory.diagnosis]

    if encounter.treatment_plan and encounter.investigations:
        breakdown[CreditCategory.treatment.value] = CREDIT_RULES[CreditCategory.treatment]

    return breakdown


# ── Pydantic schemas ───────────────────────────────────────────────────────────

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