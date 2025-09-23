from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class AppointmentStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


@dataclass
class Appointment:
    # Required fields first (no defaults)
    user_id: str                    # FK → users._id
    service_id: str                 # FK → services._id  
    
    # Optional fields with defaults
    id: Optional[str] = None        # MongoDB _id
    professional_id: Optional[str] = None  # FK → professionals._id (assigned when scheduled)
    status: AppointmentStatus = AppointmentStatus.DRAFT
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Scheduling and service details (set when appointment is confirmed)
    appointment_date: Optional[datetime] = None  # Date and time of appointment
    duration_minutes: Optional[int] = None       # Service duration
    price: Optional[float] = None                # Service price

    # Resolved reference fields (populated by repository when joining)
    user_name: Optional[str] = None              # User's full name
    user_email: Optional[str] = None             # User's email
    service_name: Optional[str] = None           # Service name
    professional_name: Optional[str] = None      # Professional's full name
    professional_email: Optional[str] = None     # Professional's email
    
    def __post_init__(self):
        if not self.user_id:
            raise ValueError("User ID is required")
        
        if not self.service_id:
            raise ValueError("Service ID is required")
        
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def confirm(self):
        """Confirm the appointment"""
        if self.status == AppointmentStatus.CANCELLED:
            raise ValueError("Cannot confirm a cancelled appointment")
        
        self.status = AppointmentStatus.CONFIRMED
    
    def cancel(self, reason: Optional[str] = None):
        """Cancel the appointment"""
        if self.status == AppointmentStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed appointment")
        
        self.status = AppointmentStatus.CANCELLED
        
        if reason:
            self.notes = f"Cancelled: {reason}" if not self.notes else f"{self.notes}\nCancelled: {reason}"
    
    def complete(self):
        """Mark appointment as completed"""
        if self.status == AppointmentStatus.CANCELLED:
            raise ValueError("Cannot complete a cancelled appointment")
        
        self.status = AppointmentStatus.COMPLETED
    
    def mark_no_show(self):
        """Mark appointment as no show"""
        if self.status == AppointmentStatus.COMPLETED:
            raise ValueError("Cannot mark completed appointment as no show")
        
        if self.status == AppointmentStatus.CANCELLED:
            raise ValueError("Cannot mark cancelled appointment as no show")
        
        self.status = AppointmentStatus.NO_SHOW
    
    def add_notes(self, notes: str):
        """Add notes to the appointment"""
        if not notes:
            return
        
        self.notes = notes if not self.notes else f"{self.notes}\n{notes}"
    
    def can_be_cancelled(self) -> bool:
        """Check if appointment can be cancelled"""
        return self.status not in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]
    
    def can_be_rescheduled(self) -> bool:
        """Check if appointment can be rescheduled"""
        return self.status not in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]