from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "Agenda IA"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    mongodb_uri: str = "mongodb://localhost:27017"  # Override in .env file
    database_name: str = "Agenda_Ai"
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API
    api_v1_prefix: str = "/api/v1"
    
    # CORS
    allowed_origins: str = "*"  # Allow all origins in development
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # AI Configuration
    openai_api_key: str = "your-openai-api-key-here"  # Override in .env file
    openai_model: str = "gpt-4o-mini"
    
    # Link Management
    link_base_url: str = "http://localhost:8000"
    default_link_expiry_hours: int = 48
    max_link_expiry_hours: int = 168
    
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