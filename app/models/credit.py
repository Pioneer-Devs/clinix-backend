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
