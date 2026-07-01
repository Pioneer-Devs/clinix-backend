from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.wallet import WalletQRRead
from app.services import patient as patient_service
from app.services import wallet as wallet_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/{patient_id}/qr", response_model=WalletQRRead)
def get_patient_wallet_qr(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient_service.get_patient_or_404(db, patient_id)
    return wallet_service.get_patient_wallet_qr(db, patient_id)
