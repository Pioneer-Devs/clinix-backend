from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.enums import ActivityType

class ActivityRead(SQLModel):
    id: UUID
    user_id: UUID
    activity_type: ActivityType
    description: str
    event_data: Optional[Dict[str, Any]]
    created_at: datetime