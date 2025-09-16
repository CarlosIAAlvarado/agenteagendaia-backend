from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import hashlib
from ...domain.entities.patient import Patient
from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.conversation_repository import IConversationRepository
from ..dto.express_registration_dto import (
    ExpressRegistrationDTO, ExpressRegistrationResponseDTO, 
    ExpressRegistrationStatsDTO, QuickRegistrationFormDTO
)
import logging

logger = logging.getLogger(__name__)


class ExpressRegistrationUseCases:
    """Use cases for express user registration functionality"""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        conversation_repository: IConversationRepository
    ):
        self._user_repo = user_repository
        self._conversation_repo = conversation_repository
    
    async def register_user_express(
        self, 
        registration_data: ExpressRegistrationDTO
    ) -> ExpressRegistrationResponseDTO:
        """Register a new user with express form (3 fields)"""
        try:
            # Check if user already exists by email
            existing_user = await self._user_repo.get_user_by_email(registration_data.email)
            
            if existing_user:
                # User exists, return existing user info
                logger.info(f"User already exists with email: {registration_data.email}")
                
                # Update phone if different
                if existing_user.phone != registration_data.phone:
                    existing_user.phone = registration_data.phone
                    await self._user_repo.update_user(existing_user)
                    logger.info(f"Updated phone for existing user: {existing_user.id}")
                
                return ExpressRegistrationResponseDTO(
                    user_id=existing_user.id,
                    name=existing_user.name,
                    email=existing_user.email,
                    phone=existing_user.phone,
                    is_new_user=False,
                    verification_required=not existing_user.is_verified,
                    verification_method="email" if not existing_user.is_verified else None,
                    privacy_policy_accepted=True,
                    preferred_communication_channel=registration_data.preferred_communication_channel,
                    created_at=existing_user.created_at.isoformat() if existing_user.created_at else datetime.utcnow().isoformat(),
                    conversation_id=registration_data.conversation_id,
                    next_step="service_selection",
                    welcome_message=f"¡Hola de nuevo, {existing_user.name}! Continuemos con tu agendamiento."
                )
            
            # Create new user
            user = User(
                id=None,
                name=registration_data.name,
                email=registration_data.email,
                phone=registration_data.phone,
                is_active=True,
                is_verified=False,  # Will be verified later
                created_at=datetime.utcnow(),
                preferences={
                    "communication_channel": registration_data.preferred_communication_channel,
                    "privacy_policy_accepted": registration_data.accept_privacy_policy,
                    "registration_method": "express",
                    "email_notifications": registration_data.preferred_communication_channel in ["email"],
                    "sms_notifications": registration_data.preferred_communication_channel in ["sms"],
                    "whatsapp_notifications": registration_data.preferred_communication_channel in ["whatsapp"]
                }
            )
            
            created_user = await self._user_repo.create_user(user)
            
            # Generate verification token if needed
            verification_method = None
            if not created_user.is_verified:
                verification_method = "email"  # Default to email verification
                # In a real implementation, send verification email here
            
            logger.info(f"Created new user via express registration: {created_user.id}")
            
            # Update conversation with user_id if conversation_id provided
            if registration_data.conversation_id:
                await self._update_conversation_user(
                    registration_data.conversation_id, 
                    created_user.id
                )
            
            return ExpressRegistrationResponseDTO(
                user_id=created_user.id,
                name=created_user.name,
                email=created_user.email,
                phone=created_user.phone,
                is_new_user=True,
                verification_required=True,
                verification_method=verification_method,
                privacy_policy_accepted=registration_data.accept_privacy_policy,
                preferred_communication_channel=registration_data.preferred_communication_channel,
                created_at=created_user.created_at.isoformat(),
                conversation_id=registration_data.conversation_id,
                next_step="service_selection",
                welcome_message=f"¡Bienvenido {created_user.name}! Tu registro ha sido exitoso. Continuemos con tu agendamiento."
            )
            
        except Exception as e:
            logger.error(f"Error in express registration: {e}")
            raise
    
    async def validate_registration_data(
        self, 
        email: str, 
        phone: str
    ) -> Dict[str, Any]:
        """Validate registration data and check for conflicts"""
        try:
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
            
            # Check if email already exists
            existing_user_email = await self._user_repo.get_user_by_email(email)
            if existing_user_email:
                validation_result["warnings"].append(
                    "Ya existe una cuenta con este correo electrónico"
                )
                validation_result["suggestions"].append(
                    "Si ya tienes cuenta, puedes iniciar sesión directamente"
                )
            
            # Check if phone already exists
            existing_user_phone = await self._user_repo.get_user_by_phone(phone)
            if existing_user_phone and existing_user_phone.email != email:
                validation_result["warnings"].append(
                    "Este número de teléfono está asociado con otra cuenta"
                )
            
            # Additional validations can be added here
            # For example, check against blocked domains, validate phone format, etc.
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating registration data: {e}")
            return {
                "is_valid": False,
                "errors": ["Error validando los datos"],
                "warnings": [],
                "suggestions": []
            }
    
    async def get_registration_form_config(
        self, 
        conversation_id: Optional[str] = None
    ) -> QuickRegistrationFormDTO:
        """Get configuration for the registration form"""
        try:
            # Customize form based on conversation context if needed
            form_config = QuickRegistrationFormDTO()
            
            if conversation_id:
                # Could customize form based on conversation context
                # For example, pre-fill some fields or adjust messaging
                pass
            
            return form_config
            
        except Exception as e:
            logger.error(f"Error getting registration form config: {e}")
            return QuickRegistrationFormDTO()  # Return default config
    
    async def get_registration_statistics(
        self,
        days: int = 30
    ) -> ExpressRegistrationStatsDTO:
        """Get registration statistics"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            today_start = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = end_date - timedelta(days=7)
            month_start = end_date - timedelta(days=30)
            
            # Get registration counts
            # In a real implementation, these would be actual database queries
            total_registrations = 450  # Mock data
            today_registrations = 15
            week_registrations = 89
            month_registrations = 245
            
            # Calculate conversion rate
            # This would be calculated from conversation -> registration data
            total_conversations = 850
            conversion_rate = (total_registrations / total_conversations) * 100
            
            # Mock channel preferences
            preferred_channels = {
                "email": 280,
                "sms": 95,
                "whatsapp": 75
            }
            
            return ExpressRegistrationStatsDTO(
                total_registrations=total_registrations,
                today_registrations=today_registrations,
                week_registrations=week_registrations,
                month_registrations=month_registrations,
                conversion_rate=round(conversion_rate, 1),
                average_form_completion_time=45.2,  # seconds
                preferred_channels=preferred_channels,
                verified_users=380,
                active_users=320,  # Users who made appointments
                generated_at=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error getting registration statistics: {e}")
            raise
    
    async def resend_verification(self, user_id: str) -> bool:
        """Resend verification email/SMS to user"""
        try:
            user = await self._user_repo.get_user_by_id(user_id)
            if not user:
                raise ValueError("Usuario no encontrado")
            
            if user.is_verified:
                raise ValueError("El usuario ya está verificado")
            
            # In a real implementation, resend verification email/SMS here
            logger.info(f"Resent verification for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resending verification: {e}")
            raise
    
    async def verify_user_registration(
        self, 
        user_id: str, 
        verification_code: str
    ) -> bool:
        """Verify user registration with code"""
        try:
            user = await self._user_repo.get_user_by_id(user_id)
            if not user:
                raise ValueError("Usuario no encontrado")
            
            if user.is_verified:
                return True  # Already verified
            
            # In a real implementation, validate the verification code
            # For now, accept any code for demonstration
            if len(verification_code) >= 4:
                user.is_verified = True
                user.verified_at = datetime.utcnow()
                await self._user_repo.update_user(user)
                
                logger.info(f"User verified successfully: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying user registration: {e}")
            raise
    
    async def update_communication_preferences(
        self,
        user_id: str,
        preferred_channel: str,
        email_notifications: bool = True,
        sms_notifications: bool = False,
        whatsapp_notifications: bool = False
    ) -> bool:
        """Update user communication preferences"""
        try:
            user = await self._user_repo.get_user_by_id(user_id)
            if not user:
                raise ValueError("Usuario no encontrado")
            
            # Update preferences
            if not user.preferences:
                user.preferences = {}
            
            user.preferences.update({
                "communication_channel": preferred_channel,
                "email_notifications": email_notifications,
                "sms_notifications": sms_notifications,
                "whatsapp_notifications": whatsapp_notifications,
                "preferences_updated_at": datetime.utcnow().isoformat()
            })
            
            await self._user_repo.update_user(user)
            logger.info(f"Updated communication preferences for user: {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating communication preferences: {e}")
            raise
    
    async def _update_conversation_user(
        self, 
        conversation_id: str, 
        user_id: str
    ) -> None:
        """Update conversation with user ID after registration"""
        try:
            conversation = await self._conversation_repo.get_conversation_by_id(conversation_id)
            if conversation:
                conversation.user_id = user_id
                # Update context to indicate user is now registered
                conversation.update_context("user_registered", True)
                conversation.update_context("registration_completed_at", datetime.utcnow().isoformat())
                
                await self._conversation_repo.update_conversation(conversation)
                logger.info(f"Updated conversation {conversation_id} with user {user_id}")
                
        except Exception as e:
            logger.error(f"Error updating conversation with user: {e}")
            # Don't raise - this is not critical for the registration flow