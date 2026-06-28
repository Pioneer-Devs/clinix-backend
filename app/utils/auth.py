import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
bearer_scheme= HTTPBearer(auto_error=False)

def normalize_email(email:str) -> str:
    return email.strip().lower()

def hash_password(password:str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
	return pwd_context.verify(plain_password, password_hash)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
	token_data = data.copy()
	expires_delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
	expire = datetime.now(timezone.utc) + expires_delta
	token_data.update({"exp": expire, "type": "access"})
	return jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> dict:
	try:
		return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
	except jwt.PyJWTError as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials") from exc

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
	token_data = data.copy()
	expires_delta = expires_delta or timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
	expire = datetime.now(timezone.utc) + expires_delta
	token_data.update({"exp": expire, "type": "refresh"})
	return jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_password_reset_token(user_id: UUID) -> str:
	expire = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
	return jwt.encode(
		{"sub": str(user_id), "type": "password_reset", "exp": expire},
		settings.SECRET_KEY,
		algorithm=settings.ALGORITHM,
	)

def decode_typed_token(token: str, expected_type: str) -> dict:
	try:
		payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
	except jwt.PyJWTError as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

	if payload.get("type") != expected_type:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

	return payload

_CODE_ALPHABET = string.ascii_uppercase + string.digits

def generate_verification_code() -> str:
	return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))


def _extract_token(request: Request, credentials: Optional[HTTPAuthorizationCredentials]) -> str:
	if credentials is not None:
		return credentials.credentials
	token = request.cookies.get("access_token")
	if token:
		return token
	raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def get_token_payload(
	request: Request,
	credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
	token = _extract_token(request, credentials)
	return decode_access_token(token)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your session has expired or is invalid. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = get_token_payload(request, credentials)
    subject = payload.get("sub")
    if not subject:
        raise credentials_exception

    try:
        user_id = UUID(subject)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="We couldn't find an account associated with this session. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def require_roles(*roles: str):
	normalized_roles = {role.strip().lower() for role in roles}

	def dependency(current_user: User = Depends(get_current_user)) -> User:
		user_role = (current_user.role or "").strip().lower()
		if user_role not in normalized_roles:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
		return current_user

	return dependency


def require_doctor():
	return require_roles("doctor")


def require_supervisor():
	return require_roles("patient")