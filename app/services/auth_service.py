from fastapi import HTTPException, status, BackgroundTasks, Response
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserCreate, VerifyEmailRequest, Token
from app.utils.auth import (
    hash_password,
    normalize_email,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_verification_code,
)
from app.utils.cookies import set_auth_cookies
from app.utils.email import send_verification_email

def register_user(payload: UserCreate, background_tasks: BackgroundTasks, db: Session) -> User:
    email = normalize_email(payload.email)

    # Check for duplicate email
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Prevent registration with patient role (patients use QR codes, no login)
    if payload.role == UserRole.patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient accounts cannot be registered. Patients access records via QR code.",
        )

    verification_code = generate_verification_code()

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        year_of_study=payload.year_of_study,
        matric_number=payload.matric_number,
        hospital=payload.hospital,
        mdcn_reg_no=payload.mdcn_reg_no,
        is_verified=False,
        verification_code=verification_code,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Send verification email (fire-and-forget for now)
    background_tasks.add_task(send_verification_email, email, verification_code, user.first_name)

    return user

def verify_user_email(payload: VerifyEmailRequest, db: Session) -> dict:
    email = normalize_email(payload.email)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email.",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is already verified.",
        )

    if user.verification_code != payload.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code.",
        )

    user.is_verified = True
    user.verification_code = None  # Clear the code after successful verification
    db.commit()

    return {"message": "Email verified successfully. You can now log in."}

def resend_user_verification(payload: VerifyEmailRequest, background_tasks: BackgroundTasks, db: Session) -> dict:
    email = normalize_email(payload.email)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email.",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is already verified.",
        )

    new_code = generate_verification_code()
    user.verification_code = new_code
    db.commit()

    background_tasks.add_task(send_verification_email, email, new_code, user.first_name)

    return {"message": "A new verification code has been sent to your email."}

def authenticate_user(form_data: OAuth2PasswordRequestForm, response: Response, db: Session) -> Token:
    email = normalize_email(form_data.username)  # OAuth2 form uses 'username'

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in.",
        )

    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    # Set HttpOnly cookies
    set_auth_cookies(response, access_token, refresh_token)

    return Token(access_token=access_token)
