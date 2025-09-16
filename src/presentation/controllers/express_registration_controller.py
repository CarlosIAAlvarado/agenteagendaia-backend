from fastapi import HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime
from ...application.use_cases.express_registration_use_cases import ExpressRegistrationUseCases
from ...application.dto.express_registration_dto import (
    ExpressRegistrationDTO, ExpressRegistrationResponseDTO,
    ExpressRegistrationStatsDTO, QuickRegistrationFormDTO
)
import logging

logger = logging.getLogger(__name__)


class ExpressRegistrationController:
    """Controller for Express Registration endpoints"""
    
    def __init__(self, express_registration_use_cases: ExpressRegistrationUseCases):
        self.express_registration_use_cases = express_registration_use_cases
    
    async def register_user(
        self, 
        registration_data: ExpressRegistrationDTO
    ) -> ExpressRegistrationResponseDTO:
        """Register user with express form (3 required fields)"""
        try:
            result = await self.express_registration_use_cases.register_user_express(
                registration_data
            )
            
            # Log registration for analytics
            if result.is_new_user:
                logger.info(f"New user registered via express form: {result.user_id}")
            else:
                logger.info(f"Existing user logged in via express form: {result.user_id}")
            
            return result
            
        except ValueError as e:
            logger.warning(f"Registration validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error in express registration: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error procesando el registro"
            )
    
    async def validate_registration_data(
        self,
        email: str,
        phone: str
    ) -> Dict[str, Any]:
        """Validate registration data before submission"""
        try:
            validation_result = await self.express_registration_use_cases.validate_registration_data(
                email, phone
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating registration data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validando los datos"
            )
    
    async def get_registration_form(
        self,
        conversation_id: Optional[str] = None
    ) -> QuickRegistrationFormDTO:
        """Get registration form configuration"""
        try:
            form_config = await self.express_registration_use_cases.get_registration_form_config(
                conversation_id
            )
            
            return form_config
            
        except Exception as e:
            logger.error(f"Error getting registration form config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo configuración del formulario"
            )
    
    async def get_registration_statistics(
        self,
        days: int = 30
    ) -> ExpressRegistrationStatsDTO:
        """Get registration statistics for admin dashboard"""
        try:
            if days < 1 or days > 365:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El período debe estar entre 1 y 365 días"
                )
            
            stats = await self.express_registration_use_cases.get_registration_statistics(days)
            
            return stats
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting registration statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo estadísticas de registro"
            )
    
    async def resend_verification(self, user_id: str) -> Dict[str, Any]:
        """Resend verification code to user"""
        try:
            success = await self.express_registration_use_cases.resend_verification(user_id)
            
            if success:
                return {
                    "message": "Código de verificación reenviado exitosamente",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo reenviar el código de verificación"
                )
                
        except ValueError as e:
            logger.warning(f"Verification resend validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error resending verification: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error reenviando verificación"
            )
    
    async def verify_registration(
        self,
        user_id: str,
        verification_code: str
    ) -> Dict[str, Any]:
        """Verify user registration with code"""
        try:
            if not verification_code or len(verification_code.strip()) < 4:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Código de verificación inválido"
                )
            
            success = await self.express_registration_use_cases.verify_user_registration(
                user_id, verification_code.strip()
            )
            
            if success:
                return {
                    "message": "Usuario verificado exitosamente",
                    "user_id": user_id,
                    "verified": True,
                    "verified_at": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Código de verificación incorrecto"
                )
                
        except ValueError as e:
            logger.warning(f"Verification validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying registration: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verificando el registro"
            )
    
    async def update_communication_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user communication preferences"""
        try:
            preferred_channel = preferences.get("preferred_channel", "email")
            email_notifications = preferences.get("email_notifications", True)
            sms_notifications = preferences.get("sms_notifications", False)
            whatsapp_notifications = preferences.get("whatsapp_notifications", False)
            
            # Validate preferred channel
            valid_channels = ["email", "sms", "whatsapp"]
            if preferred_channel not in valid_channels:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Canal de comunicación debe ser uno de: {', '.join(valid_channels)}"
                )
            
            success = await self.express_registration_use_cases.update_communication_preferences(
                user_id=user_id,
                preferred_channel=preferred_channel,
                email_notifications=email_notifications,
                sms_notifications=sms_notifications,
                whatsapp_notifications=whatsapp_notifications
            )
            
            if success:
                return {
                    "message": "Preferencias actualizadas exitosamente",
                    "user_id": user_id,
                    "preferences": {
                        "preferred_channel": preferred_channel,
                        "email_notifications": email_notifications,
                        "sms_notifications": sms_notifications,
                        "whatsapp_notifications": whatsapp_notifications
                    },
                    "updated_at": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudieron actualizar las preferencias"
                )
                
        except ValueError as e:
            logger.warning(f"Preferences update validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating communication preferences: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error actualizando preferencias"
            )
    
    async def get_registration_analytics(self) -> Dict[str, Any]:
        """Get comprehensive registration analytics"""
        try:
            # Get basic statistics
            stats = await self.express_registration_use_cases.get_registration_statistics(30)
            
            # Add additional analytics
            analytics = {
                "overview": {
                    "total_registrations": stats.total_registrations,
                    "conversion_rate": stats.conversion_rate,
                    "average_completion_time": stats.average_form_completion_time,
                    "verification_rate": (stats.verified_users / stats.total_registrations * 100) if stats.total_registrations > 0 else 0,
                    "active_user_rate": (stats.active_users / stats.verified_users * 100) if stats.verified_users > 0 else 0
                },
                "recent_activity": {
                    "today": stats.today_registrations,
                    "this_week": stats.week_registrations,
                    "this_month": stats.month_registrations
                },
                "channel_preferences": stats.preferred_channels,
                "user_engagement": {
                    "total_users": stats.total_registrations,
                    "verified_users": stats.verified_users,
                    "active_users": stats.active_users,
                    "inactive_users": stats.verified_users - stats.active_users
                },
                "form_performance": {
                    "average_completion_time": f"{stats.average_form_completion_time} segundos",
                    "completion_rate": "85%",  # Mock data
                    "abandonment_rate": "15%",  # Mock data
                    "field_validation_errors": {
                        "email": "8%",
                        "phone": "12%",
                        "name": "3%"
                    }
                },
                "insights": [
                    f"Tasa de conversión del {stats.conversion_rate}% es {'excelente' if stats.conversion_rate > 50 else 'buena' if stats.conversion_rate > 30 else 'mejorable'}",
                    f"El {((stats.verified_users / stats.total_registrations) * 100):.1f}% de los usuarios verifican su cuenta",
                    f"Email es el canal preferido ({stats.preferred_channels['email']} usuarios)",
                    f"Tiempo promedio de completación: {stats.average_form_completion_time:.1f} segundos"
                ],
                "recommendations": [
                    "Optimizar formulario para reducir tiempo de completación" if stats.average_form_completion_time > 60 else "Tiempo de completación óptimo",
                    "Implementar recordatorios de verificación" if (stats.verified_users / stats.total_registrations) < 0.8 else "Buena tasa de verificación",
                    "Promocionar canales alternativos de comunicación" if stats.preferred_channels['email'] / stats.total_registrations > 0.7 else "Buena distribución de canales"
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting registration analytics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo análisis de registros"
            )