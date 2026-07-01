from fastapi import APIRouter, Depends, Response, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, Token, VerifyEmailRequest
from app.services import auth_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Register a new student or supervisor account.
    A 6-digit verification code is sent to the provided email.
    """
    return auth_service.register_user(payload, background_tasks, db)


# ---------------------------------------------------------------------------
# POST /verify-email
# ---------------------------------------------------------------------------
@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify a user's email with the 6-digit code sent during registration."""
    return auth_service.verify_user_email(payload, db)


# ---------------------------------------------------------------------------
# POST /resend-verification
# ---------------------------------------------------------------------------
@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification(payload: VerifyEmailRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Resend a new verification code. The `code` field in the payload is ignored."""
    return auth_service.resend_user_verification(payload, background_tasks, db)


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------
@router.post("/login", response_model=Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate with email + password.
    Sets HttpOnly cookies and returns the token in the JSON body.
    """
    return auth_service.authenticate_user(form_data, response, db)


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the profile information of the currently authenticated user.
    """
    return current_user
