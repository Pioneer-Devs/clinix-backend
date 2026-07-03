from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    PASSWORD_RESET_EXPIRE_MINUTES: int = 10
    EMAIL_VERIFY_EXPIRE_MINUTES: int = 15

    AI_ENGINE: str = "mock"
    OLLAMA_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama2"
    OLLAMA_API_KEY: Optional[str] = None

    EMAIL_FROM_EMAIL: str
    EMAIL_FROM_NAME: str
    SMTP_HOST: str 
    SMTP_PORT: int 
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = False
    FRONTEND_URL: str 
    COOKIE_DOMAIN: Optional[str] = None
    COOKIE_SECURE: bool = False



    @field_validator("SMTP_PORT", mode="before")
    @classmethod
    def _coerce_smtp_port(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return 1025
        return v

    @field_validator("SMTP_USE_TLS", "COOKIE_SECURE", mode="before")
    @classmethod
    def _coerce_bool(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return False
        return v

    @field_validator("SMTP_USER", "SMTP_PASSWORD", "COOKIE_DOMAIN", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    model_config = SettingsConfigDict(env_file=str(Path(__file__).resolve().parents[2] / ".env"), extra="ignore")


settings = Settings()