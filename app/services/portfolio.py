from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.credit import ClinicalCredit
from app.models.encounter import Encounter
from app.models.enums import EncounterStatus
from app.models.skill_log import ActionSkillLog
from app.models.user import User


def get_portfolio_summary(db: Session, user: User) -> dict:
    credits = db.query(ClinicalCredit).filter(ClinicalCredit.student_id == user.id).all()
    approved_encounters = (
        db.query(Encounter)
        .filter(Encounter.student_id == user.id, Encounter.status == EncounterStatus.finalized)
        .all()
    )

    competencies: dict[str, int] = {}
    for credit in credits:
        competencies[credit.category.value] = competencies.get(credit.category.value, 0) + credit.points

    total_encounters = len(approved_encounters)
    total_diagnoses = sum(1 for encounter in approved_encounters if encounter.working_diagnosis)

    return {
        "total_encounters": total_encounters,
        "total_diagnoses": total_diagnoses,
        "diagnostic_accuracy": 0.0,
        "total_credits": sum(credit.points for credit in credits),
        "clinical_hours": total_encounters,
        "competencies": competencies,
        "verified_procedures": credits,
    }


def get_portfolio_stats(db: Session, user: User) -> dict:
    from app.models.enums import UserRole
    
    is_supervisor = user.role == UserRole.supervisor
    
    if is_supervisor:
        encounters_filter = Encounter.supervisor_id == user.id
        credits_filter = ClinicalCredit.supervisor_id == user.id if hasattr(ClinicalCredit, 'supervisor_id') else ClinicalCredit.student_id == user.id # Credits might not map to supervisor
    else:
        encounters_filter = Encounter.student_id == user.id
        credits_filter = ClinicalCredit.student_id == user.id

    return {
        "credits": _count_by(db, ClinicalCredit.category, credits_filter),
        "skills": _count_by(
            db,
            ActionSkillLog.skill_name,
            ActionSkillLog.encounter_id.in_(
                db.query(Encounter.id).filter(encounters_filter)
            ),
        ),
        "activities": _count_by(db, Activity.activity_type, Activity.user_id == user.id),
        "encounters": _count_by(db, Encounter.status, encounters_filter),
    }


def _count_by(db: Session, column, criterion) -> dict:
    rows = db.query(column, func.count()).filter(criterion).group_by(column).all()
    return {str(key.value if hasattr(key, "value") else key): count for key, count in rows}
