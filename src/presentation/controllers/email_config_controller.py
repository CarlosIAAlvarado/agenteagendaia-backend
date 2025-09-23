from fastapi import HTTPException, status
from typing import Optional

from ...application.use_cases.email_config_use_cases import EmailConfigUseCases
from ...application.dto.email_config_dto import (
    EmailConfigCreateDTO, EmailConfigUpdateDTO, EmailConfigResponseDTO,
    EmailTestDTO, EmailTestResponseDTO
)
import logging

logger = logging.getLogger(__name__)


class EmailConfigController:
    """Controller for Email Configuration endpoints"""

    def __init__(self, email_config_use_cases: EmailConfigUseCases):
        self.email_config_use_cases = email_config_use_cases

    async def get_config(self) -> Optional[EmailConfigResponseDTO]:
        """Get current email configuration"""
        try:
            config = await self.email_config_use_cases.get_current_config()
            return config

        except Exception as e:
            logger.error(f"Error getting email config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving email configuration"
            )

    async def create_config(self, config_data: EmailConfigCreateDTO) -> EmailConfigResponseDTO:
        """Create new email configuration"""
        try:
            config = await self.email_config_use_cases.create_config(config_data)
            logger.info(f"Email configuration created successfully")
            return config

        except ValueError as e:
            logger.warning(f"Invalid email config data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error creating email config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating email configuration"
            )

    async def update_config(self, config_data: EmailConfigUpdateDTO) -> EmailConfigResponseDTO:
        """Update existing email configuration"""
        try:
            config = await self.email_config_use_cases.update_config(config_data)
            logger.info(f"Email configuration updated successfully")
            return config

        except ValueError as e:
            logger.warning(f"Invalid email config update data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error updating email config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating email configuration"
            )

    async def delete_config(self) -> dict:
        """Delete current email configuration"""
        try:
            success = await self.email_config_use_cases.delete_config()

            if success:
                logger.info("Email configuration deleted successfully")
                return {"message": "Email configuration deleted successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No email configuration found to delete"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting email config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting email configuration"
            )

    async def test_email(self, test_data: EmailTestDTO) -> EmailTestResponseDTO:
        """Test email configuration"""
        try:
            result = await self.email_config_use_cases.test_email_connection(test_data)

            if result.success:
                logger.info(f"Email test successful: {test_data.test_type}")
            else:
                logger.warning(f"Email test failed: {result.message}")

            return result

        except Exception as e:
            logger.error(f"Error testing email: {e}")
            return EmailTestResponseDTO(
                success=False,
                message=f"Test failed with error: {str(e)}",
                test_type=test_data.test_type
            )