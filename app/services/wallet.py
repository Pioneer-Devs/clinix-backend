from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import WalletRecordStatus
from app.models.wallet import WalletRecord


def create_wallet_record_for_encounter(db: Session, encounter, patient) -> WalletRecord:
    existing = (
        db.query(WalletRecord)
        .filter(WalletRecord.encounter_id == encounter.id)
        .first()
    )
    if existing:
        return existing

    wallet_record = WalletRecord(
        patient_id=patient.id,
        encounter_id=encounter.id,
        qr_payload=f"CLINIX-ENC-{encounter.id}-{datetime.utcnow().date().isoformat()}",
        solid_pod_url=None,
        status=WalletRecordStatus.pending,
    )
    db.add(wallet_record)
    return wallet_record


def get_latest_patient_wallet_record(db: Session, patient_id):
    return (
        db.query(WalletRecord)
        .filter(WalletRecord.patient_id == patient_id)
        .order_by(WalletRecord.created_at.desc())
        .first()
    )


def get_patient_wallet_qr(db: Session, patient_id):
    wallet_record = get_latest_patient_wallet_record(db, patient_id)
    if not wallet_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No wallet record exists for this patient")
    return build_wallet_qr_response(wallet_record)


def build_wallet_qr_response(wallet_record):
    encounter = wallet_record.encounter
    patient = wallet_record.patient
    if not encounter or not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet record is missing encounter or patient data")

    if not patient.solid_pod_url or not patient.solid_web_id or not patient.solid_token_id or not patient.solid_token_secret:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient Solid POD credentials are not provisioned")

    access_url = f"/wallet/view?pod={patient.solid_pod_url}&enc={encounter.id}"

    return {
        "qr_payload": wallet_record.qr_payload,
        "access_url": access_url,
        "expires_at": datetime.utcnow() + timedelta(days=1),
        "encounter": {
            "encounter_id": encounter.id,
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "solid_pod_url": patient.solid_pod_url,
            "solid_web_id": patient.solid_web_id,
            "solid_token_id": patient.solid_token_id,
            "solid_token_secret": patient.solid_token_secret,
            "chief_complaint": encounter.chief_complaint,
            "diagnosis": encounter.working_diagnosis,
            "ai_diagnosis": encounter.ai_diagnosis,
            "ai_confidence": encounter.ai_confidence,
            "treatment_plan": encounter.treatment_plan,
            "follow_up": encounter.follow_up,
            "vitals": encounter.vitals or {},
            "finalized_at": encounter.finalized_at,
            "associated_symptoms": encounter.associated_symptoms or [],
            "investigations": encounter.investigations or [],
            "wallet_status": wallet_record.status,
        },
    }


def confirm_solid_push(db: Session, patient_id, solid_pod_url):
    wallet_record = get_latest_patient_wallet_record(db, patient_id)
    if not wallet_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No wallet record exists for this patient")

    wallet_record.solid_pod_url = solid_pod_url
    wallet_record.status = WalletRecordStatus.pushed
    wallet_record.pushed_at = datetime.utcnow()
    db.add(wallet_record)
    db.commit()
    db.refresh(wallet_record)
    return wallet_record
