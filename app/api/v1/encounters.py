from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.enums import EncounterStatus
from app.models.user import User
from app.schemas.encounter import (
    EncounterCreate,
    EncounterDetail,
    EncounterRead,
    EncounterUpdate,
    SupervisorDecision,
)
from app.services import encounter as encounter_service
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
