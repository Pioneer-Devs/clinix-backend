from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate


def create_patient(db: Session, payload: PatientCreate) -> Patient:
    patient = Patient(**payload.model_dump(), updated_at=datetime.utcnow())
    db.add(patient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A patient with this hospital_id already exists.",
        ) from exc
    db.refresh(patient)
    return patient


def search_patients(db: Session, query_text: str = "", limit: int = 20) -> list[Patient]:
    query = db.query(Patient)
    if query_text:
        like = f"%{query_text}%"
        query = query.filter(
            or_(
                Patient.hospital_id.ilike(like),
                Patient.first_name.ilike(like),
                Patient.last_name.ilike(like),
                Patient.phone.ilike(like),
            )
        )
    return query.order_by(Patient.created_at.desc()).limit(limit).all()


def get_patient_or_404(db: Session, patient_id) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient
