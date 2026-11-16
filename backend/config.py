"""
MedFlow AI - Configuration Module
Manages application settings, clinical thresholds, and environment flags using Pydantic v2 Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "MedFlow AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Network & Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # LLM Settings
    GEMINI_API_KEY: str = ""
    LLM_MODEL_NAME: str = "gemini-2.5-flash"
    
    # Safety & Clinical Thresholds
    CONFIDENCE_THRESHOLD: float = 0.80
    CRITICAL_SEVERITY_THRESHOLD: int = 85
    HIGH_SEVERITY_THRESHOLD: int = 65
    MODERATE_SEVERITY_THRESHOLD: int = 40
    
    # Optimization Engine Bounds
    MAX_ORTOOLS_SOLVER_TIME_SECONDS: float = 2.0
    ENABLE_DETERMINISTIC_NEWS2_OVERRIDE: bool = True


settings = Settings()
