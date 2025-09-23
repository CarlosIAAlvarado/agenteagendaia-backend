from typing import Optional
from datetime import datetime
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..dto.email_config_dto import (
    EmailConfigCreateDTO, EmailConfigUpdateDTO, EmailConfigResponseDTO,
    EmailTestDTO, EmailTestResponseDTO
)
from ...domain.entities.email_config import EmailConfig
from ...domain.repositories.email_config_repository import EmailConfigRepository
from ...domain.value_objects.email import Email
import logging

logger = logging.getLogger(__name__)


class EmailConfigUseCases:
    """Use cases for email configuration management"""

    def __init__(self, email_config_repository: EmailConfigRepository):
        self.email_config_repo = email_config_repository

    async def get_current_config(self) -> Optional[EmailConfigResponseDTO]:
        """Get current email configuration"""
        try:
            config = await self.email_config_repo.get_current_config()
            if not config:
                return None

            return EmailConfigResponseDTO(
                id=config.id,
                smtp_server=config.smtp_server,
                smtp_port=config.smtp_port,
                smtp_username=config.smtp_username,
                smtp_password="***hidden***",  # Never expose password
                email_from_name=config.email_from_name,
                email_from_address=config.email_from_address.value,
                email_enabled=config.email_enabled,
                use_tls=config.use_tls,
                use_ssl=config.use_ssl,
                created_at=config.created_at,
                updated_at=config.updated_at
            )

        except Exception as e:
            logger.error(f"Error getting email config: {e}")
            raise

    async def create_config(self, config_dto: EmailConfigCreateDTO) -> EmailConfigResponseDTO:
        """Create new email configuration"""
        try:
            # Check if config already exists
            exists = await self.email_config_repo.config_exists()
            if exists:
                # Delete existing config first (only one should exist)
                existing = await self.email_config_repo.get_current_config()
                if existing:
                    await self.email_config_repo.delete_config(existing.id)

            # Create new config entity
            config = EmailConfig(
                id=None,
                smtp_server=config_dto.smtp_server,
                smtp_port=config_dto.smtp_port,
                smtp_username=config_dto.smtp_username,
                smtp_password=config_dto.smtp_password,
                email_from_name=config_dto.email_from_name,
                email_from_address=Email(config_dto.email_from_address),
                email_enabled=config_dto.email_enabled,
                use_tls=config_dto.use_tls,
                use_ssl=config_dto.use_ssl,
                created_at=datetime.utcnow()
            )

            # Save to repository
            saved_config = await self.email_config_repo.create_config(config)

            return EmailConfigResponseDTO(
                id=saved_config.id,
                smtp_server=saved_config.smtp_server,
                smtp_port=saved_config.smtp_port,
                smtp_username=saved_config.smtp_username,
                smtp_password="***hidden***",
                email_from_name=saved_config.email_from_name,
                email_from_address=saved_config.email_from_address.value,
                email_enabled=saved_config.email_enabled,
                use_tls=saved_config.use_tls,
                use_ssl=saved_config.use_ssl,
                created_at=saved_config.created_at,
                updated_at=saved_config.updated_at
            )

        except Exception as e:
            logger.error(f"Error creating email config: {e}")
            raise

    async def update_config(self, config_dto: EmailConfigUpdateDTO) -> EmailConfigResponseDTO:
        """Update existing email configuration"""
        try:
            # Get current config
            current_config = await self.email_config_repo.get_current_config()
            if not current_config:
                raise ValueError("No email configuration found to update")

            # Update only provided fields
            if config_dto.smtp_server is not None:
                current_config.smtp_server = config_dto.smtp_server
            if config_dto.smtp_port is not None:
                current_config.smtp_port = config_dto.smtp_port
            if config_dto.smtp_username is not None:
                current_config.smtp_username = config_dto.smtp_username
            if config_dto.smtp_password is not None:
                current_config.smtp_password = config_dto.smtp_password
            if config_dto.email_from_name is not None:
                current_config.email_from_name = config_dto.email_from_name
            if config_dto.email_from_address is not None:
                current_config.email_from_address = Email(config_dto.email_from_address)
            if config_dto.email_enabled is not None:
                current_config.email_enabled = config_dto.email_enabled
            if config_dto.use_tls is not None:
                current_config.use_tls = config_dto.use_tls
            if config_dto.use_ssl is not None:
                current_config.use_ssl = config_dto.use_ssl

            current_config.updated_at = datetime.utcnow()

            # Save updated config
            updated_config = await self.email_config_repo.update_config(current_config)

            return EmailConfigResponseDTO(
                id=updated_config.id,
                smtp_server=updated_config.smtp_server,
                smtp_port=updated_config.smtp_port,
                smtp_username=updated_config.smtp_username,
                smtp_password="***hidden***",
                email_from_name=updated_config.email_from_name,
                email_from_address=updated_config.email_from_address.value,
                email_enabled=updated_config.email_enabled,
                use_tls=updated_config.use_tls,
                use_ssl=updated_config.use_ssl,
                created_at=updated_config.created_at,
                updated_at=updated_config.updated_at
            )

        except Exception as e:
            logger.error(f"Error updating email config: {e}")
            raise

    async def delete_config(self) -> bool:
        """Delete current email configuration"""
        try:
            current_config = await self.email_config_repo.get_current_config()
            if not current_config:
                return False

            return await self.email_config_repo.delete_config(current_config.id)

        except Exception as e:
            logger.error(f"Error deleting email config: {e}")
            raise

    async def test_email_connection(self, test_dto: EmailTestDTO) -> EmailTestResponseDTO:
        """Test email configuration"""
        try:
            # Get current config
            config = await self.email_config_repo.get_current_config()
            if not config:
                return EmailTestResponseDTO(
                    success=False,
                    message="No email configuration found",
                    test_type=test_dto.test_type
                )

            if not config.email_enabled:
                return EmailTestResponseDTO(
                    success=False,
                    message="Email notifications are disabled",
                    test_type=test_dto.test_type
                )

            if test_dto.test_type == "connection":
                # Test SMTP connection only
                result = await self._test_smtp_connection(config)
            else:
                # Test full email sending
                result = await self._test_send_email(config, test_dto.to_email)

            return result

        except Exception as e:
            logger.error(f"Error testing email: {e}")
            return EmailTestResponseDTO(
                success=False,
                message=f"Test failed: {str(e)}",
                test_type=test_dto.test_type
            )

    async def _test_smtp_connection(self, config: EmailConfig) -> EmailTestResponseDTO:
        """Test SMTP connection"""
        try:
            async with aiosmtplib.SMTP(
                hostname=config.smtp_server,
                port=config.smtp_port,
                use_tls=config.use_tls
            ) as smtp:
                await smtp.login(config.smtp_username, config.smtp_password)

            return EmailTestResponseDTO(
                success=True,
                message="SMTP connection successful",
                test_type="connection",
                details={
                    "server": config.smtp_server,
                    "port": config.smtp_port,
                    "username": config.smtp_username
                }
            )

        except Exception as e:
            return EmailTestResponseDTO(
                success=False,
                message=f"SMTP connection failed: {str(e)}",
                test_type="connection"
            )

    async def _test_send_email(self, config: EmailConfig, to_email: str) -> EmailTestResponseDTO:
        """Test sending actual email"""
        try:
            # Create test message
            message = MIMEMultipart("alternative")
            message["Subject"] = "✅ Test Email - Agenda IA"
            message["From"] = f"{config.email_from_name} <{config.email_from_address.value}>"
            message["To"] = to_email

            # Create email content
            text_content = """
¡Hola!

Este es un email de prueba del sistema Agenda IA.

Si recibes este mensaje, significa que la configuración de email está funcionando correctamente.

Saludos,
Sistema Agenda IA
            """

            html_content = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #059669; color: white; padding: 20px; border-radius: 8px; text-align: center;">
            <h1>✅ Test Email - Agenda IA</h1>
        </div>

        <div style="padding: 20px; background-color: #f9f9f9; border-radius: 0 0 8px 8px;">
            <p>¡Hola!</p>

            <p>Este es un email de prueba del sistema <strong>Agenda IA</strong>.</p>

            <p>Si recibes este mensaje, significa que la configuración de email está funcionando correctamente.</p>

            <div style="background-color: #d4edda; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <p style="margin: 0;"><strong>✅ Configuración exitosa</strong></p>
                <p style="margin: 5px 0 0 0; font-size: 14px;">
                    El sistema de notificaciones por email está listo para funcionar.
                </p>
            </div>

            <p>Saludos,<br><strong>Sistema Agenda IA</strong></p>
        </div>

        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #666;">
            <p>Este es un email de prueba enviado automáticamente.</p>
        </div>
    </div>
</body>
</html>
            """

            # Add content parts
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            message.attach(text_part)
            message.attach(html_part)

            # Send email
            async with aiosmtplib.SMTP(
                hostname=config.smtp_server,
                port=config.smtp_port,
                use_tls=config.use_tls
            ) as smtp:
                await smtp.login(config.smtp_username, config.smtp_password)
                await smtp.send_message(message)

            return EmailTestResponseDTO(
                success=True,
                message=f"Test email sent successfully to {to_email}",
                test_type="full_email",
                details={
                    "recipient": to_email,
                    "from": config.email_from_address.value,
                    "subject": "✅ Test Email - Agenda IA"
                }
            )

        except Exception as e:
            return EmailTestResponseDTO(
                success=False,
                message=f"Failed to send test email: {str(e)}",
                test_type="full_email"
            )