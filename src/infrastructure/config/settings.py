from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Application
    app_name: str = os.getenv("APP_NAME", "Agenda IA")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Database
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")
    database_name: str = os.getenv("DATABASE_NAME", "Agenda_Ai")

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # API
    api_v1_prefix: str = "/api/v1"

    # CORS
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "*")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # AI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Link Management
    link_base_url: str = os.getenv("LINK_BASE_URL", "http://localhost:8000")
    default_link_expiry_hours: int = int(os.getenv("DEFAULT_LINK_EXPIRY_HOURS", "48"))
    max_link_expiry_hours: int = int(os.getenv("MAX_LINK_EXPIRY_HOURS", "168"))
    
    # Email Configuration (optional)
    smtp_server: Optional[str] = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = "your-email@gmail.com"
    smtp_password: Optional[str] = "your-app-password"
    
    # WhatsApp Configuration (future use)
    whatsapp_token: Optional[str] = "your-whatsapp-token"
    whatsapp_phone_number_id: Optional[str] = "your-phone-number-id"
    
    # Rate Limiting
    max_requests_per_minute: int = 100
    
    # RAG Configuration
    vector_db_path: str = "./chroma_db"
    max_context_length: int = 4000
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Timezone Configuration
    default_timezone: str = "America/Bogota"
    display_timezone: str = "America/Bogota"
    utc_storage: bool = True  # Store in UTC, display in local timezone
    
    # Date/Time Formatting
    datetime_format: str = "%Y-%m-%d %H:%M:%S"
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"
    
    def get_allowed_origins(self) -> List[str]:
        """Get allowed origins as a list"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow extra fields from .env that aren't defined in the model
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()