from typing import Optional
from datetime import datetime

from ..dto.company_config_dto import (
    CompanyConfigCreateDTO, CompanyConfigUpdateDTO, CompanyConfigResponseDTO,
    CompanyContactInfoDTO
)
from ...domain.entities.company_config import CompanyConfig
from ...domain.repositories.company_config_repository import CompanyConfigRepository
from ...domain.value_objects.email import Email
from ...domain.value_objects.phone import Phone
import logging

logger = logging.getLogger(__name__)


class CompanyConfigUseCases:
    """Use cases for company configuration management"""

    def __init__(self, company_config_repository: CompanyConfigRepository):
        self.company_config_repo = company_config_repository

    async def get_current_config(self) -> Optional[CompanyConfigResponseDTO]:
        """Get current company configuration"""
        try:
            config = await self.company_config_repo.get_current_config()
            if not config:
                return None

            return CompanyConfigResponseDTO(
                id=config.id,
                company_name=config.company_name,
                company_address=config.company_address,
                company_phone=config.company_phone.value if config.company_phone else None,
                company_email=config.company_email.value if config.company_email else None,
                company_website=config.company_website,
                company_logo_url=config.company_logo_url,
                business_hours=config.business_hours,
                timezone=config.timezone,
                created_at=config.created_at,
                updated_at=config.updated_at
            )

        except Exception as e:
            logger.error(f"Error getting company config: {e}")
            raise

    async def get_contact_info(self) -> Optional[CompanyContactInfoDTO]:
        """Get public company contact information"""
        try:
            config = await self.company_config_repo.get_current_config()
            if not config:
                return None

            contact_info = config.get_contact_info()
            return CompanyContactInfoDTO(**contact_info)

        except Exception as e:
            logger.error(f"Error getting company contact info: {e}")
            raise

    async def create_config(self, config_dto: CompanyConfigCreateDTO) -> CompanyConfigResponseDTO:
        """Create new company configuration"""
        try:
            # Check if config already exists
            exists = await self.company_config_repo.config_exists()
            if exists:
                # Delete existing config first (only one should exist)
                existing = await self.company_config_repo.get_current_config()
                if existing:
                    await self.company_config_repo.delete_config(existing.id)

            # Parse optional phone
            phone = None
            if config_dto.company_phone:
                try:
                    phone = Phone(config_dto.company_phone)
                except ValueError as e:
                    raise ValueError(f"Invalid phone format: {e}")

            # Parse optional email
            email = None
            if config_dto.company_email:
                try:
                    email = Email(config_dto.company_email)
                except ValueError as e:
                    raise ValueError(f"Invalid email format: {e}")

            # Create new config entity
            config = CompanyConfig(
                id=None,
                company_name=config_dto.company_name,
                company_address=config_dto.company_address,
                company_phone=phone,
                company_email=email,
                company_website=config_dto.company_website,
                company_logo_url=config_dto.company_logo_url,
                business_hours=config_dto.business_hours,
                timezone=config_dto.timezone,
                created_at=datetime.utcnow()
            )

            # Save to repository
            saved_config = await self.company_config_repo.create_config(config)

            return CompanyConfigResponseDTO(
                id=saved_config.id,
                company_name=saved_config.company_name,
                company_address=saved_config.company_address,
                company_phone=saved_config.company_phone.value if saved_config.company_phone else None,
                company_email=saved_config.company_email.value if saved_config.company_email else None,
                company_website=saved_config.company_website,
                company_logo_url=saved_config.company_logo_url,
                business_hours=saved_config.business_hours,
                timezone=saved_config.timezone,
                created_at=saved_config.created_at,
                updated_at=saved_config.updated_at
            )

        except Exception as e:
            logger.error(f"Error creating company config: {e}")
            raise

    async def update_config(self, config_dto: CompanyConfigUpdateDTO) -> CompanyConfigResponseDTO:
        """Update existing company configuration"""
        try:
            # Get current config
            current_config = await self.company_config_repo.get_current_config()
            if not current_config:
                raise ValueError("No company configuration found to update")

            # Update only provided fields
            if config_dto.company_name is not None:
                current_config.company_name = config_dto.company_name

            if config_dto.company_address is not None:
                current_config.company_address = config_dto.company_address

            if config_dto.company_phone is not None:
                if config_dto.company_phone:
                    try:
                        current_config.company_phone = Phone(config_dto.company_phone)
                    except ValueError as e:
                        raise ValueError(f"Invalid phone format: {e}")
                else:
                    current_config.company_phone = None

            if config_dto.company_email is not None:
                if config_dto.company_email:
                    try:
                        current_config.company_email = Email(config_dto.company_email)
                    except ValueError as e:
                        raise ValueError(f"Invalid email format: {e}")
                else:
                    current_config.company_email = None

            if config_dto.company_website is not None:
                current_config.company_website = config_dto.company_website

            if config_dto.company_logo_url is not None:
                current_config.company_logo_url = config_dto.company_logo_url

            if config_dto.business_hours is not None:
                current_config.business_hours = config_dto.business_hours

            if config_dto.timezone is not None:
                current_config.timezone = config_dto.timezone

            current_config.updated_at = datetime.utcnow()

            # Save updated config
            updated_config = await self.company_config_repo.update_config(current_config)

            return CompanyConfigResponseDTO(
                id=updated_config.id,
                company_name=updated_config.company_name,
                company_address=updated_config.company_address,
                company_phone=updated_config.company_phone.value if updated_config.company_phone else None,
                company_email=updated_config.company_email.value if updated_config.company_email else None,
                company_website=updated_config.company_website,
                company_logo_url=updated_config.company_logo_url,
                business_hours=updated_config.business_hours,
                timezone=updated_config.timezone,
                created_at=updated_config.created_at,
                updated_at=updated_config.updated_at
            )

        except Exception as e:
            logger.error(f"Error updating company config: {e}")
            raise

    async def delete_config(self) -> bool:
        """Delete current company configuration"""
        try:
            current_config = await self.company_config_repo.get_current_config()
            if not current_config:
                return False

            return await self.company_config_repo.delete_config(current_config.id)

        except Exception as e:
            logger.error(f"Error deleting company config: {e}")
            raise

    async def initialize_default_config(self) -> CompanyConfigResponseDTO:
        """Initialize default company configuration if none exists"""
        try:
            # Check if config already exists
            existing = await self.company_config_repo.get_current_config()
            if existing:
                return CompanyConfigResponseDTO(
                    id=existing.id,
                    company_name=existing.company_name,
                    company_address=existing.company_address,
                    company_phone=existing.company_phone.value if existing.company_phone else None,
                    company_email=existing.company_email.value if existing.company_email else None,
                    company_website=existing.company_website,
                    company_logo_url=existing.company_logo_url,
                    business_hours=existing.business_hours,
                    timezone=existing.timezone,
                    created_at=existing.created_at,
                    updated_at=existing.updated_at
                )

            # Create default config
            default_dto = CompanyConfigCreateDTO(
                company_name="Agenda IA",
                company_address="",
                company_phone="",
                company_email="automatizacion@vyrtium.com",
                company_website="https://vyrtium.com",
                company_logo_url="",
                business_hours="Lunes a Viernes: 8:00 AM - 6:00 PM",
                timezone="America/Bogota"
            )

            return await self.create_config(default_dto)

        except Exception as e:
            logger.error(f"Error initializing default company config: {e}")
            raise