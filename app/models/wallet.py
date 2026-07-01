from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

from app.models.enums import WalletRecordStatus

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.encounter import Encounter


class WalletRecord(SQLModel, table=True):
    __tablename__ = "wallet_records"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    patient_id: UUID = Field(foreign_key="patients.id", index=True)
    encounter_id: UUID = Field(foreign_key="encounters.id", unique=True)  # One wallet push per encounter

    # Chekk integration
    chekk_record_id: Optional[str] = Field(default=None, max_length=100)
    qr_payload: str                          # e.g. "CLINIX-ENC-<uuid>-<date>"
    encrypted_summary: str                   # AES-256 encrypted, base64-encoded JSON
    encryption_iv: str = Field(max_length=100)  # AES initialization vector

    # Status tracking
    status: WalletRecordStatus = Field(default=WalletRecordStatus.pending, index=True)
    pushed_at: Optional[datetime] = Field(default=None)
    accessed_at: Optional[datetime] = Field(default=None)   # When patient first opens QR

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    patient: Optional["Patient"] = Relationship(back_populates="wallet_records")
    encounter: Optional["Encounter"] = Relationship(back_populates="wallet_records")
