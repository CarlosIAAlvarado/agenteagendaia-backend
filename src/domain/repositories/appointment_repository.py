from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, date
from ..entities.appointment import Appointment, AppointmentStatus
from ..value_objects.time_slot import TimeSlot


class IAppointmentRepository(ABC):
    """Interface for Appointment repository following Repository pattern"""
    
    @abstractmethod
    async def create(self, appointment: Appointment) -> Appointment:
        """Create a new appointment"""
        pass
    
    @abstractmethod
    async def get_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get all appointments with pagination"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments by user ID"""
        pass
    
    @abstractmethod
    async def get_by_professional_id(self, professional_id: str, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments by professional ID"""
        pass
    
    @abstractmethod
    async def get_by_service_id(self, service_id: str, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments by service ID"""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: AppointmentStatus, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments by status"""
        pass
    
    @abstractmethod
    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Appointment]:
        """Get appointments within date range"""
        pass
    
    @abstractmethod
    async def get_by_date(self, appointment_date: date) -> List[Appointment]:
        """Get appointments for a specific date"""
        pass
    
    @abstractmethod
    async def get_professional_appointments_by_date(self, professional_id: str, appointment_date: date) -> List[Appointment]:
        """Get professional's appointments for a specific date"""
        pass
    
    @abstractmethod
    async def get_user_upcoming_appointments(self, user_id: str) -> List[Appointment]:
        """Get user's upcoming appointments"""
        pass
    
    @abstractmethod
    async def get_professional_upcoming_appointments(self, professional_id: str) -> List[Appointment]:
        """Get professional's upcoming appointments"""
        pass
    
    @abstractmethod
    async def get_overlapping_appointments(self, professional_id: str, time_slot: TimeSlot) -> List[Appointment]:
        """Get appointments that overlap with given time slot for a professional"""
        pass
    
    @abstractmethod
    async def get_appointments_needing_confirmation(self) -> List[Appointment]:
        """Get appointments that need confirmation"""
        pass
    
    @abstractmethod
    async def get_past_due_appointments(self) -> List[Appointment]:
        """Get appointments that are past their scheduled time"""
        pass
    
    @abstractmethod
    async def update(self, appointment: Appointment) -> Appointment:
        """Update existing appointment"""
        pass
    
    @abstractmethod
    async def delete(self, appointment_id: str) -> bool:
        """Delete appointment by ID"""
        pass
    
    @abstractmethod
    async def exists_conflict(self, professional_id: str, time_slot: TimeSlot, exclude_appointment_id: Optional[str] = None) -> bool:
        """Check if there's a scheduling conflict for professional"""
        pass
    
    @abstractmethod
    async def count_total(self) -> int:
        """Count total appointments"""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: AppointmentStatus) -> int:
        """Count appointments by status"""
        pass
    
    @abstractmethod
    async def count_by_user(self, user_id: str) -> int:
        """Count appointments by user"""
        pass
    
    @abstractmethod
    async def count_by_professional(self, professional_id: str) -> int:
        """Count appointments by professional"""
        pass
    
    @abstractmethod
    async def count_by_date_range(self, start_date: datetime, end_date: datetime) -> int:
        """Count appointments within date range"""
        pass
    
    @abstractmethod
    async def count_by_professional_and_date(self, professional_id: str, target_date: date) -> int:
        """Count appointments for a professional on a specific date (excluding cancelled)"""
        pass
    
    @abstractmethod
    async def count_by_service(self, service_id: str) -> int:
        """Count appointments by service"""
        pass
    
    @abstractmethod
    async def get_by_date_range_paginated(self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments within date range with pagination"""
        pass