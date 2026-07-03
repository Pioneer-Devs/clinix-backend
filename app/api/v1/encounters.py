from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.encounter import Encounter
from app.models.enums import EncounterStatus, UserRole
from app.models.patient import Patient
from app.models.user import User
from app.schemas.encounter import (
    EncounterCreate,
    EncounterDetail,
    EncounterRead,
    EncounterUpdate,
    SupervisorDecision,
)
from app.services import encounter as encounter_service
from app.services.mcp_orchestrator import run_ai_analysis
from app.utils.auth import get_current_user

router = APIRouter(prefix="/encounters", tags=["Encounters"])


@router.post("", response_model=EncounterRead, status_code=status.HTTP_201_CREATED)
def create_encounter(
    payload: EncounterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return encounter_service.create_encounter(db, payload, current_user)


@router.get("", response_model=list[EncounterRead])
def list_encounters(
    status_filter: EncounterStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return encounter_service.list_encounters(db, current_user, status_filter)


@router.get("/{encounter_id}", response_model=EncounterDetail)
def get_encounter(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return encounter_service.get_encounter_detail(db, encounter_id, current_user)


@router.patch("/{encounter_id}", response_model=EncounterRead)
def update_encounter(
    encounter_id: UUID,
    payload: EncounterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return encounter_service.update_encounter(db, encounter_id, payload, current_user)


@router.post("/{encounter_id}/ai-analyze")
def ai_analyze_encounter(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run AI clinical analysis on this encounter (PRD endpoint).

    Triggers the full AI + MCP pipeline and stores results on the encounter.
    """
    encounter = db.get(Encounter, encounter_id)
    if not encounter:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    if current_user.role == UserRole.student and encounter.student_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    patient = db.get(Patient, encounter.patient_id)
    analysis = run_ai_analysis(db=db, encounter=encounter, patient=patient, user=current_user)

    return {
        "encounter_id": str(encounter_id),
        "status": "completed",
        "analysis": analysis,
    }


@router.post("/{encounter_id}/finalize", response_model=EncounterRead)
def finalize_encounter(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return encounter_service.finalize_encounter(db, encounter_id, current_user)


@router.post("/{encounter_id}/approve", response_model=EncounterRead)
def approve_encounter(
    encounter_id: UUID,
    payload: SupervisorDecision | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return encounter_service.approve_encounter(db, encounter_id, payload, current_user)


@router.post("/{encounter_id}/reject", response_model=EncounterRead)
def reject_encounter(
    encounter_id: UUID,
    payload: SupervisorDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return encounter_service.reject_encounter(db, encounter_id, payload, current_user)
