from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.encounter import Encounter
from app.models.enums import ActivityType, EncounterStatus, UserRole
from app.models.patient import Patient
from app.models.user import User
from app.schemas.encounter import EncounterCreate, EncounterUpdate, SupervisorDecision
from app.services.activity import log_activity
from app.services.credit import calculate_provisional_credits, create_verified_credits
from app.services.wallet import create_wallet_record_for_encounter


def create_encounter(db: Session, payload: EncounterCreate, user: User) -> Encounter:
    _require_role(user, UserRole.student)
    patient = _get_patient_or_404(db, payload.patient_id)
    encounter = Encounter(
        **payload.model_dump(),
        student_id=user.id,
        consent_timestamp=datetime.utcnow() if payload.consent_obtained else None,
    )
    db.add(encounter)
    db.flush()
    log_activity(
        db,
        user,
        ActivityType.encounter_complete,
        f"Created encounter draft for {patient.full_name}",
        {"encounter_id": str(encounter.id), "patient_id": str(patient.id), "status": encounter.status.value},
    )
    db.commit()
    db.refresh(encounter)
    return encounter


def list_encounters(db: Session, user: User, status_filter: EncounterStatus | None = None) -> list[Encounter]:
    query = db.query(Encounter)
    if user.role == UserRole.student:
        query = query.filter(Encounter.student_id == user.id)
    elif user.role == UserRole.supervisor:
        query = query.filter(or_(Encounter.supervisor_id == user.id, Encounter.status == EncounterStatus.pending_review))
    else:
        _require_role(user, UserRole.admin)

    if status_filter:
        query = query.filter(Encounter.status == status_filter)
    return query.order_by(Encounter.updated_at.desc()).all()


def get_encounter_detail(db: Session, encounter_id, user: User) -> dict:
    encounter = get_accessible_encounter(db, encounter_id, user)
    patient = _get_patient_or_404(db, encounter.patient_id)
    activities = db.query(Activity).order_by(Activity.created_at.asc()).all()
    timeline = [
        activity
        for activity in activities
        if (activity.event_data or {}).get("encounter_id") == str(encounter.id)
    ]
    return {
        **_encounter_response(encounter),
        "patient": patient,
        "activity_timeline": [_activity_response(activity) for activity in timeline],
    }


def update_encounter(db: Session, encounter_id, payload: EncounterUpdate, user: User) -> Encounter:
    encounter = get_accessible_encounter(db, encounter_id, user)
    if encounter.status not in {EncounterStatus.draft, EncounterStatus.in_progress, EncounterStatus.rejected}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft, in-progress, or rejected encounters can be edited.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(encounter, field, value)
    encounter.status = EncounterStatus.in_progress
    encounter.updated_at = datetime.utcnow()
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    return encounter


def finalize_encounter(db: Session, encounter_id, user: User) -> Encounter:
    encounter = get_accessible_encounter(db, encounter_id, user)
    if user.role != UserRole.student or encounter.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the student owner can finalize this encounter")
    if not encounter.working_diagnosis or not encounter.treatment_plan:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="working_diagnosis and treatment_plan are required before finalizing.",
        )

    encounter.credit_breakdown = calculate_provisional_credits(encounter)
    encounter.credits_provisional = sum(encounter.credit_breakdown.values())
    encounter.status = EncounterStatus.pending_review
    encounter.finalized_at = datetime.utcnow()
    encounter.updated_at = datetime.utcnow()
    db.add(encounter)
    log_activity(
        db,
        user,
        ActivityType.encounter_complete,
        "Encounter submitted for supervisor review",
        {"encounter_id": str(encounter.id), "status": encounter.status.value},
    )
    db.commit()
    db.refresh(encounter)
    return encounter


def approve_encounter(db: Session, encounter_id, payload: SupervisorDecision | None, user: User) -> Encounter:
    _require_role(user, UserRole.supervisor)
    encounter = _get_encounter_or_404(db, encounter_id)
    if encounter.status != EncounterStatus.pending_review:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending review encounters can be approved")

    patient = _get_patient_or_404(db, encounter.patient_id)
    encounter.status = EncounterStatus.finalized
    encounter.supervisor_id = user.id
    encounter.supervisor_notes = payload.notes if payload else None
    encounter.supervisor_verified = True
    encounter.verified_at = datetime.utcnow()
    encounter.updated_at = datetime.utcnow()
    create_verified_credits(db, encounter, user.id)
    encounter.credits_earned = sum((encounter.credit_breakdown or {}).values())
    wallet_record = create_wallet_record_for_encounter(db, encounter, patient)
    db.add(encounter)
    log_activity(
        db,
        user,
        ActivityType.encounter_approved,
        "Encounter approved and credits awarded",
        {"encounter_id": str(encounter.id), "student_id": str(encounter.student_id), "credits_earned": encounter.credits_earned},
    )
    log_activity(
        db,
        user,
        ActivityType.wallet_push,
        "Encounter summary added to patient wallet",
        {"encounter_id": str(encounter.id), "patient_id": str(patient.id), "wallet_record_id": str(wallet_record.id)},
    )
    db.commit()
    db.refresh(encounter)
    return encounter


def reject_encounter(db: Session, encounter_id, payload: SupervisorDecision, user: User) -> Encounter:
    _require_role(user, UserRole.supervisor)
    encounter = _get_encounter_or_404(db, encounter_id)
    if encounter.status != EncounterStatus.pending_review:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending review encounters can be rejected")

    encounter.status = EncounterStatus.rejected
    encounter.supervisor_id = user.id
    encounter.supervisor_notes = payload.notes
    encounter.updated_at = datetime.utcnow()
    db.add(encounter)
    log_activity(
        db,
        user,
        ActivityType.encounter_rejected,
        "Encounter rejected by supervisor",
        {"encounter_id": str(encounter.id), "student_id": str(encounter.student_id), "notes": payload.notes},
    )
    db.commit()
    db.refresh(encounter)
    return encounter


def get_accessible_encounter(db: Session, encounter_id, user: User) -> Encounter:
    encounter = _get_encounter_or_404(db, encounter_id)
    if user.role == UserRole.student and encounter.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Encounter does not belong to this student")
    if user.role == UserRole.supervisor:
        return encounter
    if user.role != UserRole.student:
        _require_role(user, UserRole.admin)
    return encounter


def _get_encounter_or_404(db: Session, encounter_id) -> Encounter:
    encounter = db.get(Encounter, encounter_id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")
    return encounter


def _get_patient_or_404(db: Session, patient_id) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def _require_role(user: User, role: UserRole) -> None:
    if user.role != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{role.value.title()} access required")


def _encounter_response(encounter: Encounter) -> dict:
    return {
        field: getattr(encounter, field)
        for field in (
            "id",
            "patient_id",
            "student_id",
            "supervisor_id",
            "status",
            "chief_complaint",
            "duration",
            "severity",
            "associated_symptoms",
            "consent_obtained",
            "ai_diagnosis",
            "ai_confidence",
            "ai_differential",
            "ai_actions_triggered",
            "vitals",
            "exam_notes",
            "working_diagnosis",
            "investigations",
            "treatment_plan",
            "follow_up",
            "supervisor_notes",
            "supervisor_verified",
            "verified_at",
            "credits_provisional",
            "credits_earned",
            "credit_breakdown",
            "created_at",
            "updated_at",
            "finalized_at",
        )
    }


def _activity_response(activity: Activity) -> dict:
    return {
        "id": activity.id,
        "user_id": activity.user_id,
        "activity_type": activity.activity_type,
        "description": activity.description,
        "event_data": activity.event_data,
        "created_at": activity.created_at,
    }
