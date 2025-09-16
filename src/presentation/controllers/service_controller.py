from typing import List, Optional, Dict, Any
from ...application.use_cases.service_use_cases import ServiceUseCases
from ...application.dto.service_dto import ServiceDTO, ServiceCreateDTO, ServiceUpdateDTO
import logging

logger = logging.getLogger(__name__)


class ServiceController:
    """Controller for service management endpoints"""
    
    def __init__(self, service_use_cases: ServiceUseCases):
        self._service_use_cases = service_use_cases
    
    async def get_all_services(self, skip: int = 0, limit: int = 100) -> List[ServiceDTO]:
        """Get all services with pagination"""
        try:
            return await self._service_use_cases.get_all_services(skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Controller error getting all services: {e}")
            raise
    
    async def get_active_services(self, skip: int = 0, limit: int = 100) -> List[ServiceDTO]:
        """Get all active services"""
        try:
            return await self._service_use_cases.get_active_services(skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Controller error getting active services: {e}")
            raise
    
    async def get_service_by_id(self, service_id: str) -> Optional[ServiceDTO]:
        """Get service by ID"""
        try:
            return await self._service_use_cases.get_service_by_id(service_id)
        except Exception as e:
            logger.error(f"Controller error getting service {service_id}: {e}")
            raise
    
    async def search_services_by_name(self, name: str, skip: int = 0, limit: int = 50) -> List[ServiceDTO]:
        """Search services by name"""
        try:
            return await self._service_use_cases.search_services_by_name(name, skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Controller error searching services by name '{name}': {e}")
            raise
    
    async def get_services_by_type(self, service_type: str, skip: int = 0, limit: int = 50) -> List[ServiceDTO]:
        """Get services by type"""
        try:
            return await self._service_use_cases.get_services_by_type(service_type, skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Controller error getting services by type '{service_type}': {e}")
            raise
    
    async def create_service(self, service_data: ServiceCreateDTO) -> ServiceDTO:
        """Create a new service"""
        try:
            return await self._service_use_cases.create_service(service_data)
        except Exception as e:
            logger.error(f"Controller error creating service: {e}")
            raise
    
    async def update_service(self, service_id: str, service_data: ServiceUpdateDTO) -> Optional[ServiceDTO]:
        """Update existing service"""
        try:
            return await self._service_use_cases.update_service(service_id, service_data)
        except Exception as e:
            logger.error(f"Controller error updating service {service_id}: {e}")
            raise
    
    async def delete_service(self, service_id: str) -> bool:
        """Delete service by ID"""
        try:
            return await self._service_use_cases.delete_service(service_id)
        except Exception as e:
            logger.error(f"Controller error deleting service {service_id}: {e}")
            raise
    
    async def activate_service(self, service_id: str) -> Optional[ServiceDTO]:
        """Activate service"""
        try:
            return await self._service_use_cases.activate_service(service_id)
        except Exception as e:
            logger.error(f"Controller error activating service {service_id}: {e}")
            raise
    
    async def deactivate_service(self, service_id: str) -> Optional[ServiceDTO]:
        """Deactivate service"""
        try:
            return await self._service_use_cases.deactivate_service(service_id)
        except Exception as e:
            logger.error(f"Controller error deactivating service {service_id}: {e}")
            raise
    
    async def get_services_stats(self) -> Dict[str, Any]:
        """Get services statistics summary"""
        try:
            return await self._service_use_cases.get_services_stats()
        except Exception as e:
            logger.error(f"Controller error getting services stats: {e}")
            raise
    
    async def bulk_upload_services(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process bulk upload of services from CSV or JSON file"""
        try:
            return await self._service_use_cases.bulk_upload_services(file_content, filename)
        except Exception as e:
            logger.error(f"Controller error in bulk upload: {e}")
            raise