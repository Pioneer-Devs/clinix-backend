"""AI Analysis API Router.

Provides the endpoint for running AI-powered clinical analysis on encounters.
This is the core "AI that acts" feature — triggering symptom analysis,
differential diagnosis, and MCP action skills in one call.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.encounter import Encounter
from app.models.enums import EncounterStatus, UserRole
from app.models.patient import Patient
from app.models.user import User
from app.services.ai_agent import analyze_symptoms
from app.services.mcp_orchestrator import run_ai_analysis
from app.utils.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.post("/encounters/{encounter_id}/analyze")
def ai_analyze_encounter(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run AI clinical analysis on an existing encounter.

    Triggers the full AI + MCP pipeline:
    1. Symptom pattern matching → diagnosis + confidence
    2. MCP skill execution → inventory checks, test recommendations
    3. Logs skill executions to the database
    4. Updates the encounter record with AI results

    Requires the encounter to be in draft or in_progress status.
    Only the encounter's student owner can trigger analysis.
    """
    encounter = db.get(Encounter, encounter_id)
    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )

    # Access control: only the student owner or a supervisor can trigger
    if current_user.role == UserRole.student and encounter.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only analyze your own encounters",
        )

    # Only allow analysis on editable encounters
    if encounter.status not in {EncounterStatus.draft, EncounterStatus.in_progress, EncounterStatus.rejected}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot run AI analysis on encounter with status '{encounter.status.value}'",
        )

    # Get patient for demographic context
    patient = db.get(Patient, encounter.patient_id)

    # Run the full AI + MCP pipeline
    analysis = run_ai_analysis(
        db=db,
        encounter=encounter,
        patient=patient,
        user=current_user,
    )

    return {
        "encounter_id": str(encounter_id),
        "status": "completed",
        "analysis": analysis,
    }


from pydantic import BaseModel

class SymptomAnalysisRequest(BaseModel):
    chief_complaint: str
    associated_symptoms: list[str] | None = None
    vitals: dict | None = None
    patient_age: int | None = None
    patient_gender: str | None = None


@router.post("/analyze-symptoms")
def ai_analyze_symptoms_direct(
    payload: SymptomAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """Run AI analysis on raw symptoms without an encounter.

    Useful for quick symptom checks before creating a formal encounter.
    Does NOT persist results or trigger MCP actions.
    """
    analysis = analyze_symptoms(
        chief_complaint=payload.chief_complaint,
        associated_symptoms=payload.associated_symptoms or [],
        vitals=payload.vitals or {},
        patient_age=payload.patient_age,
        patient_gender=payload.patient_gender,
    )

    return {
        "status": "completed",
        "analysis": analysis,
    }

