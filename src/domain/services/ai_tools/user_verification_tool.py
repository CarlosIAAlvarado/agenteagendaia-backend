"""
AI Tool: Verificación de Usuario
Herramienta para verificar si un usuario está registrado en el sistema
"""
from typing import Dict, Any, Optional
import logging
import re

from ...repositories.user_repository import IUserRepository
from ...value_objects.email import Email
from ...value_objects.phone import Phone

logger = logging.getLogger(__name__)


class UserVerificationTool:
    """
    Herramienta AI: Verificación de Usuario
    
    OpenAI usa esta herramienta cuando:
    1. Usuario dice "sí, estoy registrado"
    2. Usuario proporciona email o teléfono para verificar
    3. Necesita verificar existencia antes de proceder
    """
    
    def __init__(self, user_repository: IUserRepository):
        self._user_repo = user_repository
    
    async def verify_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Verifica si un usuario existe por email
        
        Args:
            email: Email del usuario a verificar
            
        Returns:
            {
                "exists": bool,
                "user_id": str (si existe),
                "user_name": str (si existe),
                "message": str
            }
        """
        try:
            # Validar formato de email
            if not self._is_valid_email(email):
                return {
                    "tool_used": "user_verification",
                    "action": "email_verification",
                    "exists": False,
                    "error": "Email inválido",
                    "message": "El email que proporcionaste no tiene un formato válido. ¿Puedes verificarlo?"
                }
            
            # Buscar usuario por email
            email_obj = Email(email)
            user = await self._user_repo.get_by_email(email_obj)
            
            if user:
                logger.info(f"[VERIFICATION] User found with email: {email}")
                return {
                    "tool_used": "user_verification", 
                    "action": "email_verification",
                    "exists": True,
                    "user_id": user.id,
                    "user_name": user.name,
                    "user_email": user.email.value,
                    "message": f"¡Perfecto! Te encontré en el sistema, {user.name}. Ahora puedes proceder con tu cita.",
                    "next_step": "proceed_to_appointment"
                }
            else:
                logger.info(f"[VERIFICATION] No user found with email: {email}")
                return {
                    "tool_used": "user_verification",
                    "action": "email_verification", 
                    "exists": False,
                    "message": f"No encontré una cuenta con el email {email}. ¿Te gustaría registrarte ahora?",
                    "next_step": "registration_required",
                    "suggested_email": email  # Pre-llenar el formulario
                }
                
        except Exception as e:
            logger.error(f"Error verifying user by email: {e}")
            return {
                "tool_used": "user_verification",
                "action": "email_verification",
                "exists": False,
                "error": str(e),
                "message": "Hubo un error verificando tu información. ¿Puedes intentar de nuevo?"
            }
    
    async def verify_user_by_phone(self, phone: str) -> Dict[str, Any]:
        """
        Verifica si un usuario existe por teléfono
        """
        try:
            # Limpiar y validar teléfono
            clean_phone = self._clean_phone(phone)
            if not clean_phone:
                return {
                    "tool_used": "user_verification",
                    "action": "phone_verification",
                    "exists": False,
                    "error": "Teléfono inválido",
                    "message": "El teléfono que proporcionaste no tiene un formato válido. ¿Puedes verificarlo?"
                }
            
            # Buscar usuario por teléfono
            phone_obj = Phone(clean_phone)
            user = await self._user_repo.get_by_phone(phone_obj)
            
            if user:
                logger.info(f"[VERIFICATION] User found with phone: {clean_phone}")
                return {
                    "tool_used": "user_verification",
                    "action": "phone_verification", 
                    "exists": True,
                    "user_id": user.id,
                    "user_name": user.name,
                    "user_phone": user.phone.value,
                    "message": f"¡Perfecto! Te encontré en el sistema, {user.name}. Ahora puedes proceder con tu cita.",
                    "next_step": "proceed_to_appointment"
                }
            else:
                logger.info(f"[VERIFICATION] No user found with phone: {clean_phone}")
                return {
                    "tool_used": "user_verification",
                    "action": "phone_verification",
                    "exists": False,
                    "message": f"No encontré una cuenta con el teléfono {clean_phone}. ¿Te gustaría registrarte ahora?",
                    "next_step": "registration_required",
                    "suggested_phone": clean_phone  # Pre-llenar el formulario
                }
                
        except Exception as e:
            logger.error(f"Error verifying user by phone: {e}")
            return {
                "tool_used": "user_verification",
                "action": "phone_verification",
                "exists": False,
                "error": str(e),
                "message": "Hubo un error verificando tu información. ¿Puedes intentar de nuevo?"
            }
    
    def _is_valid_email(self, email: str) -> bool:
        """Valida formato básico de email"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email.strip()) is not None
    
    def _clean_phone(self, phone: str) -> Optional[str]:
        """Limpia y valida el teléfono"""
        # Remover espacios, guiones, paréntesis
        clean = re.sub(r'[^\d+]', '', phone.strip())
        
        # Validar que tenga al menos 10 dígitos
        digits_only = re.sub(r'[^\d]', '', clean)
        if len(digits_only) >= 10:
            return clean
        return None
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información sobre esta herramienta para OpenAI Function Calling"""
        return {
            "name": "user_verification_tool",
            "description": "Herramienta para verificar si un usuario está registrado en el sistema",
            "functions": [
                {
                    "name": "verify_user_by_email",
                    "description": "Verifica si existe un usuario con el email proporcionado",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email del usuario a verificar"
                            }
                        },
                        "required": ["email"]
                    }
                },
                {
                    "name": "verify_user_by_phone", 
                    "description": "Verifica si existe un usuario con el teléfono proporcionado",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phone": {
                                "type": "string",
                                "description": "Teléfono del usuario a verificar"
                            }
                        },
                        "required": ["phone"]
                    }
                }
            ]
        }