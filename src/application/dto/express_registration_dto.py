from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator, EmailStr
import re


class ExpressRegistrationDTO(BaseModel):
    """DTO for express user registration (3 fields as specified in PDF)"""
    name: str
    email: EmailStr
    phone: str
    
    # Optional fields for enhanced functionality
    accept_privacy_policy: bool = True
    preferred_communication_channel: str = "email"  # email, sms, whatsapp
    conversation_id: Optional[str] = None  # Link to current conversation
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        if len(v.strip()) > 100:
            raise ValueError('El nombre no puede exceder 100 caracteres')
        # Check if name contains only letters, spaces, and common characters
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-]+$', v.strip()):
            raise ValueError('El nombre solo puede contener letras, espacios y caracteres básicos')
        return v.strip().title()  # Capitalize properly
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v or len(v.strip()) < 8:
            raise ValueError('El teléfono debe tener al menos 8 dígitos')
        
        # Clean phone number - remove spaces, dashes, parentheses
        cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', v.strip())
        
        # Check if it contains only numbers after cleaning
        if not cleaned_phone.isdigit():
            raise ValueError('El teléfono debe contener solo números')
        
        # Check length after cleaning
        if len(cleaned_phone) < 8 or len(cleaned_phone) > 15:
            raise ValueError('El teléfono debe tener entre 8 y 15 dígitos')
        
        return cleaned_phone
    
    @validator('preferred_communication_channel')
    def validate_communication_channel(cls, v):
        valid_channels = ['email', 'sms', 'whatsapp']
        if v not in valid_channels:
            raise ValueError(f'Canal de comunicación debe ser uno de: {", ".join(valid_channels)}')
        return v
    
    @validator('accept_privacy_policy')
    def validate_privacy_policy(cls, v):
        if not v:
            raise ValueError('Debe aceptar la política de privacidad para continuar')
        return v


class ExpressRegistrationResponseDTO(BaseModel):
    """DTO for express registration response"""
    user_id: str
    name: str
    email: str
    phone: str
    is_new_user: bool
    verification_required: bool = False
    verification_method: Optional[str] = None  # 'email' or 'sms'
    
    # Privacy and communication preferences
    privacy_policy_accepted: bool
    preferred_communication_channel: str
    created_at: str
    
    # Integration with conversation flow
    conversation_id: Optional[str] = None
    next_step: str = "service_selection"  # Next step in conversation flow
    welcome_message: str = "¡Registro exitoso! Ahora puedes continuar con tu agendamiento."
    
    class Config:
        from_attributes = True


class ExpressRegistrationValidationDTO(BaseModel):
    """DTO for validating registration data before submission"""
    name: str
    email: str
    phone: str
    
    class Config:
        from_attributes = True


class QuickRegistrationFormDTO(BaseModel):
    """DTO for rendering the quick registration form"""
    title: str = "Registro Rápido"
    description: str = "Para continuar, necesitamos algunos datos básicos:"
    fields: List[Dict[str, Any]] = [
        {
            "name": "name",
            "label": "Nombre completo",
            "type": "text",
            "placeholder": "Ej: Juan Pérez",
            "required": True,
            "validation": "Mínimo 2 caracteres"
        },
        {
            "name": "email",
            "label": "Correo electrónico",
            "type": "email",
            "placeholder": "Ej: juan@email.com",
            "required": True,
            "validation": "Debe ser un correo válido"
        },
        {
            "name": "phone",
            "label": "Teléfono celular",
            "type": "tel",
            "placeholder": "Ej: 3001234567",
            "required": True,
            "validation": "8-15 dígitos"
        }
    ]
    privacy_notice: str = "Al registrarte, aceptas nuestra política de privacidad y el uso de tus datos para el agendamiento de citas."
    communication_options: List[Dict[str, str]] = [
        {"value": "email", "label": "Correo electrónico"},
        {"value": "sms", "label": "SMS"},
        {"value": "whatsapp", "label": "WhatsApp"}
    ]
    submit_button_text: str = "Continuar con el agendamiento"
    
    class Config:
        from_attributes = True


class ExpressRegistrationUpdateDTO(BaseModel):
    """DTO for updating express registration preferences"""
    user_id: str
    preferred_communication_channel: Optional[str] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    whatsapp_notifications: Optional[bool] = None
    
    @validator('preferred_communication_channel')
    def validate_communication_channel(cls, v):
        if v is not None:
            valid_channels = ['email', 'sms', 'whatsapp']
            if v not in valid_channels:
                raise ValueError(f'Canal de comunicación debe ser uno de: {", ".join(valid_channels)}')
        return v


class ExpressRegistrationStatsDTO(BaseModel):
    """DTO for express registration statistics"""
    total_registrations: int
    today_registrations: int
    week_registrations: int
    month_registrations: int
    
    # Conversion metrics
    conversion_rate: float  # % of conversations that resulted in registration
    average_form_completion_time: float  # in seconds
    
    # Channel preferences
    preferred_channels: Dict[str, int] = {
        "email": 0,
        "sms": 0,
        "whatsapp": 0
    }
    
    # User engagement
    verified_users: int
    active_users: int  # Users who made at least one appointment
    
    generated_at: str
    
    class Config:
        from_attributes = True