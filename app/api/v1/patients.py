from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientRead, PatientSearchResult
from app.services import patient as patient_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def create_patient(
    payload: PatientCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await patient_service.create_patient(db, payload, background_tasks)


@router.get("/search", response_model=list[PatientSearchResult])
def search_patients(
    q: str = Query("", description="Search by name, hospital ID, or phone number"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return patient_service.search_patients(db, q, limit)


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return patient_service.get_patient_or_404(db, patient_id)
