from typing import Optional, Any, Dict, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from app.models.encounter import Encounter

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


# Registered skill names — extend as new MCP skills are added
SKILL_NAMES = {
    "malaria_detect",
    "cardiac_alert",
    "diabetes_management",
    "prenatal_screening",
}


class ActionSkillLog(SQLModel, table=True):
    __tablename__ = "action_skill_logs"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    encounter_id: UUID = Field(foreign_key="encounters.id", index=True)
    skill_name: str = Field(max_length=50, index=True)  # e.g. "malaria_detect"
    triggered_at: datetime = Field(default_factory=datetime.utcnow)

    # Raw input fed to the skill (symptoms, vitals, demographics)
    input_data: Optional[Dict[str, Any]] = Field(
        default={}, sa_column=Column(JSON_TYPE, default=dict)
    )
    # Structured output: {diagnosis_confidence, recommended_actions, urgency}
    output_data: Optional[Dict[str, Any]] = Field(
        default={}, sa_column=Column(JSON_TYPE, default=dict)
    )
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)
    execution_time_ms: Optional[int] = Field(default=None)

    # Tracks whether the student/supervisor accepted or dismissed this skill's output
    outcome: Optional[str] = Field(
        default=None, max_length=20
    )  # "accepted" | "dismissed" | "modified"

    # Relationship
    encounter: Optional["Encounter"] = Relationship(back_populates="skill_logs")
