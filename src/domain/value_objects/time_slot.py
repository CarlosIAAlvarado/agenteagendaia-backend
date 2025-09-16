from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
from ...infrastructure.utils.timezone_utils import now_colombia, colombia_to_utc, utc_to_colombia


@dataclass(frozen=True)
class TimeSlot:
    start_time: datetime
    end_time: datetime
    _skip_validation: bool = False
    
    def __post_init__(self):
        if not isinstance(self.start_time, datetime):
            raise TypeError("start_time must be a datetime object")
        
        if not isinstance(self.end_time, datetime):
            raise TypeError("end_time must be a datetime object")
        
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")
        
        # Skip validation for existing appointments loaded from database
        if self._skip_validation:
            return
        
        # Convert to Colombia timezone for comparison
        current_colombia_time = now_colombia()
        start_colombia = utc_to_colombia(self.start_time) if self.start_time.tzinfo else self.start_time
        
        if start_colombia < current_colombia_time:
            raise ValueError("Cannot create time slot in the past")
        
        # Ensure times are in the future (at least 1 hour from now)
        min_time = current_colombia_time + timedelta(hours=1)
        if start_colombia < min_time:
            raise ValueError("Appointment must be scheduled at least 1 hour in advance")
    
    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    @property
    def duration_hours(self) -> float:
        """Get duration in hours"""
        return self.duration_minutes / 60
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """Check if this time slot overlaps with another"""
        return (self.start_time < other.end_time and 
                self.end_time > other.start_time)
    
    def is_adjacent_to(self, other: 'TimeSlot') -> bool:
        """Check if this time slot is adjacent to another"""
        return (self.end_time == other.start_time or 
                self.start_time == other.end_time)
    
    def can_merge_with(self, other: 'TimeSlot') -> bool:
        """Check if this time slot can be merged with another"""
        return self.overlaps_with(other) or self.is_adjacent_to(other)
    
    def merge_with(self, other: 'TimeSlot') -> 'TimeSlot':
        """Merge this time slot with another"""
        if not self.can_merge_with(other):
            raise ValueError("Time slots cannot be merged")
        
        start = min(self.start_time, other.start_time)
        end = max(self.end_time, other.end_time)
        return TimeSlot(start, end)
    
    def split_at(self, split_time: datetime) -> List['TimeSlot']:
        """Split this time slot at a specific time"""
        if split_time <= self.start_time or split_time >= self.end_time:
            raise ValueError("Split time must be within the time slot")
        
        return [
            TimeSlot(self.start_time, split_time),
            TimeSlot(split_time, self.end_time)
        ]
    
    def contains_time(self, time: datetime) -> bool:
        """Check if a specific time is within this slot"""
        return self.start_time <= time < self.end_time
    
    def is_same_day(self) -> bool:
        """Check if start and end time are on the same day"""
        return self.start_time.date() == self.end_time.date()
    
    def __str__(self) -> str:
        return f"{self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TimeSlot):
            return False
        return self.start_time == other.start_time and self.end_time == other.end_time
    
    def __hash__(self) -> int:
        return hash((self.start_time, self.end_time))
    
    @classmethod
    def from_existing(cls, start_time: datetime, end_time: datetime) -> 'TimeSlot':
        """Create a time slot from existing appointment data without validation"""
        return cls(start_time, end_time, _skip_validation=True)
    
    @classmethod
    def create_from_duration(cls, start_time: datetime, duration_minutes: int) -> 'TimeSlot':
        """Create a time slot from start time and duration"""
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        return cls(start_time, end_time)
    
    @classmethod
    def create_daily_slots(cls, date: datetime, start_hour: int, end_hour: int, 
                          slot_duration_minutes: int) -> List['TimeSlot']:
        """Create multiple time slots for a day"""
        if start_hour >= end_hour:
            raise ValueError("Start hour must be before end hour")
        
        if slot_duration_minutes <= 0:
            raise ValueError("Slot duration must be positive")
        
        slots = []
        current_time = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        
        while current_time + timedelta(minutes=slot_duration_minutes) <= end_time:
            slot_end = current_time + timedelta(minutes=slot_duration_minutes)
            try:
                slot = cls(current_time, slot_end)
                slots.append(slot)
            except ValueError:
                # Skip slots in the past
                pass
            current_time = slot_end
        
        return slots