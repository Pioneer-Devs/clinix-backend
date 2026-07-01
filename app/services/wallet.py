import base64
import json
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.enums import WalletRecordStatus
from app.models.wallet import WalletRecord
from fastapi import HTTPException, status


def create_wallet_record_for_encounter(db: Session, encounter, patient) -> WalletRecord:
    existing = (
        db.query(WalletRecord)
        .filter(WalletRecord.encounter_id == encounter.id)
        .first()
    )
    if existing:
        return existing

    summary = {
        "encounter_id": str(encounter.id),
        "patient_id": str(patient.id),
        "encounter_date": encounter.finalized_at.isoformat() if encounter.finalized_at else datetime.utcnow().isoformat(),
        "chief_complaint": encounter.chief_complaint,
        "history": {
            "duration": encounter.duration,
            "severity": encounter.severity.value if encounter.severity else None,
            "associated_symptoms": encounter.associated_symptoms or [],
        },
        "vitals": encounter.vitals or {},
        "working_diagnosis": encounter.working_diagnosis,
        "investigations": encounter.investigations or [],
        "treatment_plan": encounter.treatment_plan,
        "follow_up": encounter.follow_up,
        "student_id": str(encounter.student_id),
        "supervisor_id": str(encounter.supervisor_id) if encounter.supervisor_id else None,
    }

    wallet_record = WalletRecord(
        patient_id=patient.id,
        encounter_id=encounter.id,
        qr_payload=f"CLINIX-ENC-{encounter.id}-{datetime.utcnow().date().isoformat()}",
        encrypted_summary=base64.urlsafe_b64encode(json.dumps(summary).encode("utf-8")).decode("utf-8"),
        encryption_iv=uuid4().hex,
        status=WalletRecordStatus.pushed,
        pushed_at=datetime.utcnow(),
    )
    db.add(wallet_record)
    return wallet_record


def get_latest_patient_wallet_record(db: Session, patient_id) -> WalletRecord | None:
    return (
        db.query(WalletRecord)
        .filter(WalletRecord.patient_id == patient_id)
        .order_by(WalletRecord.created_at.desc())
        .first()
    )


def get_patient_wallet_qr(db: Session, patient_id) -> dict:
    wallet_record = get_latest_patient_wallet_record(db, patient_id)
    if not wallet_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No wallet record exists for this patient")
    return build_wallet_qr_response(wallet_record)


def build_wallet_qr_response(wallet_record: WalletRecord) -> dict:
    return {
        "qr_payload": wallet_record.qr_payload,
        "access_url": f"https://wallet.clinix.local/records/{wallet_record.qr_payload}",
        "expires_at": wallet_record.created_at + timedelta(days=30),
    }
