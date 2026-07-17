import os
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # App
    APP_NAME: str = "율소프트 견적 시스템"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str

    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, str]] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"
    STATIC_DIR: Path = BASE_DIR / "app" / "static"

    # PDF/WeasyPrint
    WEASYPRINT_GTK_PATH: str = ""

    # External Services (Optional)
    SOLAPI_API_KEY: str = ""
    SOLAPI_API_SECRET: str = ""
    SOLAPI_SENDER_NUMBER: str = ""

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_S3_REGION: str = "ap-northeast-2"
    AWS_S3_ENDPOINT_URL: str = ""

    SENTRY_DSN: str = ""
    PROMETHEUS_METRICS_ENABLED: bool = False


settings = Settings()

# WeasyPrint GTK Path Setup (Windows)
if settings.WEASYPRINT_GTK_PATH and os.name == 'nt':
    os.environ['PATH'] = settings.WEASYPRINT_GTK_PATH + ';' + os.environ['PATH']