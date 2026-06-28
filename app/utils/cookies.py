from fastapi import Response

from app.core.config import settings

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def set_auth_cookies(
	response: Response,
	access_token: str,
	refresh_token: str,
) -> None:
	samesite_policy = "none" if settings.COOKIE_SECURE else "lax"

	response.set_cookie(
		key=ACCESS_COOKIE,
		value=access_token,
		httponly=True,
		secure=settings.COOKIE_SECURE,
		samesite=samesite_policy,
		domain=settings.COOKIE_DOMAIN,
		path="/",
		max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
	)
	response.set_cookie(
		key=REFRESH_COOKIE,
		value=refresh_token,
		httponly=True,
		secure=settings.COOKIE_SECURE,
		samesite=samesite_policy,
		domain=settings.COOKIE_DOMAIN,
		path="/api/v1/auth",  # only sent to auth endpoints
		max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
	)


def clear_auth_cookies(response: Response) -> None:
	"""Remove both auth cookies."""
	samesite_policy = "none" if settings.COOKIE_SECURE else "lax"

	response.delete_cookie(
		key=ACCESS_COOKIE,
		httponly=True,
		secure=settings.COOKIE_SECURE,
		samesite=samesite_policy,
		domain=settings.COOKIE_DOMAIN,
		path="/",
	)
	response.delete_cookie(
		key=REFRESH_COOKIE,
		httponly=True,
		secure=settings.COOKIE_SECURE,
		samesite=samesite_policy,
		domain=settings.COOKIE_DOMAIN,
		path="/api/v1/auth",
	)