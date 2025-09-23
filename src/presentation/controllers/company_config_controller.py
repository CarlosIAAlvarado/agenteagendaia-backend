from fastapi import HTTPException, status
from typing import Optional

from ...application.use_cases.company_config_use_cases import CompanyConfigUseCases
from ...application.dto.company_config_dto import (
    CompanyConfigCreateDTO, CompanyConfigUpdateDTO, CompanyConfigResponseDTO,
    CompanyContactInfoDTO
)
import logging

logger = logging.getLogger(__name__)


class CompanyConfigController:
    """Controller for Company Configuration endpoints"""

    def __init__(self, company_config_use_cases: CompanyConfigUseCases):
        self.company_config_use_cases = company_config_use_cases

    async def get_config(self) -> Optional[CompanyConfigResponseDTO]:
        """Get current company configuration"""
        try:
            config = await self.company_config_use_cases.get_current_config()
            return config

        except Exception as e:
            logger.error(f"Error getting company config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving company configuration"
            )

    async def get_contact_info(self) -> Optional[CompanyContactInfoDTO]:
        """Get public company contact information"""
        try:
            contact_info = await self.company_config_use_cases.get_contact_info()
            return contact_info

        except Exception as e:
            logger.error(f"Error getting company contact info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving company contact information"
            )

    async def create_config(self, config_data: CompanyConfigCreateDTO) -> CompanyConfigResponseDTO:
        """Create new company configuration"""
        try:
            config = await self.company_config_use_cases.create_config(config_data)
            logger.info(f"Company configuration created successfully")
            return config

        except ValueError as e:
            logger.warning(f"Invalid company config data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error creating company config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating company configuration"
            )

    async def update_config(self, config_data: CompanyConfigUpdateDTO) -> CompanyConfigResponseDTO:
        """Update existing company configuration"""
        try:
            config = await self.company_config_use_cases.update_config(config_data)
            logger.info(f"Company configuration updated successfully")
            return config

        except ValueError as e:
            logger.warning(f"Invalid company config update data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error updating company config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating company configuration"
            )

    async def delete_config(self) -> dict:
        """Delete current company configuration"""
        try:
            success = await self.company_config_use_cases.delete_config()

            if success:
                logger.info("Company configuration deleted successfully")
                return {"message": "Company configuration deleted successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No company configuration found to delete"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting company config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting company configuration"
            )

    async def initialize_default(self) -> CompanyConfigResponseDTO:
        """Initialize default company configuration"""
        try:
            config = await self.company_config_use_cases.initialize_default_config()
            logger.info("Default company configuration initialized")
            return config

        except Exception as e:
            logger.error(f"Error initializing default company config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error initializing default company configuration"
            )