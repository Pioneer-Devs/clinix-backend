from app.models.enums import WalletRecordStatus
from app.models.wallet import WalletRecord
from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class WalletPushRequest(SQLModel):
    encounter_id: UUID


class WalletRecordRead(SQLModel):
    id: UUID
    patient_id: UUID
    encounter_id: UUID
    qr_payload: str
    status: WalletRecordStatus
    pushed_at: Optional[datetime]
    accessed_at: Optional[datetime]
    created_at: datetime


class WalletQRRead(SQLModel):
    qr_payload: str
    access_url: str
    expires_at: datetime
