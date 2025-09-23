from fastapi import APIRouter, Depends, status
from typing import Optional

from ..controllers.company_config_controller import CompanyConfigController
from ...application.use_cases.company_config_use_cases import CompanyConfigUseCases
from ...application.dto.company_config_dto import (
    CompanyConfigCreateDTO, CompanyConfigUpdateDTO, CompanyConfigResponseDTO,
    CompanyContactInfoDTO
)
from ...infrastructure.database.repositories.company_config_repository_impl import CompanyConfigRepositoryImpl
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company-config", tags=["Company Configuration"])


def get_company_config_use_cases() -> CompanyConfigUseCases:
    """Dependency to get CompanyConfigUseCases instance"""
    company_config_repo = CompanyConfigRepositoryImpl()
    return CompanyConfigUseCases(company_config_repo)


def get_company_config_controller(
    use_cases: CompanyConfigUseCases = Depends(get_company_config_use_cases)
) -> CompanyConfigController:
    """Dependency to get CompanyConfigController instance"""
    return CompanyConfigController(use_cases)


@router.get("/", response_model=Optional[CompanyConfigResponseDTO])
async def get_company_config(
    controller: CompanyConfigController = Depends(get_company_config_controller)
) -> Optional[CompanyConfigResponseDTO]:
    """Get current company configuration"""
    return await controller.get_config()


@router.get("/contact-info", response_model=Optional[CompanyContactInfoDTO])
async def get_company_contact_info(
    controller: CompanyConfigController = Depends(get_company_config_controller)
) -> Optional[CompanyContactInfoDTO]:
    """Get public company contact information"""
    return await controller.get_contact_info()


@router.post("/", response_model=CompanyConfigResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_company_config(
    config_data: CompanyConfigCreateDTO,
    controller: CompanyConfigController = Depends(get_company_config_controller)
) -> CompanyConfigResponseDTO:
    """Create new company configuration"""
    return await controller.create_config(config_data)


@router.put("/", response_model=CompanyConfigResponseDTO)
async def update_company_config(
    config_data: CompanyConfigUpdateDTO,
    controller: CompanyConfigController = Depends(get_company_config_controller)
) -> CompanyConfigResponseDTO:
    """Update existing company configuration"""
    return await controller.update_config(config_data)


@router.delete("/", status_code=status.HTTP_200_OK)
async def delete_company_config(
    controller: CompanyConfigController = Depends(get_company_config_controller)
) -> dict:
    """Delete current company configuration"""
    return await controller.delete_config()


@router.post("/initialize", response_model=CompanyConfigResponseDTO, status_code=status.HTTP_201_CREATED)
async def initialize_default_company_config(
    controller: CompanyConfigController = Depends(get_company_config_controller)
) -> CompanyConfigResponseDTO:
    """Initialize default company configuration"""
    return await controller.initialize_default()