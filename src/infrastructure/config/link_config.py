"""
Configuration for Link Management System
"""

import os
from typing import Dict, List
from pydantic import BaseModel
from ...application.dto.link_management_dto import LinkAction


class LinkConfiguration(BaseModel):
    """Configuration for the link management system"""
    
    # Base URL for link generation
    BASE_URL: str = os.getenv("LINK_BASE_URL", "https://agenda-ia.example.com")
    
    # Default expiration times (in hours)
    DEFAULT_RESCHEDULE_EXPIRY: int = 48
    DEFAULT_CANCEL_EXPIRY: int = 48
    DEFAULT_CONFIRM_EXPIRY: int = 24
    
    # Maximum expiration time allowed
    MAX_EXPIRY_HOURS: int = 168  # 1 week
    
    # Security settings
    ENABLE_IP_RESTRICTIONS: bool = False
    ENABLE_USER_AGENT_RESTRICTIONS: bool = False
    ENABLE_SECURITY_LOGGING: bool = True
    
    # Rate limiting
    MAX_LINKS_PER_USER_PER_HOUR: int = 10
    MAX_LINKS_PER_APPOINTMENT: int = 5
    
    # Cleanup settings
    AUTO_CLEANUP_ENABLED: bool = True
    CLEANUP_INTERVAL_HOURS: int = 24
    KEEP_EXPIRED_LINKS_DAYS: int = 30
    
    # Allowed actions
    ALLOWED_ACTIONS: List[str] = ["reschedule", "cancel", "confirm"]
    
    # Notification settings
    SEND_EMAIL_NOTIFICATIONS: bool = True
    SEND_SMS_NOTIFICATIONS: bool = False
    
    # Templates for different link actions
    LINK_TEMPLATES: Dict[str, str] = {
        "reschedule": {
            "subject": "Reagenda tu cita - Agenda IA",
            "message": "Puedes reagendar tu cita usando el siguiente enlace: {link_url}"
        },
        "cancel": {
            "subject": "Cancela tu cita - Agenda IA", 
            "message": "Si necesitas cancelar tu cita, puedes hacerlo usando el siguiente enlace: {link_url}"
        },
        "confirm": {
            "subject": "Confirma tu cita - Agenda IA",
            "message": "Por favor confirma tu asistencia usando el siguiente enlace: {link_url}"
        }
    }
    
    # Time restrictions
    MIN_HOURS_BEFORE_APPOINTMENT: int = 2  # Minimum hours before appointment to allow changes
    MAX_RESCHEDULE_ATTEMPTS: int = 3  # Maximum times a user can reschedule the same appointment
    
    # Frontend URLs for redirects
    SUCCESS_REDIRECT_URL: str = "/appointment-success"
    ERROR_REDIRECT_URL: str = "/appointment-error"
    
    @classmethod
    def get_template(cls, action: str, template_type: str = "message") -> str:
        """Get template for a specific action"""
        return cls.LINK_TEMPLATES.get(action, {}).get(template_type, "")
    
    @classmethod
    def get_expiry_hours(cls, action: str) -> int:
        """Get default expiry hours for an action"""
        expiry_map = {
            "reschedule": cls.DEFAULT_RESCHEDULE_EXPIRY,
            "cancel": cls.DEFAULT_CANCEL_EXPIRY,
            "confirm": cls.DEFAULT_CONFIRM_EXPIRY
        }
        return expiry_map.get(action, cls.DEFAULT_RESCHEDULE_EXPIRY)
    
    @classmethod
    def is_action_allowed(cls, action: str) -> bool:
        """Check if an action is allowed"""
        return action in cls.ALLOWED_ACTIONS


# Global configuration instance
link_config = LinkConfiguration()