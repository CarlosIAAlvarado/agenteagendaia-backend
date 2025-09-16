from datetime import datetime, time
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum
from ..value_objects.email import Email
from ..value_objects.phone import Phone


class WeekDay(Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


@dataclass
class WorkingHours:
    day: WeekDay
    start_time: time
    end_time: time
    is_available: bool = True
    
    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")


@dataclass
class Professional:
    id: Optional[str]
    name: str
    email: Email
    phone: Phone
    specialization: str
    working_hours: List[WorkingHours] = field(default_factory=list)
    service_ids: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Professional name must be at least 2 characters long")
        
        if not self.specialization or len(self.specialization.strip()) < 2:
            raise ValueError("Specialization must be at least 2 characters long")
        
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def add_working_hours(self, working_hours: WorkingHours):
        """Add working hours for a specific day"""
        # Remove existing hours for the same day
        self.working_hours = [wh for wh in self.working_hours if wh.day != working_hours.day]
        self.working_hours.append(working_hours)
        self.updated_at = datetime.utcnow()
    
    def remove_working_hours(self, day: WeekDay):
        """Remove working hours for a specific day"""
        self.working_hours = [wh for wh in self.working_hours if wh.day != day]
        self.updated_at = datetime.utcnow()
    
    def add_service(self, service_id: str):
        """Add a service to professional's capabilities"""
        if service_id not in self.service_ids:
            self.service_ids.append(service_id)
            self.updated_at = datetime.utcnow()
    
    def remove_service(self, service_id: str):
        """Remove a service from professional's capabilities"""
        if service_id in self.service_ids:
            self.service_ids.remove(service_id)
            self.updated_at = datetime.utcnow()
    
    def is_available_on_day(self, day: WeekDay) -> bool:
        """Check if professional works on a specific day"""
        return any(wh.day == day and wh.is_available for wh in self.working_hours)
    
    def get_working_hours_for_day(self, day: WeekDay) -> Optional[WorkingHours]:
        """Get working hours for a specific day"""
        for wh in self.working_hours:
            if wh.day == day and wh.is_available:
                return wh
        return None
    
    def activate(self):
        """Activate professional"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate professional"""
        self.is_active = False
        self.updated_at = datetime.utcnow()