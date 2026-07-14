from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.schemas.wallet import WalletConfirmPushRequest, WalletQRRead, WalletRecordRead
from app.services import patient as patient_service
from app.services import wallet as wallet_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/wallets", tags=["Wallet"])
legacy_router = APIRouter(prefix="/wallet", tags=["Wallet"])


def _get_patient_wallet_qr(patient_id, db, current_user):
    patient_service.get_patient_or_404(db, patient_id)
    return wallet_service.get_patient_wallet_qr(db, patient_id)


@router.get("/{patient_id}", response_model=WalletQRRead)
def get_patient_wallet(patient_id, db=Depends(get_db), current_user=Depends(get_current_user)):
    return _get_patient_wallet_qr(patient_id, db, current_user)


@router.get("/{patient_id}/qr", response_model=WalletQRRead)
def get_patient_wallet_qr(patient_id, db=Depends(get_db), current_user=Depends(get_current_user)):
    return _get_patient_wallet_qr(patient_id, db, current_user)


@router.post("/{patient_id}/push-to-pod")
async def push_patient_wallet_to_pod(patient_id, db=Depends(get_db), current_user=Depends(get_current_user)):
    patient_service.get_patient_or_404(db, patient_id)
    return await wallet_service.push_patient_wallet_to_pod(db, patient_id)


@router.post("/{patient_id}/confirm-push", response_model=WalletRecordRead)
def confirm_patient_wallet_push(
    patient_id,
    payload: WalletConfirmPushRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient_service.get_patient_or_404(db, patient_id)
    return wallet_service.confirm_solid_push(db, patient_id, payload.solid_pod_url)


@legacy_router.get("/{patient_id}/qr", response_model=WalletQRRead)
def get_legacy_patient_wallet_qr(patient_id, db=Depends(get_db), current_user=Depends(get_current_user)):
    return _get_patient_wallet_qr(patient_id, db, current_user)


@legacy_router.post("/recover")
async def recover_wallet_record(
    enc: UUID = Query(..., description="Encounter ID from the wallet QR link"),
    db=Depends(get_db),
):
    """Public endpoint (no auth). Re-provisions the Solid pod and re-pushes
    encounter data when the pod has been wiped after a redeploy."""
    return await wallet_service.recover_wallet_record(db, str(enc))

