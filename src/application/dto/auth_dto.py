from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from ...domain.entities.system_user import UserRole, UserStatus


class LoginRequest(BaseModel):
    """DTO para solicitud de login"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()


class RegisterRequest(BaseModel):
    """DTO para registro de nuevo usuario"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: Optional[UserRole] = UserRole.USER  # Por defecto es USER
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()
    
    @validator('full_name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class TokenResponse(BaseModel):
    """DTO para respuesta de token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # segundos


class RefreshTokenRequest(BaseModel):
    """DTO para solicitud de refresh token"""
    refresh_token: str


class UserResponse(BaseModel):
    """DTO para respuesta de información del usuario"""
    id: str
    email: str
    full_name: str
    role: str
    status: str
    created_at: datetime
    last_login: Optional[datetime]
    permissions: dict
    
    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """DTO para cambio de contraseña"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def passwords_different(cls, v, values):
        if 'current_password' in values and v == values['current_password']:
            raise ValueError("La nueva contraseña debe ser diferente a la actual")
        return v


class UpdateProfileRequest(BaseModel):
    """DTO para actualizar perfil de usuario"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    
    @validator('email')
    def email_lowercase(cls, v):
        if v:
            return v.lower()
        return v


class CreateUserRequest(BaseModel):
    """DTO para crear usuario (solo super admin)"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole
    status: Optional[UserStatus] = UserStatus.ACTIVE
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()


class UpdateUserRequest(BaseModel):
    """DTO para actualizar usuario (solo super admin)"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    
    @validator('email')
    def email_lowercase(cls, v):
        if v:
            return v.lower()
        return v


class LoginResponse(BaseModel):
    """DTO para respuesta completa de login"""
    user: UserResponse
    tokens: TokenResponse
    message: str = "Login exitoso"


class PasswordResetRequest(BaseModel):
    """DTO para solicitud de reseteo de contraseña"""
    email: EmailStr
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()


class PasswordResetConfirm(BaseModel):
    """DTO para confirmar reseteo de contraseña"""
    token: str
    new_password: str = Field(..., min_length=8)