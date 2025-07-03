"""
Configurazione dell'applicazione
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Configurazione dell'applicazione"""

    # App info
    app_name: str = "tl;dv Integration API"
    app_version: str = "1.0.0"
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("development", env="ENVIRONMENT")

    # API Configuration
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_prefix: str = "/api"

    # tl;dv API
    tldv_api_key: str = Field(..., env="TLDV_API_KEY")
    tldv_api_base_url: str = Field("https://pasta.tldv.io/v1alpha1", env="TLDV_API_BASE_URL")
    tldv_timeout: int = Field(30, env="TLDV_TIMEOUT")

    # Firebase
    firebase_credentials_file: str = Field(..., env="FIREBASE_CREDENTIALS_FILE")

    # Redis
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    allowed_origins: List[str] = Field(
        ["http://localhost:3000", "http://127.0.0.1:3000"],
        env="ALLOWED_ORIGINS"
    )

    # Rate limiting
    max_concurrent_downloads: int = Field(5, env="MAX_CONCURRENT_DOWNLOADS")
    max_requests_per_minute: int = Field(100, env="MAX_REQUESTS_PER_MINUTE")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")

    # Storage
    storage_bucket: str = Field("meetings", env="STORAGE_BUCKET")
    max_file_size_mb: int = Field(500, env="MAX_FILE_SIZE_MB")

    class Config:
        env_file = ".env"
        case_sensitive = False

# Istanza globale delle impostazioni
settings = Settings()
