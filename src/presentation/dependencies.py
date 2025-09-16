from fastapi import Depends
from ..application.use_cases.user_use_cases import UserUseCases
from ..application.use_cases.appointment_use_cases import AppointmentUseCases
from ..infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from ..infrastructure.database.repositories.service_repository_impl import ServiceRepositoryImpl
from ..infrastructure.database.repositories.professional_repository_impl import ProfessionalRepositoryImpl
from ..infrastructure.database.repositories.appointment_repository_impl import AppointmentRepositoryImpl
from ..domain.services.availability_service import AvailabilityDomainService
from .controllers.user_controller import UserController
from .controllers.appointment_controller import AppointmentController


# Repository dependencies
def get_user_repository() -> UserRepositoryImpl:
    """Get user repository instance"""
    return UserRepositoryImpl()


def get_service_repository() -> ServiceRepositoryImpl:
    """Get service repository instance"""
    return ServiceRepositoryImpl()


def get_professional_repository() -> ProfessionalRepositoryImpl:
    """Get professional repository instance"""
    return ProfessionalRepositoryImpl()


def get_appointment_repository() -> AppointmentRepositoryImpl:
    """Get appointment repository instance"""
    return AppointmentRepositoryImpl()


# Domain service dependencies
def get_availability_service(
    appointment_repo: AppointmentRepositoryImpl = Depends(get_appointment_repository),
    professional_repo: ProfessionalRepositoryImpl = Depends(get_professional_repository)
) -> AvailabilityDomainService:
    """Get availability service instance"""
    return AvailabilityDomainService(appointment_repo, professional_repo)


# Use case dependencies
def get_user_use_cases(
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
) -> UserUseCases:
    """Get user use cases instance"""
    return UserUseCases(user_repo)


def get_appointment_use_cases(
    appointment_repo: AppointmentRepositoryImpl = Depends(get_appointment_repository),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    service_repo: ServiceRepositoryImpl = Depends(get_service_repository),
    professional_repo: ProfessionalRepositoryImpl = Depends(get_professional_repository),
    availability_service: AvailabilityDomainService = Depends(get_availability_service)
) -> AppointmentUseCases:
    """Get appointment use cases instance"""
    return AppointmentUseCases(
        appointment_repo,
        user_repo,
        service_repo,
        professional_repo,
        availability_service
    )


# Controller dependencies
def get_user_controller(
    user_use_cases: UserUseCases = Depends(get_user_use_cases)
) -> UserController:
    """Get user controller instance"""
    return UserController(user_use_cases)


def get_appointment_controller(
    appointment_use_cases: AppointmentUseCases = Depends(get_appointment_use_cases)
) -> AppointmentController:
    """Get appointment controller instance"""
    return AppointmentController(appointment_use_cases)