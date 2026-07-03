from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.models.enums import WalletRecordStatus


class WalletPushRequest(SQLModel):
    encounter_id: UUID


class WalletConfirmPushRequest(SQLModel):
    solid_pod_url: str


class WalletRecordRead(SQLModel):
    id: UUID
    patient_id: UUID
    encounter_id: UUID
    qr_payload: str
    solid_pod_url: Optional[str]
    status: WalletRecordStatus
    pushed_at: Optional[datetime]
    accessed_at: Optional[datetime]
    created_at: datetime


class WalletEncounterPayload(SQLModel):
    encounter_id: UUID
    patient_id: UUID
    patient_name: str
    solid_pod_url: Optional[str]
    solid_web_id: Optional[str]
    solid_token_id: Optional[str]
    solid_token_secret: Optional[str]
    chief_complaint: str
    diagnosis: Optional[str]
    ai_diagnosis: Optional[str]
    ai_confidence: Optional[float]
    treatment_plan: Optional[str]
    follow_up: Optional[str]
    vitals: Optional[Dict[str, Any]]
    finalized_at: Optional[datetime]
    associated_symptoms: Optional[List[Any]]
    investigations: Optional[List[Any]]
    wallet_status: WalletRecordStatus


class WalletQRRead(SQLModel):
    qr_payload: str
    access_url: str
    expires_at: datetime
    encounter: WalletEncounterPayload
