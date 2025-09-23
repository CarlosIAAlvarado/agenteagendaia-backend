from fastapi import APIRouter, Depends, status
from typing import Optional

from ..controllers.email_config_controller import EmailConfigController
from ...application.use_cases.email_config_use_cases import EmailConfigUseCases
from ...application.dto.email_config_dto import (
    EmailConfigCreateDTO, EmailConfigUpdateDTO, EmailConfigResponseDTO,
    EmailTestDTO, EmailTestResponseDTO
)
from ...infrastructure.database.repositories.email_config_repository_impl import EmailConfigRepositoryImpl
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-config", tags=["Email Configuration"])


def get_email_config_use_cases() -> EmailConfigUseCases:
    """Dependency to get EmailConfigUseCases instance"""
    email_config_repo = EmailConfigRepositoryImpl()
    return EmailConfigUseCases(email_config_repo)


def get_email_config_controller(
    use_cases: EmailConfigUseCases = Depends(get_email_config_use_cases)
) -> EmailConfigController:
    """Dependency to get EmailConfigController instance"""
    return EmailConfigController(use_cases)


@router.get("/", response_model=Optional[EmailConfigResponseDTO])
async def get_email_config(
    controller: EmailConfigController = Depends(get_email_config_controller)
) -> Optional[EmailConfigResponseDTO]:
    """Get current email configuration"""
    return await controller.get_config()


@router.post("/", response_model=EmailConfigResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_email_config(
    config_data: EmailConfigCreateDTO,
    controller: EmailConfigController = Depends(get_email_config_controller)
) -> EmailConfigResponseDTO:
    """Create new email configuration"""
    return await controller.create_config(config_data)


@router.put("/", response_model=EmailConfigResponseDTO)
async def update_email_config(
    config_data: EmailConfigUpdateDTO,
    controller: EmailConfigController = Depends(get_email_config_controller)
) -> EmailConfigResponseDTO:
    """Update existing email configuration"""
    return await controller.update_config(config_data)


@router.delete("/", status_code=status.HTTP_200_OK)
async def delete_email_config(
    controller: EmailConfigController = Depends(get_email_config_controller)
) -> dict:
    """Delete current email configuration"""
    return await controller.delete_config()


@router.post("/test", response_model=EmailTestResponseDTO)
async def test_email_config(
    test_data: EmailTestDTO,
    controller: EmailConfigController = Depends(get_email_config_controller)
) -> EmailTestResponseDTO:
    """Test email configuration"""
    return await controller.test_email(test_data)