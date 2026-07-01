from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.activity import ActivityRead
from app.services import activity as activity_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("", response_model=list[ActivityRead])
def list_activity(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return activity_service.list_user_activity(db, current_user, limit)
