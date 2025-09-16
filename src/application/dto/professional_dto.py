from datetime import datetime, time
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator
from enum import Enum


class WeekDayDTO(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class WorkingHoursDTO(BaseModel):
    """DTO for working hours"""
    day: WeekDayDTO
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    is_available: bool = True
    
    @validator('start_time')
    def validate_start_time(cls, v):
        try:
            time.fromisoformat(v)
        except ValueError:
            raise ValueError('Start time must be in HH:MM format')
        return v
    
    @validator('end_time')
    def validate_end_time(cls, v):
        try:
            time.fromisoformat(v)
        except ValueError:
            raise ValueError('End time must be in HH:MM format')
        return v
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        if 'start_time' in values:
            start = time.fromisoformat(values['start_time'])
            end = time.fromisoformat(v)
            if start >= end:
                raise ValueError('End time must be after start time')
        return v


class ProfessionalCreateDTO(BaseModel):
    """DTO for creating a new professional"""
    name: str
    email: EmailStr
    phone: str
    specialization: str
    working_hours: List[WorkingHoursDTO] = []
    service_ids: List[str] = []
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Professional name must be at least 2 characters long')
        return v.strip()
    
    @validator('specialization')
    def validate_specialization(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Specialization must be at least 2 characters long')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Phone number must be at least 10 characters long')
        return v.strip()


class ProfessionalUpdateDTO(BaseModel):
    """DTO for updating professional information"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    working_hours: Optional[List[WorkingHoursDTO]] = None
    service_ids: Optional[List[str]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or len(v.strip()) < 2):
            raise ValueError('Professional name must be at least 2 characters long')
        return v.strip() if v else None
    
    @validator('specialization')
    def validate_specialization(cls, v):
        if v is not None and (not v or len(v.strip()) < 2):
            raise ValueError('Specialization must be at least 2 characters long')
        return v.strip() if v else None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None and (not v or len(v.strip()) < 10):
            raise ValueError('Phone number must be at least 10 characters long')
        return v.strip() if v else None


class ProfessionalResponseDTO(BaseModel):
    """DTO for professional response data"""
    id: str
    name: str
    email: str
    phone: str
    specialization: str
    working_hours: List[WorkingHoursDTO]
    service_ids: List[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProfessionalListResponseDTO(BaseModel):
    """DTO for paginated professional list response"""
    professionals: List[ProfessionalResponseDTO]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class ProfessionalFilterDTO(BaseModel):
    """DTO for filtering professionals"""
    specialization: Optional[str] = None
    service_id: Optional[str] = None
    available_day: Optional[WeekDayDTO] = None
    search: Optional[str] = None
    active_only: bool = True


class AddServiceToProfessionalDTO(BaseModel):
    """DTO for adding service to professional"""
    service_id: str


class RemoveServiceFromProfessionalDTO(BaseModel):
    """DTO for removing service from professional"""
    service_id: str