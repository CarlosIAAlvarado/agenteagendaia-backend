"""
DTOs for Link Management System
Handles reschedule and cancellation links sent to users
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime, timedelta
from enum import Enum


class LinkAction(str, Enum):
    """Action types for appointment links"""
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    CONFIRM = "confirm"


class LinkStatus(str, Enum):
    """Status of a link"""
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    INVALID = "invalid"


class GenerateLinkDTO(BaseModel):
    """DTO for generating appointment management links"""
    appointment_id: str
    user_id: str
    action: LinkAction
    expires_in_hours: int = 48
    custom_message: Optional[str] = None
    
    @validator('expires_in_hours')
    def validate_expires_in_hours(cls, v):
        if v < 1 or v > 168:  # Max 1 week
            raise ValueError('Expiration must be between 1 and 168 hours')
        return v


class AppointmentLinkResponseDTO(BaseModel):
    """Response DTO for generated appointment links"""
    link_id: str
    appointment_id: str
    action: LinkAction
    secure_url: str
    expires_at: datetime
    status: LinkStatus
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ValidateLinkDTO(BaseModel):
    """DTO for link validation"""
    link_token: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class LinkValidationResponseDTO(BaseModel):
    """Response DTO for link validation"""
    is_valid: bool
    link_id: Optional[str] = None
    appointment_id: Optional[str] = None
    action: Optional[LinkAction] = None
    status: LinkStatus
    appointment_details: Optional[Dict[str, Any]] = None
    user_details: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class RescheduleRequestDTO(BaseModel):
    """DTO for rescheduling an appointment via link"""
    link_token: str
    new_date: datetime
    new_time_slot: str
    reason: Optional[str] = None
    preferred_professional_id: Optional[str] = None
    
    @validator('new_date')
    def validate_new_date(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('New date must be in the future')
        return v


class CancelRequestDTO(BaseModel):
    """DTO for cancelling an appointment via link"""
    link_token: str
    reason: Optional[str] = None
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None
    
    @validator('feedback_rating')
    def validate_feedback_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class LinkActionResponseDTO(BaseModel):
    """Response DTO for link actions (reschedule/cancel)"""
    success: bool
    message: str
    appointment_id: str
    action: LinkAction
    new_appointment_id: Optional[str] = None  # For reschedule
    new_appointment_details: Optional[Dict[str, Any]] = None
    confirmation_code: Optional[str] = None
    follow_up_required: bool = False
    next_steps: List[str] = []


class BulkLinkGenerationDTO(BaseModel):
    """DTO for generating multiple links at once"""
    appointment_ids: List[str]
    actions: List[LinkAction]
    expires_in_hours: int = 48
    custom_template: Optional[str] = None
    send_notifications: bool = True
    
    @validator('appointment_ids')
    def validate_appointment_ids(cls, v):
        if len(v) == 0 or len(v) > 50:
            raise ValueError('Must provide 1-50 appointment IDs')
        return v


class BulkLinkResponseDTO(BaseModel):
    """Response DTO for bulk link generation"""
    total_processed: int
    successful_links: int
    failed_links: int
    links: List[AppointmentLinkResponseDTO]
    errors: List[Dict[str, Any]] = []
    processing_time_ms: int


class LinkAnalyticsDTO(BaseModel):
    """DTO for link usage analytics"""
    total_links_generated: int
    total_links_used: int
    total_links_expired: int
    usage_rate: float
    action_breakdown: Dict[str, int]
    popular_time_slots: List[Dict[str, Any]]
    cancellation_reasons: Dict[str, int]
    reschedule_patterns: Dict[str, int]
    user_engagement_metrics: Dict[str, Any]
    generated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class LinkSecurityLogDTO(BaseModel):
    """DTO for link security events"""
    link_id: str
    event_type: Literal["accessed", "validated", "used", "suspicious"]
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class LinkConfigurationDTO(BaseModel):
    """DTO for link system configuration"""
    base_url: str
    default_expiration_hours: int = 48
    max_expiration_hours: int = 168
    enable_tracking: bool = True
    require_confirmation: bool = False
    allowed_actions: List[LinkAction] = [LinkAction.RESCHEDULE, LinkAction.CANCEL]
    security_settings: Dict[str, Any] = {}
    notification_templates: Dict[str, str] = {}


class LinkDashboardDTO(BaseModel):
    """DTO for link management dashboard"""
    overview: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    security_alerts: List[Dict[str, Any]]
    system_health: Dict[str, str]
    period_start: datetime
    period_end: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }