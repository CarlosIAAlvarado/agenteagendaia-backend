from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class ServiceType(Enum):
    MEDICAL = "medical"
    BEAUTY = "beauty"
    CONSULTATION = "consultation"
    MAINTENANCE = "maintenance"
    OTHER = "other"


class ServiceMode(Enum):
    PRESENTIAL = "presential"
    VIRTUAL = "virtual"
    BOTH = "both"


@dataclass
class Service:
    id: Optional[str]
    name: str
    description: str
    duration_minutes: int
    service_type: ServiceType
    service_mode: ServiceMode
    category_id: Optional[str] = None  # Foreign key to Category
    price: Optional[float] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Service name must be at least 2 characters long")
        
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be greater than 0")
        
        if self.duration_minutes > 480:  # 8 hours max
            raise ValueError("Duration cannot exceed 480 minutes (8 hours)")
        
        if self.price is not None and self.price < 0:
            raise ValueError("Price cannot be negative")
        
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def update_service(self, name: Optional[str] = None, description: Optional[str] = None, 
                      duration_minutes: Optional[int] = None, price: Optional[float] = None,
                      category_id: Optional[str] = None):
        """Update service information"""
        if name:
            if len(name.strip()) < 2:
                raise ValueError("Service name must be at least 2 characters long")
            self.name = name.strip()
        
        if description:
            self.description = description.strip()
        
        if duration_minutes:
            if duration_minutes <= 0 or duration_minutes > 480:
                raise ValueError("Duration must be between 1 and 480 minutes")
            self.duration_minutes = duration_minutes
        
        if price is not None:
            if price < 0:
                raise ValueError("Price cannot be negative")
            self.price = price
        
        if category_id is not None:
            self.category_id = category_id
        
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Activate service"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate service"""
        self.is_active = False
        self.updated_at = datetime.utcnow()