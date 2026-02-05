"""
Configuration de l'application - VERSION ULTRA-ROBUSTE
Variables d'environnement et settings
Support upload 5 GB + Tous formats
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Application
    APP_NAME: str = "Bid-Killer Engine"
    APP_VERSION: str = "2.0.0"  # Upgraded !
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/bidkiller"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Anthropic API
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS: int = 8000  # Augmenté pour capturer tous les lots
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_STARTER_PRICE_ID: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_ENTERPRISE_PRICE_ID: str = ""
    
    # File Storage - UPGRADED TO 5 GB !
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024 * 1024  # 5 GB (était 100 MB)
    
    # TOUS les formats acceptés (Universal Support)
    ALLOWED_EXTENSIONS: list = [
        # Documents
        ".pdf", ".docx", ".doc", ".txt", ".md", ".rtf",
        # Archives
        ".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".bz2",
        # Spreadsheets
        ".xlsx", ".xls", ".csv"
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    
    # Email (optionnel pour notifications)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """Récupère les settings (cached)"""
    return Settings()

# Instance globale
settings = get_settings()
