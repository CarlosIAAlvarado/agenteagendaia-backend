from datetime import datetime, date, timedelta
from typing import List, Optional
from ..entities.professional import Professional, WeekDay
from ..entities.appointment import Appointment, AppointmentStatus
from ..value_objects.time_slot import TimeSlot
from ..repositories.appointment_repository import IAppointmentRepository
from ..repositories.professional_repository import IProfessionalRepository
import logging

logger = logging.getLogger(__name__)

class AvailabilityDomainService:
    """Domain service for managing availability logic using internal calendar only"""
    
    def __init__(self, appointment_repo: IAppointmentRepository, professional_repo: IProfessionalRepository):
        self._appointment_repo = appointment_repo
        self._professional_repo = professional_repo
    
    async def get_available_slots(self, professional_id: str, target_date: date, 
                                service_duration_minutes: int, slot_duration_minutes: int = 30) -> List[TimeSlot]:
        """Get available time slots for a professional on a specific date"""
        
        # Get professional and validate
        professional = await self._professional_repo.get_by_id(professional_id)
        if not professional or not professional.is_active:
            return []
        
        # Get working hours for the target day
        weekday = WeekDay(target_date.strftime('%A').lower())
        working_hours = professional.get_working_hours_for_day(weekday)
        
        if not working_hours:
            return []
        
        # Create potential time slots based on working hours
        start_datetime = datetime.combine(target_date, working_hours.start_time)
        end_datetime = datetime.combine(target_date, working_hours.end_time)
        
        # Generate all possible slots
        potential_slots = []
        current_time = start_datetime
        
        while current_time + timedelta(minutes=service_duration_minutes) <= end_datetime:
            slot_end = current_time + timedelta(minutes=service_duration_minutes)
            try:
                time_slot = TimeSlot(current_time, slot_end)
                potential_slots.append(time_slot)
            except ValueError:
                # Skip invalid slots (past times)
                pass
            current_time += timedelta(minutes=slot_duration_minutes)
        
        # Get existing appointments for the professional on that date
        existing_appointments = await self._appointment_repo.get_professional_appointments_by_date(
            professional_id, target_date
        )
        
        # Filter out unavailable appointments
        active_appointments = [
            apt for apt in existing_appointments 
            if apt.status not in [AppointmentStatus.CANCELLED]
        ]
        
        # Filter available slots
        available_slots = []
        for slot in potential_slots:
            is_available = True
            for appointment in active_appointments:
                if slot.overlaps_with(appointment.time_slot):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(slot)
        
        return available_slots
    
    async def is_slot_available(self, professional_id: str, time_slot: TimeSlot, 
                              exclude_appointment_id: Optional[str] = None) -> bool:
        """Check if a specific time slot is available for a professional"""
        
        # Get professional and validate
        professional = await self._professional_repo.get_by_id(professional_id)
        if not professional or not professional.is_active:
            return False
        
        # Check if professional works on this day
        weekday = WeekDay(time_slot.start_time.strftime('%A').lower())
        if not professional.is_available_on_day(weekday):
            return False
        
        # Check if slot is within working hours
        working_hours = professional.get_working_hours_for_day(weekday)
        if not working_hours:
            return False
        
        slot_start_time = time_slot.start_time.time()
        slot_end_time = time_slot.end_time.time()
        
        if not (working_hours.start_time <= slot_start_time and slot_end_time <= working_hours.end_time):
            return False
        
        # Check for conflicts with existing appointments
        if await self._appointment_repo.exists_conflict(professional_id, time_slot, exclude_appointment_id):
            return False
        
        # Check daily appointment limit (8 appointments per day per professional)
        appointment_date = time_slot.start_time.date()
        daily_count = await self._appointment_repo.count_by_professional_and_date(professional_id, appointment_date)
        
        # If we're excluding an appointment (for rescheduling), don't count it against the limit
        if exclude_appointment_id is None and daily_count >= 8:
            return False
            
        return True
    
    async def find_next_available_slots(self, professional_id: Optional[str] = None, service_duration_minutes: int = 30, 
                                      start_date: Optional[date] = None, max_days_ahead: int = 30, 
                                      max_slots: int = 10) -> List[TimeSlot]:
        """Find next available slots for a professional (or any professional if None) starting from a date"""
        
        if start_date is None:
            start_date = date.today()
        
        available_slots = []
        current_date = start_date
        days_checked = 0
        
        # If no specific professional, get slots from all active professionals
        if professional_id is None:
            professionals = await self._professional_repo.get_active_professionals()
            
            while len(available_slots) < max_slots and days_checked < max_days_ahead:
                for professional in professionals:
                    if len(available_slots) >= max_slots:
                        break
                    
                    daily_slots = await self.get_available_slots(
                        professional.id, current_date, service_duration_minutes
                    )
                    
                    # Create enriched slots with professional info
                    for slot in daily_slots:
                        # Create a new slot object with professional information
                        enriched_slot = TimeSlot(slot.start_time, slot.end_time)
                        # Use object.__setattr__ to bypass the frozen nature for these specific attributes
                        object.__setattr__(enriched_slot, 'professional_id', professional.id)
                        object.__setattr__(enriched_slot, 'professional', professional.name)
                        object.__setattr__(enriched_slot, 'source', 'internal_calendar')
                        available_slots.append(enriched_slot)
                
                current_date += timedelta(days=1)
                days_checked += 1
        else:
            # Logic for specific professional
            while len(available_slots) < max_slots and days_checked < max_days_ahead:
                daily_slots = await self.get_available_slots(
                    professional_id, current_date, service_duration_minutes
                )
                
                # Add source information to slots
                for slot in daily_slots:
                    object.__setattr__(slot, 'source', 'internal_calendar')
                
                available_slots.extend(daily_slots)
                current_date += timedelta(days=1)
                days_checked += 1
        
        # Sort by start time and return limited results
        available_slots.sort(key=lambda slot: slot.start_time)
        return available_slots[:max_slots]
    
    async def find_professionals_available_at_time(self, service_id: str, time_slot: TimeSlot) -> List[Professional]:
        """Find all professionals available for a service at a specific time"""
        
        # Get professionals who provide this service
        professionals = await self._professional_repo.get_by_service_id(service_id)
        
        available_professionals = []
        
        for professional in professionals:
            if await self.is_slot_available(professional.id, time_slot):
                available_professionals.append(professional)
        
        return available_professionals
    
    async def suggest_alternative_slots(self, professional_id: str, requested_slot: TimeSlot, 
                                      service_duration_minutes: int, alternatives_count: int = 3) -> List[TimeSlot]:
        """Suggest alternative slots when requested slot is not available"""
        
        # Try same day first
        same_day_slots = await self.get_available_slots(
            professional_id, 
            requested_slot.start_time.date(), 
            service_duration_minutes
        )
        
        # Filter out slots that are too close to requested time
        filtered_slots = [
            slot for slot in same_day_slots
            if abs((slot.start_time - requested_slot.start_time).total_seconds()) > 1800  # 30 minutes difference
        ]
        
        if len(filtered_slots) >= alternatives_count:
            return filtered_slots[:alternatives_count]
        
        # If not enough alternatives on same day, look at next few days
        next_slots = await self.find_next_available_slots(
            professional_id, 
            service_duration_minutes,
            requested_slot.start_time.date() + timedelta(days=1),
            max_days_ahead=7,
            max_slots=alternatives_count - len(filtered_slots)
        )
        
        filtered_slots.extend(next_slots)
        return filtered_slots[:alternatives_count]
    
    async def get_professional_schedule(self, professional_id: str, target_date: date) -> dict:
        """Get complete schedule for a professional on a specific date"""
        
        professional = await self._professional_repo.get_by_id(professional_id)
        if not professional:
            return {}
        
        # Get working hours
        weekday = WeekDay(target_date.strftime('%A').lower())
        working_hours = professional.get_working_hours_for_day(weekday)
        
        # Get appointments
        appointments = await self._appointment_repo.get_professional_appointments_by_date(
            professional_id, target_date
        )
        
        active_appointments = [
            apt for apt in appointments 
            if apt.status not in [AppointmentStatus.CANCELLED]
        ]
        
        return {
            "date": target_date,
            "working_hours": working_hours,
            "appointments": active_appointments,
            "is_working_day": working_hours is not None
        }