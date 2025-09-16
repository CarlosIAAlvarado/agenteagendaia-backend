from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator, EmailStr


class ChatMessageDTO(BaseModel):
    """DTO for incoming chat message"""
    content: str
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Message content cannot be empty')
        if len(v.strip()) > 2000:
            raise ValueError('Message content too long (max 2000 characters)')
        return v.strip()


class ChatResponseDTO(BaseModel):
    """DTO for AI chat response with tool support"""
    message: str
    conversation_id: str
    intent: str
    confidence: float
    context: Dict[str, Any]
    step: str
    timestamp: str
    suggestions: Optional[List[str]] = None
    
    # Tool-based architecture fields
    tool_used: Optional[str] = None
    tool_type: Optional[str] = None
    tool_data: Optional[Dict[str, Any]] = None
    conversation_type: Optional[str] = "natural"  # "natural" or "tool_based"
    ai_enhanced: Optional[bool] = False
    
    # Interactive form fields for frontend rendering
    display_type: Optional[str] = None  # interactive_form, calendar, service_list, etc.
    form_config: Optional[Dict[str, Any]] = None  # Configuration for interactive elements
    ai_continues_after: Optional[bool] = False  # Whether AI continues after form submission
    
    class Config:
        from_attributes = True


class ConversationCreateDTO(BaseModel):
    """DTO for creating a new conversation"""
    user_id: Optional[str] = None
    initial_message: Optional[str] = None
    channel: str = "web"  # web, api, etc.
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponseDTO(BaseModel):
    """DTO for conversation response"""
    id: str
    user_id: Optional[str]
    status: str
    current_step: str
    context: Dict[str, Any]
    message_count: int
    created_at: str
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_minutes: Optional[float] = None
    
    class Config:
        from_attributes = True


class MessageResponseDTO(BaseModel):
    """DTO for message response"""
    id: str
    conversation_id: str
    role: str
    content: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    entities: Optional[Dict[str, Any]] = None
    created_at: str
    
    class Config:
        from_attributes = True


class ConversationListResponseDTO(BaseModel):
    """DTO for conversation list response"""
    conversations: List[ConversationResponseDTO]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class ConversationAnalyticsDTO(BaseModel):
    """DTO for conversation analytics"""
    period: Dict[str, str]
    total_conversations: int
    by_status: Dict[str, Any]
    generated_at: str
    
    class Config:
        from_attributes = True


class EscalationRequestDTO(BaseModel):
    """DTO for escalation request"""
    reason: str
    priority: Optional[str] = "normal"  # low, normal, high
    contact_info: Optional[str] = None
    
    @validator('reason')
    def validate_reason(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Escalation reason must be at least 5 characters long')
        return v.strip()


class AvailableSlotsRequestDTO(BaseModel):
    """DTO for requesting available slots within conversation"""
    service_id: str
    preferred_date: Optional[str] = None
    preferred_professional_id: Optional[str] = None
    mode: Optional[str] = None
    
    @validator('service_id')
    def validate_service_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Service ID is required')
        return v.strip()


class QuickReplyDTO(BaseModel):
    """DTO for quick reply options"""
    text: str
    value: str
    action: Optional[str] = None  # navigate, select, etc.


class ConversationContextUpdateDTO(BaseModel):
    """DTO for updating conversation context"""
    key: str
    value: Any
    
    @validator('key')
    def validate_key(cls, v):
        if not v or not v.strip():
            raise ValueError('Context key is required')
        return v.strip()


class BulkMessageDTO(BaseModel):
    """DTO for sending bulk messages"""
    message: str
    user_ids: List[str]
    schedule_time: Optional[str] = None
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one user ID is required')
        if len(v) > 100:
            raise ValueError('Maximum 100 users per bulk message')
        return v


class UserRegistrationDTO(BaseModel):
    """DTO for structured user registration from forms"""
    name: str
    email: EmailStr
    phone: str
    conversation_id: str
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Name must be at least 3 characters long')
        if len(v.strip()) > 100:
            raise ValueError('Name too long (max 100 characters)')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Phone number must be at least 10 characters')
        # Remove all non-digits for validation
        digits_only = ''.join(c for c in v if c.isdigit())
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValueError('Phone number must have 7-15 digits')
        return v.strip()


class UserRegistrationResponseDTO(BaseModel):
    """DTO for user registration response"""
    user_id: str
    name: str
    email: str
    phone: str
    success: bool = True
    message: str = "Usuario registrado exitosamente"
    conversation_updated: bool = False


class ConversationSearchDTO(BaseModel):
    """DTO for searching conversations"""
    query: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    intent: Optional[str] = None
    skip: int = 0
    limit: int = 50
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v


class ConversationExportDTO(BaseModel):
    """DTO for exporting conversations"""
    conversation_ids: List[str]
    format: str = "json"  # json, csv, txt
    include_messages: bool = True
    include_context: bool = True
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['json', 'csv', 'txt']:
            raise ValueError('Format must be json, csv, or txt')
        return v


class WebhookConfigDTO(BaseModel):
    """DTO for webhook configuration"""
    url: str
    events: List[str]
    secret: Optional[str] = None
    active: bool = True
    
    @validator('url')
    def validate_url(cls, v):
        if not v or not v.startswith('http'):
            raise ValueError('Valid HTTP URL is required')
        return v
    
    @validator('events')
    def validate_events(cls, v):
        valid_events = [
            'conversation.started',
            'conversation.ended',
            'message.sent',
            'message.received',
            'appointment.created',
            'escalation.requested'
        ]
        for event in v:
            if event not in valid_events:
                raise ValueError(f'Invalid event: {event}')
        return v