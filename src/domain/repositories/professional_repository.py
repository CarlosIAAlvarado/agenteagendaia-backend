from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.professional import Professional, WeekDay
from ..value_objects.email import Email
from ..value_objects.phone import Phone


class IProfessionalRepository(ABC):
    """Interface for Professional repository following Repository pattern"""
    
    @abstractmethod
    async def create(self, professional: Professional) -> Professional:
        """Create a new professional"""
        pass
    
    @abstractmethod
    async def get_by_id(self, professional_id: str) -> Optional[Professional]:
        """Get professional by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[Professional]:
        """Get professional by email"""
        pass
    
    @abstractmethod
    async def get_by_phone(self, phone: Phone) -> Optional[Professional]:
        """Get professional by phone"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Professional]:
        """Get all professionals with pagination"""
        pass
    
    @abstractmethod
    async def get_active_professionals(self, skip: int = 0, limit: int = 100) -> List[Professional]:
        """Get all active professionals"""
        pass
    
    @abstractmethod
    async def get_by_service_id(self, service_id: str) -> List[Professional]:
        """Get professionals who provide a specific service"""
        pass
    
    @abstractmethod
    async def get_by_specialization(self, specialization: str) -> List[Professional]:
        """Get professionals by specialization"""
        pass
    
    @abstractmethod
    async def get_available_on_day(self, day: WeekDay) -> List[Professional]:
        """Get professionals available on a specific day"""
        pass
    
    @abstractmethod
    async def get_by_service_and_day(self, service_id: str, day: WeekDay) -> List[Professional]:
        """Get professionals who provide service and are available on specific day"""
        pass
    
    @abstractmethod
    async def update(self, professional: Professional) -> Professional:
        """Update existing professional"""
        pass
    
    @abstractmethod
    async def delete(self, professional_id: str) -> bool:
        """Delete professional by ID"""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Professional]:
        """Search professionals by name"""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """Check if professional exists by email"""
        pass
    
    @abstractmethod
    async def exists_by_phone(self, phone: Phone) -> bool:
        """Check if professional exists by phone"""
        pass
    
    @abstractmethod
    async def count_total(self) -> int:
        """Count total professionals"""
        pass
    
    @abstractmethod
    async def count_active(self) -> int:
        """Count active professionals"""
        pass
    
    @abstractmethod
    async def count_by_specialization(self, specialization: str) -> int:
        """Count professionals by specialization"""
        pass