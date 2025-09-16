from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator
from enum import Enum


class ServiceTypeDTO(str, Enum):
    MEDICAL = "medical"
    BEAUTY = "beauty"
    CONSULTATION = "consultation"
    MAINTENANCE = "maintenance"
    OTHER = "other"


class ServiceModeDTO(str, Enum):
    PRESENTIAL = "presential"
    VIRTUAL = "virtual"
    BOTH = "both"


class ServiceCreateDTO(BaseModel):
    """DTO for creating a new service"""
    name: str
    description: str
    duration_minutes: int
    service_type: ServiceTypeDTO
    service_mode: ServiceModeDTO
    category_id: Optional[str] = None
    price: Optional[float] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Service name must be at least 2 characters long')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Description must be at least 5 characters long')
        return v.strip()
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError('Duration must be greater than 0')
        if v > 480:  # 8 hours max
            raise ValueError('Duration cannot exceed 480 minutes (8 hours)')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        return v


class ServiceUpdateDTO(BaseModel):
    """DTO for updating service information"""
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    service_type: Optional[ServiceTypeDTO] = None
    service_mode: Optional[ServiceModeDTO] = None
    category_id: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or len(v.strip()) < 2):
            raise ValueError('Service name must be at least 2 characters long')
        return v.strip() if v else None
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and (not v or len(v.strip()) < 5):
            raise ValueError('Description must be at least 5 characters long')
        return v.strip() if v else None
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Duration must be greater than 0')
            if v > 480:
                raise ValueError('Duration cannot exceed 480 minutes (8 hours)')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        return v


class ServiceResponseDTO(BaseModel):
    """DTO for service response data"""
    id: str
    name: str
    description: str
    duration_minutes: int
    service_type: ServiceTypeDTO
    service_mode: ServiceModeDTO
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    price: Optional[float] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ServiceListResponseDTO(BaseModel):
    """DTO for paginated service list response"""
    services: list[ServiceResponseDTO]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class ServiceFilterDTO(BaseModel):
    """DTO for filtering services"""
    service_type: Optional[ServiceTypeDTO] = None
    service_mode: Optional[ServiceModeDTO] = None
    category_id: Optional[str] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    search: Optional[str] = None
    active_only: bool = True


class ServiceDTO(BaseModel):
    """Data Transfer Object for Service - Compatible with frontend"""
    id: Optional[str] = None
    name: str
    description: str
    duration_minutes: int
    service_type: str  # Use string instead of enum for frontend compatibility
    service_mode: str  # Use string instead of enum for frontend compatibility
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    price: Optional[float] = None
    is_active: bool = True
    created_at: Optional[str] = None  # ISO string format for frontend
    updated_at: Optional[str] = None  # ISO string format for frontend

    class Config:
        from_attributes = True