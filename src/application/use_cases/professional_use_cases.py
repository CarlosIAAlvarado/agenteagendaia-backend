from typing import List, Optional, Dict, Any
from datetime import datetime, time
from ..dto.professional_dto import (
    ProfessionalResponseDTO, ProfessionalCreateDTO, ProfessionalUpdateDTO, 
    ProfessionalListResponseDTO, ProfessionalFilterDTO, WeekDayDTO
)
from ...domain.entities.professional import Professional, WeekDay, WorkingHours
from ...domain.value_objects.email import Email
from ...domain.value_objects.phone import Phone
from ...domain.repositories.professional_repository import IProfessionalRepository
import logging

logger = logging.getLogger(__name__)


class ProfessionalUseCases:
    """Use cases for professional management"""
    
    def __init__(self, professional_repository: IProfessionalRepository):
        self._professional_repo = professional_repository
    
    async def get_all_professionals(self, skip: int = 0, limit: int = 100) -> ProfessionalListResponseDTO:
        """Get all professionals with pagination"""
        try:
            professionals = await self._professional_repo.get_all(skip=skip, limit=limit)
            total = await self._professional_repo.count_total()
            
            return ProfessionalListResponseDTO(
                professionals=[self._professional_to_dto(professional) for professional in professionals],
                total=total,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error in get_all_professionals use case: {e}")
            raise
    
    async def get_active_professionals(self, skip: int = 0, limit: int = 100) -> ProfessionalListResponseDTO:
        """Get all active professionals"""
        try:
            professionals = await self._professional_repo.get_active_professionals(skip=skip, limit=limit)
            total = await self._professional_repo.count_active()
            
            return ProfessionalListResponseDTO(
                professionals=[self._professional_to_dto(professional) for professional in professionals],
                total=total,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error in get_active_professionals use case: {e}")
            raise
    
    async def get_professional_by_id(self, professional_id: str) -> Optional[ProfessionalResponseDTO]:
        """Get professional by ID"""
        try:
            professional = await self._professional_repo.get_by_id(professional_id)
            return self._professional_to_dto(professional) if professional else None
        except Exception as e:
            logger.error(f"Error in get_professional_by_id use case: {e}")
            raise
    
    async def search_professionals(self, search_term: str, skip: int = 0, limit: int = 50) -> ProfessionalListResponseDTO:
        """Search professionals by name or specialization"""
        try:
            professionals = await self._professional_repo.search_by_name(search_term, skip=skip, limit=limit)
            # For search, we approximate total (this could be improved)
            total = len(professionals)
            
            return ProfessionalListResponseDTO(
                professionals=[self._professional_to_dto(professional) for professional in professionals],
                total=total,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error in search_professionals use case: {e}")
            raise
    
    async def get_professionals_by_service(self, service_id: str) -> List[ProfessionalResponseDTO]:
        """Get professionals who provide a specific service"""
        try:
            professionals = await self._professional_repo.get_by_service_id(service_id)
            return [self._professional_to_dto(professional) for professional in professionals]
        except Exception as e:
            logger.error(f"Error in get_professionals_by_service use case: {e}")
            raise
    
    async def get_professionals_by_specialization(self, specialization: str) -> List[ProfessionalResponseDTO]:
        """Get professionals by specialization"""
        try:
            professionals = await self._professional_repo.get_by_specialization(specialization)
            return [self._professional_to_dto(professional) for professional in professionals]
        except Exception as e:
            logger.error(f"Error in get_professionals_by_specialization use case: {e}")
            raise
    
    async def get_available_professionals(self, day: str) -> List[ProfessionalResponseDTO]:
        """Get professionals available on a specific day"""
        try:
            # Convert string to WeekDay enum
            try:
                week_day = WeekDay(day.lower())
            except ValueError:
                raise ValueError(f"Invalid day: {day}")
            
            professionals = await self._professional_repo.get_available_on_day(week_day)
            return [self._professional_to_dto(professional) for professional in professionals]
        except Exception as e:
            logger.error(f"Error in get_available_professionals use case: {e}")
            raise
    
    async def create_professional(self, professional_data: ProfessionalCreateDTO) -> ProfessionalResponseDTO:
        """Create a new professional"""
        try:
            # Create value objects
            email = Email(professional_data.email)
            phone = Phone(professional_data.phone)
            
            # Check if professional with same email or phone exists
            existing_by_email = await self._professional_repo.get_by_email(email)
            if existing_by_email:
                raise ValueError(f"Professional with email '{professional_data.email}' already exists")
            
            existing_by_phone = await self._professional_repo.get_by_phone(phone)
            if existing_by_phone:
                raise ValueError(f"Professional with phone '{professional_data.phone}' already exists")
            
            # Convert working hours
            working_hours = []
            for wh_dto in professional_data.working_hours:
                working_hours.append(WorkingHours(
                    day=WeekDay(wh_dto.day.value),
                    start_time=time.fromisoformat(wh_dto.start_time),
                    end_time=time.fromisoformat(wh_dto.end_time),
                    is_available=wh_dto.is_available
                ))
            
            # Create professional entity
            professional = Professional(
                id=None,
                name=professional_data.name,
                email=email,
                phone=phone,
                specialization=professional_data.specialization,
                working_hours=working_hours,
                service_ids=professional_data.service_ids.copy(),
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Save to repository
            created_professional = await self._professional_repo.create(professional)
            return self._professional_to_dto(created_professional)
            
        except Exception as e:
            logger.error(f"Error in create_professional use case: {e}")
            raise
    
    async def update_professional(self, professional_id: str, professional_data: ProfessionalUpdateDTO) -> Optional[ProfessionalResponseDTO]:
        """Update existing professional"""
        try:
            # Get existing professional
            existing = await self._professional_repo.get_by_id(professional_id)
            if not existing:
                return None
            
            # Update fields if provided
            if professional_data.name is not None:
                existing.name = professional_data.name
            
            if professional_data.email is not None:
                new_email = Email(professional_data.email)
                # Check if another professional has this email
                other_with_email = await self._professional_repo.get_by_email(new_email)
                if other_with_email and other_with_email.id != professional_id:
                    raise ValueError(f"Another professional with email '{professional_data.email}' already exists")
                existing.email = new_email
            
            if professional_data.phone is not None:
                new_phone = Phone(professional_data.phone)
                # Check if another professional has this phone
                other_with_phone = await self._professional_repo.get_by_phone(new_phone)
                if other_with_phone and other_with_phone.id != professional_id:
                    raise ValueError(f"Another professional with phone '{professional_data.phone}' already exists")
                existing.phone = new_phone
            
            if professional_data.specialization is not None:
                existing.specialization = professional_data.specialization
            
            if professional_data.working_hours is not None:
                working_hours = []
                for wh_dto in professional_data.working_hours:
                    working_hours.append(WorkingHours(
                        day=WeekDay(wh_dto.day.value),
                        start_time=time.fromisoformat(wh_dto.start_time),
                        end_time=time.fromisoformat(wh_dto.end_time),
                        is_available=wh_dto.is_available
                    ))
                existing.working_hours = working_hours
            
            if professional_data.service_ids is not None:
                existing.service_ids = professional_data.service_ids.copy()
            
            existing.updated_at = datetime.utcnow()
            
            # Update in repository
            updated_professional = await self._professional_repo.update(existing)
            return self._professional_to_dto(updated_professional)
            
        except Exception as e:
            logger.error(f"Error in update_professional use case: {e}")
            raise
    
    async def delete_professional(self, professional_id: str) -> bool:
        """Delete professional by ID"""
        try:
            return await self._professional_repo.delete(professional_id)
        except Exception as e:
            logger.error(f"Error in delete_professional use case: {e}")
            raise
    
    async def activate_professional(self, professional_id: str) -> Optional[ProfessionalResponseDTO]:
        """Activate professional"""
        try:
            professional = await self._professional_repo.get_by_id(professional_id)
            if not professional:
                return None
            
            professional.activate()
            updated_professional = await self._professional_repo.update(professional)
            return self._professional_to_dto(updated_professional)
            
        except Exception as e:
            logger.error(f"Error in activate_professional use case: {e}")
            raise
    
    async def deactivate_professional(self, professional_id: str) -> Optional[ProfessionalResponseDTO]:
        """Deactivate professional"""
        try:
            professional = await self._professional_repo.get_by_id(professional_id)
            if not professional:
                return None
            
            professional.deactivate()
            updated_professional = await self._professional_repo.update(professional)
            return self._professional_to_dto(updated_professional)
            
        except Exception as e:
            logger.error(f"Error in deactivate_professional use case: {e}")
            raise
    
    async def add_service_to_professional(self, professional_id: str, service_id: str) -> Optional[ProfessionalResponseDTO]:
        """Add service to professional"""
        try:
            professional = await self._professional_repo.get_by_id(professional_id)
            if not professional:
                return None
            
            professional.add_service(service_id)
            updated_professional = await self._professional_repo.update(professional)
            return self._professional_to_dto(updated_professional)
            
        except Exception as e:
            logger.error(f"Error in add_service_to_professional use case: {e}")
            raise
    
    async def remove_service_from_professional(self, professional_id: str, service_id: str) -> Optional[ProfessionalResponseDTO]:
        """Remove service from professional"""
        try:
            professional = await self._professional_repo.get_by_id(professional_id)
            if not professional:
                return None
            
            professional.remove_service(service_id)
            updated_professional = await self._professional_repo.update(professional)
            return self._professional_to_dto(updated_professional)
            
        except Exception as e:
            logger.error(f"Error in remove_service_from_professional use case: {e}")
            raise
    
    async def filter_professionals(self, filters: ProfessionalFilterDTO, skip: int = 0, limit: int = 100) -> ProfessionalListResponseDTO:
        """Filter professionals based on criteria"""
        try:
            professionals = []
            
            # Apply different filters
            if filters.service_id:
                professionals = await self._professional_repo.get_by_service_id(filters.service_id)
            elif filters.specialization:
                professionals = await self._professional_repo.get_by_specialization(filters.specialization)
            elif filters.available_day:
                week_day = WeekDay(filters.available_day.value)
                professionals = await self._professional_repo.get_available_on_day(week_day)
            elif filters.search:
                professionals = await self._professional_repo.search_by_name(filters.search, skip=skip, limit=limit)
            else:
                # No specific filter, get all or active only
                if filters.active_only:
                    professionals = await self._professional_repo.get_active_professionals(skip=skip, limit=limit)
                else:
                    professionals = await self._professional_repo.get_all(skip=skip, limit=limit)
            
            # Apply pagination if not already applied in repo call
            if not filters.search and not filters.service_id and not filters.specialization and not filters.available_day:
                total = await self._professional_repo.count_active() if filters.active_only else await self._professional_repo.count_total()
            else:
                # For filtered results, use actual count
                total = len(professionals)
                professionals = professionals[skip:skip + limit]
            
            return ProfessionalListResponseDTO(
                professionals=[self._professional_to_dto(professional) for professional in professionals],
                total=total,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error in filter_professionals use case: {e}")
            raise
    
    def _professional_to_dto(self, professional: Professional) -> ProfessionalResponseDTO:
        """Convert Professional entity to DTO"""
        working_hours_dto = []
        for wh in professional.working_hours:
            working_hours_dto.append({
                "day": wh.day.value,
                "start_time": wh.start_time.strftime("%H:%M"),
                "end_time": wh.end_time.strftime("%H:%M"),
                "is_available": wh.is_available
            })
        
        return ProfessionalResponseDTO(
            id=professional.id,
            name=professional.name,
            email=professional.email.value,
            phone=professional.phone.value,
            specialization=professional.specialization,
            working_hours=working_hours_dto,
            service_ids=professional.service_ids,
            is_active=professional.is_active,
            created_at=professional.created_at,
            updated_at=professional.updated_at
        )