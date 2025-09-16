from functools import lru_cache
from typing import Optional
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .database.connection import get_database

# Domain Repository Interfaces
from ..domain.repositories.user_repository import IUserRepository as UserRepository
from ..domain.repositories.service_repository import IServiceRepository as ServiceRepository
from ..domain.repositories.professional_repository import IProfessionalRepository as ProfessionalRepository
from ..domain.repositories.appointment_repository import IAppointmentRepository as AppointmentRepository
from ..domain.repositories.conversation_repository import IConversationRepository as ConversationRepository

# Infrastructure Repository Implementations
from .database.repositories.user_repository_impl import UserRepositoryImpl
from .database.repositories.service_repository_impl import ServiceRepositoryImpl
from .database.repositories.professional_repository_impl import ProfessionalRepositoryImpl
from .database.repositories.appointment_repository_impl import AppointmentRepositoryImpl
from .database.repositories.conversation_repository_impl import ConversationRepositoryImpl
from .repositories.mongo_appointment_link_repository import MongoAppointmentLinkRepository

# Domain Services
from ..domain.services.availability_service import AvailabilityDomainService

# Infrastructure Services
# ELIMINADOS: openai_client y vector_store - NO SE USAN

# Application Use Cases (only importing existing ones)
from ..application.use_cases.user_use_cases import UserUseCases
from ..application.use_cases.service_use_cases import ServiceUseCases
from ..application.use_cases.professional_use_cases import ProfessionalUseCases
from ..application.use_cases.appointment_use_cases import AppointmentUseCases
from ..application.use_cases.conversation_use_cases_v2 import ConversationUseCasesV2

# ELIMINADO: Singleton AI Agent - causaba cache de respuestas idénticas


# Repository Dependencies
async def get_user_repository() -> UserRepository:
    """Get UserRepository instance"""
    from .database.repositories.user_repository_impl import UserRepositoryImpl
    return UserRepositoryImpl()


async def get_service_repository() -> ServiceRepository:
    """Get ServiceRepository instance"""
    from .database.repositories.service_repository_impl import ServiceRepositoryImpl
    return ServiceRepositoryImpl()


async def get_professional_repository() -> ProfessionalRepository:
    """Get ProfessionalRepository instance"""
    from .database.repositories.professional_repository_impl import ProfessionalRepositoryImpl
    return ProfessionalRepositoryImpl()


async def get_appointment_repository() -> AppointmentRepository:
    """Get AppointmentRepository instance"""
    from .database.repositories.appointment_repository_impl import AppointmentRepositoryImpl
    return AppointmentRepositoryImpl()


async def get_conversation_repository() -> ConversationRepository:
    """Get ConversationRepository instance"""
    from .database.repositories.conversation_repository_impl import ConversationRepositoryImpl
    return ConversationRepositoryImpl()


async def get_appointment_link_repository() -> MongoAppointmentLinkRepository:
    """Get AppointmentLinkRepository instance"""
    database = await get_database()
    return MongoAppointmentLinkRepository(database)


# Service Dependencies
def get_availability_service(
    professional_repo: ProfessionalRepository = Depends(get_professional_repository),
    appointment_repo: AppointmentRepository = Depends(get_appointment_repository)
) -> AvailabilityDomainService:
    """Get AvailabilityDomainService instance"""
    return AvailabilityDomainService(professional_repo, appointment_repo)


# AI Dependencies
# ELIMINADAS: get_openai_client y get_rag_service - YA NO SE USAN


async def get_ai_agent():
    """Get AI Agent FRESH instance with ALL tools (NO SINGLETON) - Fixed caching issue"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # CREAR INSTANCIA FRESCA cada vez con herramientas - NO SINGLETON para evitar cache de respuestas
        from .ai.agenda_ia_agent import AgendaIAAgent
        
        # Obtener TODOS los repositorios para herramientas AI COMPLETAS
        user_repo = await get_user_repository()
        conversation_repo = await get_conversation_repository()
        service_repo = await get_service_repository()
        professional_repo = await get_professional_repository()
        appointment_repo = await get_appointment_repository()
        
        # Pasar TODOS los repositorios para inicializar ALL TOOLS incluyendo appointment tool
        fresh_agent = AgendaIAAgent(
            user_repo=user_repo, 
            conversation_repo=conversation_repo,
            service_repo=service_repo,
            professional_repo=professional_repo,
            appointment_repo=appointment_repo
        )
        logger.info("[SUCCESS] Created FRESH AI Agent instance with ALL TOOLS (no caching)")
        return fresh_agent
    except Exception as e:
        logger.error(f"Error initializing AI Agent: {e}")
        return None


# Use Case Dependencies
async def get_user_use_cases(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserUseCases:
    """Get UserUseCases instance"""
    return UserUseCases(user_repo)


async def get_service_use_cases(
    service_repo: ServiceRepository = Depends(get_service_repository)
) -> ServiceUseCases:
    """Get ServiceUseCases instance"""
    return ServiceUseCases(service_repo)


async def get_professional_use_cases(
    professional_repo: ProfessionalRepository = Depends(get_professional_repository)
) -> ProfessionalUseCases:
    """Get ProfessionalUseCases instance"""
    return ProfessionalUseCases(professional_repo)


async def get_appointment_use_cases(
    appointment_repo: AppointmentRepository = Depends(get_appointment_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    service_repo: ServiceRepository = Depends(get_service_repository),
    professional_repo: ProfessionalRepository = Depends(get_professional_repository),
    availability_service: AvailabilityDomainService = Depends(get_availability_service)
) -> AppointmentUseCases:
    """Get AppointmentUseCases instance"""
    return AppointmentUseCases(
        appointment_repo,
        user_repo,
        service_repo,
        professional_repo,
        availability_service
    )



async def get_conversation_use_cases(
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    service_repo: ServiceRepository = Depends(get_service_repository),
    professional_repo: ProfessionalRepository = Depends(get_professional_repository),
    appointment_repo: AppointmentRepository = Depends(get_appointment_repository),
    availability_service: AvailabilityDomainService = Depends(get_availability_service),
    ai_agent = Depends(get_ai_agent)
) -> ConversationUseCasesV2:
    """Get ConversationUseCasesV2 instance with fresh AI Agent"""
    return ConversationUseCasesV2(
        conversation_repo,
        user_repo,
        service_repo,
        professional_repo,
        appointment_repo,
        availability_service,
        ai_agent
    )