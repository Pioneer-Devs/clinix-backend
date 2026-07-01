from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class ActionSkillLogRead(SQLModel):
    id: UUID
    encounter_id: UUID
    skill_name: str
    triggered_at: datetime
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    success: bool
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    outcome: Optional[str]