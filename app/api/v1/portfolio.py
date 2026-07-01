from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.credit import PortfolioStats, PortfolioSummary
from app.services import portfolio as portfolio_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/me", response_model=PortfolioSummary)
def get_my_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return portfolio_service.get_portfolio_summary(db, current_user)


@router.get("/stats", response_model=PortfolioStats)
def get_portfolio_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return portfolio_service.get_portfolio_stats(db, current_user)
