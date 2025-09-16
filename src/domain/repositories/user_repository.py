from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.patient import Patient
from ..value_objects.email import Email
from ..value_objects.phone import Phone


class IUserRepository(ABC):
    """Interface for Patient repository following Repository pattern"""
    
    @abstractmethod
    async def create(self, user: Patient) -> Patient:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[Patient]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[Patient]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_by_phone(self, phone: Phone) -> Optional[Patient]:
        """Get user by phone number"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Get all users with pagination"""
        pass
    
    @abstractmethod
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Get all active users"""
        pass
    
    @abstractmethod
    async def update(self, user: Patient) -> Patient:
        """Update existing user"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """Check if user exists by email"""
        pass
    
    @abstractmethod
    async def exists_by_phone(self, phone: Phone) -> bool:
        """Check if user exists by phone"""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Search users by name"""
        pass
    
    @abstractmethod
    async def count_total(self) -> int:
        """Count total users"""
        pass
    
    @abstractmethod
    async def count_active(self) -> int:
        """Count active users"""
        pass