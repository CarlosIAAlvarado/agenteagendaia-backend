from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, validator


class UserCreateDTO(BaseModel):
    """DTO for creating a new user"""
    name: str
    email: EmailStr
    phone: str
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Phone number must be at least 10 characters long')
        return v.strip()


class UserUpdateDTO(BaseModel):
    """DTO for updating user information"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or len(v.strip()) < 2):
            raise ValueError('Name must be at least 2 characters long')
        return v.strip() if v else None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None and (not v or len(v.strip()) < 10):
            raise ValueError('Phone number must be at least 10 characters long')
        return v.strip() if v else None


class UserResponseDTO(BaseModel):
    """DTO for user response data"""
    id: str
    name: str
    email: str
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserListResponseDTO(BaseModel):
    """DTO for paginated user list response"""
    users: list[UserResponseDTO]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True