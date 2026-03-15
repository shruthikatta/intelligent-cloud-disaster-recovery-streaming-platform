from __future__ import annotations

"""Application settings from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_mode: Literal["mock", "aws"] = Field(default="mock", alias="APP_MODE")
    use_real_aws: bool = Field(default=False, alias="USE_REAL_AWS")
    primary_region: str = Field(default="us-west-2", alias="PRIMARY_REGION")
    dr_region: str = Field(default="us-east-1", alias="DR_REGION")

    enable_sns: bool = Field(default=False, alias="ENABLE_SNS")
    enable_sqs: bool = Field(default=False, alias="ENABLE_SQS")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    jwt_secret: str = Field(default="demo-secret-change-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Database (SQLite local; RDS in AWS)
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/streamvault.db",
        alias="DATABASE_URL",
    )

    # S3 / storage
    s3_bucket: str = Field(default="streamvault-demo-bucket", alias="S3_BUCKET")
    s3_prefix: str = Field(default="videos/", alias="S3_PREFIX")

    # ML
    ml_model_path: str = Field(
        default="services/ml_predictor/models/ed_lstm_demo.keras",
        alias="ML_MODEL_PATH",
    )
    ml_service_url: str = Field(default="http://127.0.0.1:8001", alias="ML_SERVICE_URL")
    ml_use_standalone_service: bool = Field(default=False, alias="ML_USE_STANDALONE_SERVICE")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
