from typing import List, Optional, Dict, Any
from ...application.use_cases.professional_use_cases import ProfessionalUseCases
from ...application.dto.professional_dto import (
    ProfessionalResponseDTO, ProfessionalCreateDTO, ProfessionalUpdateDTO,
    ProfessionalListResponseDTO, ProfessionalFilterDTO
)
import logging

logger = logging.getLogger(__name__)


class ProfessionalController:
    """Controller for professional management endpoints"""
    
    def __init__(self, professional_use_cases: ProfessionalUseCases):
        self._professional_use_cases = professional_use_cases
    
    async def get_all_professionals(self, skip: int = 0, limit: int = 100) -> ProfessionalListResponseDTO:
        """Get all professionals with pagination"""
        try:
            return await self._professional_use_cases.get_all_professionals(skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Controller error getting all professionals: {e}")
            raise
    
    async def get_active_professionals(self, skip: int = 0, limit: int = 100) -> ProfessionalListResponseDTO:
        """Get all active professionals"""
        try:
            return await self._professional_use_cases.get_active_professionals(skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Controller error getting active professionals: {e}")
            raise
    
    async def get_professional_by_id(self, professional_id: str) -> Optional[ProfessionalResponseDTO]:
        """Get professional by ID"""
        try:
            return await self._professional_use_cases.get_professional_by_id(professional_id)
        except Exception as e:
            logger.error(f"Controller error getting professional {professional_id}: {e}")
            raise
    
    async def search_professionals(self, search_term: str, skip: int = 0, limit: int = 50) -> ProfessionalListResponseDTO:
        """Search professionals by name or specialization"""
        try:
            return await self._professional_use_cases.search_professionals(search_term, skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Controller error searching professionals with term '{search_term}': {e}")
            raise
    
    async def get_professionals_by_service(self, service_id: str) -> List[ProfessionalResponseDTO]:
        """Get professionals who provide a specific service"""
        try:
            return await self._professional_use_cases.get_professionals_by_service(service_id)
        except Exception as e:
            logger.error(f"Controller error getting professionals by service '{service_id}': {e}")
            raise
    
    async def get_professionals_by_specialization(self, specialization: str) -> List[ProfessionalResponseDTO]:
        """Get professionals by specialization"""
        try:
            return await self._professional_use_cases.get_professionals_by_specialization(specialization)
        except Exception as e:
            logger.error(f"Controller error getting professionals by specialization '{specialization}': {e}")
            raise
    
    async def get_available_professionals(self, day: str) -> List[ProfessionalResponseDTO]:
        """Get professionals available on a specific day"""
        try:
            return await self._professional_use_cases.get_available_professionals(day)
        except Exception as e:
            logger.error(f"Controller error getting available professionals for day '{day}': {e}")
            raise
    
    async def create_professional(self, professional_data: ProfessionalCreateDTO) -> ProfessionalResponseDTO:
        """Create a new professional"""
        try:
            return await self._professional_use_cases.create_professional(professional_data)
        except Exception as e:
            logger.error(f"Controller error creating professional: {e}")
            raise
    
    async def update_professional(self, professional_id: str, professional_data: ProfessionalUpdateDTO) -> Optional[ProfessionalResponseDTO]:
        """Update existing professional"""
        try:
            return await self._professional_use_cases.update_professional(professional_id, professional_data)
        except Exception as e:
            logger.error(f"Controller error updating professional {professional_id}: {e}")
            raise
    
    async def delete_professional(self, professional_id: str) -> bool:
        """Delete professional by ID"""
        try:
            return await self._professional_use_cases.delete_professional(professional_id)
        except Exception as e:
            logger.error(f"Controller error deleting professional {professional_id}: {e}")
            raise
    
    async def activate_professional(self, professional_id: str) -> Optional[ProfessionalResponseDTO]:
        """Activate professional"""
        try:
            return await self._professional_use_cases.activate_professional(professional_id)
        except Exception as e:
            logger.error(f"Controller error activating professional {professional_id}: {e}")
            raise
    
    async def deactivate_professional(self, professional_id: str) -> Optional[ProfessionalResponseDTO]:
        """Deactivate professional"""
        try:
            return await self._professional_use_cases.deactivate_professional(professional_id)
        except Exception as e:
            logger.error(f"Controller error deactivating professional {professional_id}: {e}")
            raise
    
    async def add_service_to_professional(self, professional_id: str, service_id: str) -> Optional[ProfessionalResponseDTO]:
        """Add service to professional"""
        try:
            return await self._professional_use_cases.add_service_to_professional(professional_id, service_id)
        except Exception as e:
            logger.error(f"Controller error adding service {service_id} to professional {professional_id}: {e}")
            raise
    
    async def remove_service_from_professional(self, professional_id: str, service_id: str) -> Optional[ProfessionalResponseDTO]:
        """Remove service from professional"""
        try:
            return await self._professional_use_cases.remove_service_from_professional(professional_id, service_id)
        except Exception as e:
            logger.error(f"Controller error removing service {service_id} from professional {professional_id}: {e}")
            raise
    
    async def filter_professionals(self, filters: ProfessionalFilterDTO, skip: int = 0, limit: int = 100) -> ProfessionalListResponseDTO:
        """Filter professionals based on criteria"""
        try:
            return await self._professional_use_cases.filter_professionals(filters, skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Controller error filtering professionals: {e}")
            raise