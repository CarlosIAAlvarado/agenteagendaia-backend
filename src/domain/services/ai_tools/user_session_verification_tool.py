"""
AI Tool: Verificación de Sesión de Usuario en Tiempo Real
Permite a OpenAI verificar el estado actual del usuario en la base de datos
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from ...repositories.user_repository import IUserRepository
from ...entities.patient import Patient
from ...value_objects.email import Email
from ...value_objects.phone import Phone

logger = logging.getLogger(__name__)


class UserSessionVerificationTool:
    """
    Herramienta AI: Verificación de Sesión de Usuario

    OpenAI usa esta herramienta para:
    1. Verificar si un usuario existe en tiempo real
    2. Obtener información completa del usuario
    3. Verificar el estado de registro actual
    4. Actualizar el contexto de la conversación con datos reales
    """

    def __init__(self, user_repository: IUserRepository):
        self._user_repo = user_repository

    async def verify_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Verifica usuario por email en tiempo real

        Args:
            email: Email del usuario a verificar

        Returns:
            {
                "exists": bool,
                "user_data": {...} if exists,
                "session_verified": bool,
                "action_required": "show_services" | "show_registration" | "continue"
            }
        """
        try:
            logger.info(f"[USER_VERIFICATION] Checking email: {email}")

            # Buscar usuario en base de datos
            # Convertir string a objeto Email
            email_obj = Email(email)
            user = await self._user_repo.get_by_email(email_obj)

            if user:
                logger.info(f"[USER_VERIFICATION] User found: {user.name} (ID: {user.id})")

                return {
                    "tool_used": "user_session_verification",
                    "action": "user_verified",
                    "exists": True,
                    "session_verified": True,
                    "user_data": {
                        "user_id": user.id,
                        "name": user.name,
                        "email": user.email.value if hasattr(user.email, 'value') else str(user.email),
                        "phone": user.phone.value if hasattr(user.phone, 'value') else str(user.phone),
                        "preferred_communication": "email",  # Default para Patient
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat() if user.created_at else None
                    },
                    "context_updates": {
                        "user_verified": True,
                        "user_registered": True,
                        "user_id": user.id,
                        "user_data": {
                            "name": user.name,
                            "email": user.email.value if hasattr(user.email, 'value') else str(user.email),
                            "phone": user.phone.value if hasattr(user.phone, 'value') else str(user.phone),
                            "id": user.id
                        },
                        "skip_registration_detection": True
                    },
                    "action_required": "show_services",
                    "message": f"¡Hola {user.name}! Te reconocí por tu email. Bienvenido de vuelta.",
                    "next_step": "service_selection"
                }
            else:
                logger.info(f"[USER_VERIFICATION] User not found: {email}")

                return {
                    "tool_used": "user_session_verification",
                    "action": "user_not_found",
                    "exists": False,
                    "session_verified": False,
                    "user_data": None,
                    "context_updates": {
                        "user_verified": False,
                        "user_registered": False,
                        "detected_email": email
                    },
                    "action_required": "show_registration",
                    "message": f"No encontré una cuenta con el email {email}. ¿Te gustaría registrarte ahora?",
                    "next_step": "registration"
                }

        except Exception as e:
            logger.error(f"Error verifying user by email: {e}")
            return {
                "tool_used": "user_session_verification",
                "action": "error",
                "exists": False,
                "session_verified": False,
                "error": str(e),
                "message": "Hubo un error verificando tu información. ¿Puedes intentar nuevamente?",
                "next_step": "retry"
            }

    async def verify_user_by_phone(self, phone: str) -> Dict[str, Any]:
        """
        Verifica usuario por teléfono en tiempo real
        """
        try:
            logger.info(f"[USER_VERIFICATION] Checking phone: {phone}")

            # Normalizar teléfono (agregar +57 si no lo tiene)
            normalized_phone = phone
            if not phone.startswith('+'):
                if phone.startswith('57'):
                    normalized_phone = '+' + phone
                elif phone.startswith('3'):  # Número colombiano típico
                    normalized_phone = '+57' + phone
                else:
                    normalized_phone = '+57' + phone

            # Convertir string a objeto Phone
            phone_obj = Phone(normalized_phone)
            user = await self._user_repo.get_by_phone(phone_obj)

            if user:
                logger.info(f"[USER_VERIFICATION] User found by phone: {user.name} (ID: {user.id})")

                return {
                    "tool_used": "user_session_verification",
                    "action": "user_verified",
                    "exists": True,
                    "session_verified": True,
                    "user_data": {
                        "user_id": user.id,
                        "name": user.name,
                        "email": user.email.value if hasattr(user.email, 'value') else str(user.email),
                        "phone": user.phone.value if hasattr(user.phone, 'value') else str(user.phone),
                        "preferred_communication": "phone",  # Default para Patient
                        "is_active": user.is_active
                    },
                    "context_updates": {
                        "user_verified": True,
                        "user_registered": True,
                        "user_id": user.id,
                        "user_data": {
                            "name": user.name,
                            "email": user.email.value if hasattr(user.email, 'value') else str(user.email),
                            "phone": user.phone.value if hasattr(user.phone, 'value') else str(user.phone),
                            "id": user.id
                        },
                        "skip_registration_detection": True
                    },
                    "action_required": "show_services",
                    "message": f"¡Hola {user.name}! Te reconocí por tu teléfono. Bienvenido de vuelta.",
                    "next_step": "service_selection"
                }
            else:
                logger.info(f"[USER_VERIFICATION] User not found by phone: {normalized_phone}")

                return {
                    "tool_used": "user_session_verification",
                    "action": "user_not_found",
                    "exists": False,
                    "session_verified": False,
                    "user_data": None,
                    "context_updates": {
                        "user_verified": False,
                        "user_registered": False,
                        "detected_phone": normalized_phone
                    },
                    "action_required": "show_registration",
                    "message": f"No encontré una cuenta con el número {normalized_phone}. ¿Te gustaría registrarte ahora?",
                    "next_step": "registration"
                }

        except Exception as e:
            logger.error(f"Error verifying user by phone: {e}")
            return {
                "tool_used": "user_session_verification",
                "action": "error",
                "exists": False,
                "session_verified": False,
                "error": str(e),
                "message": "Hubo un error verificando tu información. ¿Puedes intentar nuevamente?",
                "next_step": "retry"
            }

    async def get_current_user_status(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado actual del usuario desde la conversación
        """
        try:
            # Esta función puede ser usada por OpenAI para verificar
            # el estado actual del usuario en cualquier momento
            logger.info(f"[USER_VERIFICATION] Getting current user status for conversation: {conversation_id}")

            return {
                "tool_used": "user_session_verification",
                "action": "status_check",
                "message": "Verificando tu estado actual...",
                "next_step": "continue"
            }

        except Exception as e:
            logger.error(f"Error getting user status: {e}")
            return {
                "tool_used": "user_session_verification",
                "action": "error",
                "error": str(e),
                "message": "Hubo un error verificando tu estado. ¿Puedes continuar?",
                "next_step": "continue"
            }

    def get_tool_info(self) -> Dict[str, Any]:
        """Información sobre esta herramienta para OpenAI Function Calling"""
        return {
            "name": "user_session_verification_tool",
            "description": "Herramienta para verificar usuarios en tiempo real y mantener sesión actualizada",
            "functions": [
                {
                    "name": "verify_user_by_email",
                    "description": "USAR AUTOMÁTICAMENTE cuando el usuario proporcione un email. Verifica en tiempo real si el usuario existe en la base de datos.",
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
                    "description": "USAR AUTOMÁTICAMENTE cuando el usuario proporcione un teléfono. Verifica en tiempo real si el usuario existe en la base de datos.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phone": {
                                "type": "string",
                                "description": "Número de teléfono del usuario a verificar"
                            }
                        },
                        "required": ["phone"]
                    }
                },
                {
                    "name": "get_current_user_status",
                    "description": "Obtiene el estado actual del usuario para verificar sesión",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversation_id": {
                                "type": "string",
                                "description": "ID de la conversación actual"
                            }
                        },
                        "required": ["conversation_id"]
                    }
                }
            ]
        }