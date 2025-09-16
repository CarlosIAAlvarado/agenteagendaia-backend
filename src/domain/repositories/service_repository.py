from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.service import Service, ServiceType, ServiceMode


class IServiceRepository(ABC):
    """Interface for Service repository following Repository pattern"""
    
    @abstractmethod
    async def create(self, service: Service) -> Service:
        """Create a new service"""
        pass
    
    @abstractmethod
    async def get_by_id(self, service_id: str) -> Optional[Service]:
        """Get service by ID"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get all services with pagination"""
        pass
    
    @abstractmethod
    async def get_active_services(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get all active services"""
        pass
    
    @abstractmethod
    async def get_by_type(self, service_type: ServiceType, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get services by type"""
        pass
    
    @abstractmethod
    async def get_by_mode(self, service_mode: ServiceMode, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get services by mode (presential/virtual/both)"""
        pass
    
    @abstractmethod
    async def get_by_duration_range(self, min_duration: int, max_duration: int) -> List[Service]:
        """Get services by duration range"""
        pass
    
    @abstractmethod
    async def get_by_price_range(self, min_price: float, max_price: float) -> List[Service]:
        """Get services by price range"""
        pass
    
    @abstractmethod
    async def update(self, service: Service) -> Service:
        """Update existing service"""
        pass
    
    @abstractmethod
    async def delete(self, service_id: str) -> bool:
        """Delete service by ID"""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Service]:
        """Search services by name"""
        pass
    
    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """Check if service exists by name"""
        pass
    
    @abstractmethod
    async def count_total(self) -> int:
        """Count total services"""
        pass
    
    @abstractmethod
    async def count_active(self) -> int:
        """Count active services"""
        pass
    
    @abstractmethod
    async def count_by_type(self, service_type: ServiceType) -> int:
        """Count services by type"""
        pass