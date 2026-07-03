from typing import Optional, Any, Dict, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.models.enums import ActivityType

if TYPE_CHECKING:
    from app.models.user import User

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class Activity(SQLModel, table=True):
    __tablename__ = "activities"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    activity_type: ActivityType = Field(index=True)
    description: str                        # Human-readable, shown in feed
    # Flexible context bag: {encounter_id, patient_name, credits_earned, etc.}
    # Note: "metadata" is reserved by SQLAlchemy — using event_data instead.
    event_data: Optional[Dict[str, Any]] = Field(
        default={}, sa_column=Column(JSON_TYPE, default=dict)
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    user: Optional["User"] = Relationship(back_populates="activities")
