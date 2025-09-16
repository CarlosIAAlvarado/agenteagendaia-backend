from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, validator
from enum import Enum


class AppointmentStatusDTO(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentModeDTO(str, Enum):
    PRESENTIAL = "presential"
    VIRTUAL = "virtual"


class TimeSlotResponseDTO(BaseModel):
    """DTO for time slot in responses (no future validation)"""
    start_time: datetime
    end_time: datetime
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class TimeSlotDTO(BaseModel):
    """DTO for time slot in requests (with future validation)"""
    start_time: datetime
    end_time: datetime
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('start_time')
    def validate_future_time(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Appointment must be scheduled in the future')
        return v


class AppointmentCreateDTO(BaseModel):
    """DTO for creating a new appointment"""
    user_id: str
    service_id: str
    professional_id: str
    start_time: datetime
    mode: AppointmentModeDTO
    notes: Optional[str] = None
    
    @validator('start_time')
    def validate_future_time(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Appointment must be scheduled in the future')
        return v
    
    @validator('user_id', 'service_id', 'professional_id')
    def validate_ids(cls, v):
        if not v or not v.strip():
            raise ValueError('ID cannot be empty')
        return v.strip()


class AppointmentUpdateDTO(BaseModel):
    """DTO for updating appointment information"""
    start_time: Optional[datetime] = None
    professional_id: Optional[str] = None
    mode: Optional[AppointmentModeDTO] = None
    notes: Optional[str] = None
    
    @validator('start_time')
    def validate_future_time(cls, v):
        if v is not None and v <= datetime.utcnow():
            raise ValueError('Appointment must be scheduled in the future')
        return v
    
    @validator('professional_id')
    def validate_professional_id(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Professional ID cannot be empty')
        return v.strip() if v else None


class AppointmentRescheduleDTO(BaseModel):
    """DTO for rescheduling an appointment"""
    start_time: datetime
    professional_id: Optional[str] = None
    
    @validator('start_time')
    def validate_future_time(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Appointment must be scheduled in the future')
        return v
    
    @validator('professional_id')
    def validate_professional_id(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Professional ID cannot be empty')
        return v.strip() if v else None


class AppointmentCancelDTO(BaseModel):
    """DTO for cancelling an appointment"""
    reason: Optional[str] = None


class AppointmentResponseDTO(BaseModel):
    """DTO for appointment response data"""
    id: str
    user_id: str
    service_id: str
    professional_id: Optional[str] = None
    time_slot: TimeSlotResponseDTO  # Use response DTO without future validation
    mode: Optional[AppointmentModeDTO] = None  # Allow None values
    status: AppointmentStatusDTO
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    # Service information (denormalized)
    service_name: Optional[str] = None
    professional_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    
    class Config:
        from_attributes = True
        # Ensure all fields are included in JSON even when None
        anystr_strip_whitespace = False
        validate_assignment = False


class AppointmentListResponseDTO(BaseModel):
    """DTO for paginated appointment list response"""
    appointments: List[AppointmentResponseDTO]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class AppointmentFilterDTO(BaseModel):
    """DTO for filtering appointments"""
    user_id: Optional[str] = None
    professional_id: Optional[str] = None
    service_id: Optional[str] = None
    status: Optional[AppointmentStatusDTO] = None
    mode: Optional[AppointmentModeDTO] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    upcoming_only: bool = False


class AvailableSlotDTO(BaseModel):
    """DTO for available time slots"""
    start_time: datetime
    end_time: datetime
    professional_id: str
    professional_name: str
    
    class Config:
        from_attributes = True


class AvailabilityRequestDTO(BaseModel):
    """DTO for requesting available slots"""
    service_id: str
    preferred_date: Optional[date] = None
    preferred_professional_id: Optional[str] = None
    mode: Optional[AppointmentModeDTO] = None
    max_days_ahead: Optional[int] = 30
    max_slots: Optional[int] = 10
    
    @validator('max_days_ahead')
    def validate_max_days_ahead(cls, v):
        if v is not None and (v < 1 or v > 90):
            raise ValueError('Max days ahead must be between 1 and 90')
        return v
    
    @validator('max_slots')
    def validate_max_slots(cls, v):
        if v is not None and (v < 1 or v > 50):
            raise ValueError('Max slots must be between 1 and 50')
        return v


class AvailabilityResponseDTO(BaseModel):
    """DTO for availability response"""
    available_slots: List[AvailableSlotDTO]
    requested_date: Optional[date] = None
    service_id: str
    
    class Config:
        from_attributes = True