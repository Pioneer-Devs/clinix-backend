"""MCP Action Skills API Router.

Exposes endpoints for listing available MCP skills and querying
skill execution logs for encounters.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.encounter import Encounter
from app.models.skill_log import ActionSkillLog
from app.models.user import User
from app.services.mcp_orchestrator import get_available_skills
from app.utils.auth import get_current_user

router = APIRouter(prefix="/mcp", tags=["MCP Action Skills"])


@router.get("/skills")
def list_mcp_skills(
    current_user: User = Depends(get_current_user),
):
    """List all registered MCP Action Skills.

    Returns skill names, descriptions, and current status.
    """
    return {
        "skills": get_available_skills(),
        "total": len(get_available_skills()),
        "engine_status": "active",
    }


@router.get("/encounters/{encounter_id}/skill-logs")
def get_encounter_skill_logs(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all MCP skill execution logs for an encounter.

    Returns a timeline of all skills triggered during AI analysis,
    including input/output data and execution times.
    """
    encounter = db.get(Encounter, encounter_id)
    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )

    logs = (
        db.query(ActionSkillLog)
        .filter(ActionSkillLog.encounter_id == encounter_id)
        .order_by(ActionSkillLog.triggered_at.desc())
        .all()
    )

    return {
        "encounter_id": str(encounter_id),
        "skill_logs": [
            {
                "id": str(log.id),
                "skill_name": log.skill_name,
                "triggered_at": log.triggered_at.isoformat() if log.triggered_at else None,
                "input_data": log.input_data,
                "output_data": log.output_data,
                "success": log.success,
                "error_message": log.error_message,
                "execution_time_ms": log.execution_time_ms,
                "outcome": log.outcome,
            }
            for log in logs
        ],
        "total": len(logs),
    }
