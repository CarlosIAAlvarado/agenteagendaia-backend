"""
AI Tool: Registro Express
Herramienta para que OpenAI controle el proceso de registro de usuario a paciente
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from ...repositories.user_repository import IUserRepository
from ...repositories.conversation_repository import IConversationRepository
from ...value_objects.email import Email
from ...value_objects.phone import Phone
from ...entities.patient import Patient

logger = logging.getLogger(__name__)


class ExpressRegistrationTool:
    """
    Herramienta AI: Registro Express
    
    OpenAI usa esta herramienta cuando:
    1. Usuario menciona querer agendar cita
    2. No existe en la base de datos
    3. Necesita convertir usuario → paciente
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        conversation_repository: IConversationRepository
    ):
        self._user_repo = user_repository
        self._conversation_repo = conversation_repository
    
    async def check_user_exists(self, email: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Verifica si el usuario ya existe en la base de datos
        OpenAI usa esto antes de decidir si mostrar formulario de registro
        
        Returns:
            {
                "user_exists": bool,
                "user_data": dict o None,
                "needs_registration": bool,
                "action_needed": str
            }
        """
        try:
            result = {
                "user_exists": False,
                "user_data": None,
                "needs_registration": True,
                "action_needed": "show_registration_form"
            }
            
            # Buscar por email si se proporciona
            if email:
                try:
                    email_obj = Email(email)
                    user = await self._user_repo.get_by_email(email_obj)
                    if user:
                        result = {
                            "user_exists": True,
                            "user_data": {
                                "id": user.id,
                                "name": user.name,
                                "email": user.email.value,
                                "phone": user.phone.value,
                                "is_active": user.is_active
                            },
                            "needs_registration": False,
                            "action_needed": "proceed_to_service_selection"
                        }
                        return result
                except Exception:
                    pass  # Email inválido, continúa con phone
            
            # Buscar por teléfono si se proporciona
            if phone:
                try:
                    phone_obj = Phone(phone)
                    user = await self._user_repo.get_by_phone(phone_obj)
                    if user:
                        result = {
                            "user_exists": True,
                            "user_data": {
                                "id": user.id,
                                "name": user.name,
                                "email": user.email.value,
                                "phone": user.phone.value,
                                "is_active": user.is_active
                            },
                            "needs_registration": False,
                            "action_needed": "proceed_to_service_selection"
                        }
                        return result
                except Exception:
                    pass  # Phone inválido
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking user existence: {e}")
            return {
                "user_exists": False,
                "user_data": None,
                "needs_registration": True,
                "action_needed": "show_registration_form",
                "error": str(e)
            }
    
    async def show_registration_form(self, conversation_id: str, pre_filled_data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        OpenAI usa esta función para mostrar el formulario de registro
        
        Returns:
            {
                "form_type": "registration_express",
                "form_config": {...},
                "message": str,
                "next_step": str
            }
        """
        try:
            # Usar datos pre-detectados si están disponibles
            default_name = pre_filled_data.get('name', '') if pre_filled_data else ''
            default_email = pre_filled_data.get('email', '') if pre_filled_data else ''
            default_phone = pre_filled_data.get('phone', '') if pre_filled_data else ''
            
            # Mensaje personalizado si hay datos pre-detectados
            subtitle = "Para agendar tu cita, necesitamos algunos datos:"
            if pre_filled_data:
                if default_email:
                    subtitle = f"Vi que mencionaste {default_email}. Solo necesito completar algunos datos más:"
                elif default_phone:
                    subtitle = f"Vi que mencionaste {default_phone}. Solo necesito completar algunos datos más:"
            
            form_config = {
                "id": "express_registration_form",
                "type": "interactive_form",
                "render_mode": "embedded",  # embedded = dentro del chat, modal = ventana flotante
                "title": "📝 Registro de Paciente",
                "subtitle": subtitle,
                "theme": {
                    "primary_color": "#10B981",  # Verde médico
                    "background": "#F9FAFB",
                    "border_radius": "12px",
                    "animation": "slide-up"
                },
                "fields": [
                    {
                        "id": "name_field",
                        "name": "name",
                        "label": "👤 Nombre completo",
                        "type": "text",
                        "placeholder": "Ej: María González",
                        "required": True,
                        "default_value": default_name,  # Pre-llenar con datos detectados
                        "validation": {
                            "min_length": 2,
                            "pattern": "^[a-zA-ZáéíóúÁÉÍÓÚñÑ\\s\\'-]+$",
                            "error_message": "Por favor ingresa un nombre válido"
                        },
                        "icon": "user",
                        "autocomplete": "name"
                    },
                    {
                        "id": "email_field",
                        "name": "email",
                        "label": "📧 Correo electrónico",
                        "type": "email",
                        "placeholder": "Ej: maria@gmail.com",
                        "required": True,
                        "default_value": default_email,  # Pre-llenar con datos detectados
                        "validation": {
                            "pattern": "email",
                            "error_message": "Por favor ingresa un correo válido"
                        },
                        "icon": "mail",
                        "autocomplete": "email"
                    },
                    {
                        "id": "phone_field",
                        "name": "phone",
                        "label": "📱 Teléfono celular",
                        "type": "tel",
                        "placeholder": "Ej: 3001234567",
                        "required": True,
                        "default_value": default_phone,  # Pre-llenar con datos detectados
                        "validation": {
                            "min_length": 8,
                            "max_length": 15,
                            "pattern": "^[0-9]+$",
                            "error_message": "Por favor ingresa un número válido"
                        },
                        "icon": "phone",
                        "input_mask": "999 999 9999",
                        "autocomplete": "tel"
                    },
                    {
                        "id": "communication_field",
                        "name": "preferred_communication",
                        "label": "💬 ¿Cómo prefieres que te contactemos?",
                        "type": "select",
                        "options": [
                            {"value": "email", "label": "📧 Correo electrónico", "icon": "mail"},
                            {"value": "sms", "label": "💬 SMS", "icon": "message-square"},
                            {"value": "whatsapp", "label": "📱 WhatsApp", "icon": "message-circle"}
                        ],
                        "required": True,
                        "default": "email",
                        "icon": "message-circle"
                    }
                ],
                "buttons": {
                    "submit": {
                        "text": "✅ Registrarme y Continuar",
                        "style": "primary",
                        "loading_text": "Registrando...",
                        "disabled_until_valid": True
                    },
                    "cancel": {
                        "text": "Cancelar",
                        "style": "secondary",
                        "visible": False  # No mostramos cancelar para no confundir
                    }
                },
                "privacy_notice": {
                    "text": "🔒 Al registrarte, aceptas nuestras políticas de privacidad y protección de datos.",
                    "link": "/privacy-policy",
                    "style": "info"
                },
                "behavior": {
                    "auto_focus": True,  # Focus automático en primer campo
                    "validate_on_blur": True,  # Validar cuando sale del campo
                    "show_progress": False,  # No mostrar barra de progreso
                    "submit_on_enter": False,  # No enviar con Enter
                    "clear_on_submit": False,  # No limpiar después de enviar
                    "disable_chat_input": True  # Deshabilitar input del chat mientras llena formulario
                },
                "conversation_id": conversation_id
            }
            
            return {
                "tool_used": "express_registration",
                "action": "show_form",
                "display_type": "interactive_form",  # Le dice al frontend que renderice un formulario
                "form_type": "registration_express",
                "form_config": form_config,
                "message": "Para poder agendar tu cita, primero necesito registrarte como paciente. Por favor completa este formulario rápido:",
                "ai_continues_after": True,  # OpenAI sigue controlando después
                "next_step": "await_registration_data",
                "conversation_flow": "registration_required"
            }
            
        except Exception as e:
            logger.error(f"Error showing registration form: {e}")
            return {
                "tool_used": "express_registration",
                "action": "error",
                "error": f"Error mostrando formulario: {str(e)}",
                "message": "Disculpa, hubo un error. ¿Puedes decirme tu nombre, email y teléfono para registrarte?",
                "next_step": "manual_registration"
            }
    
    async def process_registration(
        self, 
        name: str, 
        email: str, 
        phone: str, 
        conversation_id: str,
        preferred_communication: str = "email"
    ) -> Dict[str, Any]:
        """
        Procesa el registro del nuevo paciente
        OpenAI llama esto cuando el usuario envía los datos del formulario
        """
        try:
            # Validar datos básicos
            if not name or len(name.strip()) < 2:
                return {
                    "success": False,
                    "error": "El nombre debe tener al menos 2 caracteres",
                    "field_error": "name",
                    "message": "Por favor ingresa tu nombre completo (mínimo 2 caracteres)"
                }
            
            # Crear objetos de valor
            email_obj = Email(email)
            phone_obj = Phone(phone)
            
            # Verificar si ya existe
            existing_user = await self._user_repo.get_by_email(email_obj)
            if existing_user:
                return {
                    "success": True,
                    "is_new_user": False,
                    "user_id": existing_user.id,
                    "user_data": {
                        "name": existing_user.name,
                        "email": existing_user.email.value,
                        "phone": existing_user.phone.value
                    },
                    "message": f"¡Perfecto {existing_user.name}! Ya tienes una cuenta con nosotros. Continuemos con tu agendamiento.",
                    "next_step": "service_selection",
                    "conversation_flow": "existing_user_found",
                    "tool_used": "express_registration_completed",  # Usar mismo nombre para evitar re-detección
                    "user_registered": True,  # Bandera de usuario ya registrado
                    "no_form_display": True,  # No mostrar formularios
                    "tool_response": {}  # Respuesta limpia
                }
            
            # Crear nuevo usuario/paciente
            user = Patient(
                id=None,
                name=name.strip().title(),
                email=email_obj,
                phone=phone_obj,
                is_active=True,
                created_at=datetime.utcnow(),
                preferences={
                    "communication_channel": preferred_communication,
                    "registration_method": "express_chat",
                    "email_notifications": preferred_communication in ["email"],
                    "sms_notifications": preferred_communication in ["sms"], 
                    "whatsapp_notifications": preferred_communication in ["whatsapp"],
                    "registered_via": "ai_chat"
                }
            )
            
            created_user = await self._user_repo.create(user)
            
            # Actualizar conversación con user_id
            await self._update_conversation_with_user(conversation_id, created_user.id)
            
            logger.info(f"✅ Nuevo paciente registrado via AI: {created_user.id} - {name}")
            logger.info(f"✅ User data saved: Name={created_user.name}, Email={created_user.email.value}, Phone={created_user.phone.value}")
            
            return {
                "success": True,
                "is_new_user": True,
                "user_id": created_user.id,
                "user_data": {
                    "name": created_user.name,
                    "email": created_user.email.value,
                    "phone": created_user.phone.value
                },
                "message": f"¡Excelente {created_user.name}! Tu registro fue exitoso. Ahora eres oficialmente nuestro paciente. ¿Qué servicio médico te interesa?",
                "next_step": "service_selection",
                "conversation_flow": "new_patient_registered",
                "tool_used": "express_registration_completed",  # CAMBIO CLAVE: nuevo nombre para evitar re-detección
                "action": "registration_completed",
                "user_registered": True,  # BANDERA CLARA de registro completado
                "skip_tool_detection": True,
                "no_form_display": True,  # Evitar mostrar cualquier formulario
                "tool_response": {}  # Respuesta vacía para limpiar frontend
            }
            
        except ValueError as ve:
            # Error de validación
            return {
                "success": False,
                "error": str(ve),
                "message": f"Hay un problema con los datos: {str(ve)}. ¿Puedes verificar y enviarlos nuevamente?",
                "next_step": "fix_registration_data"
            }
        except Exception as e:
            logger.error(f"Error processing registration: {e}")
            return {
                "success": False,
                "error": f"Error interno: {str(e)}",
                "message": "Disculpa, hubo un error procesando tu registro. ¿Puedes intentar nuevamente?",
                "next_step": "retry_registration"
            }
    
    async def _update_conversation_with_user(self, conversation_id: str, user_id: str) -> None:
        """Actualiza la conversación con el user_id después del registro"""
        try:
            conversation = await self._conversation_repo.get_conversation_by_id(conversation_id)
            if conversation:
                conversation.user_id = user_id
                conversation.update_context("user_registered", True)
                conversation.update_context("patient_registration_completed", datetime.utcnow().isoformat())
                conversation.update_context("registration_method", "ai_express")
                
                await self._conversation_repo.update_conversation(conversation)
                logger.info(f"✅ Conversación {conversation_id} actualizada con paciente {user_id}")
        except Exception as e:
            logger.error(f"Error updating conversation with user: {e}")
            # No hacer raise - no es crítico
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información sobre esta herramienta para OpenAI Function Calling"""
        return {
            "name": "express_registration_tool",
            "description": "Herramienta para registrar nuevos pacientes cuando quieren agendar citas",
            "functions": [
                {
                    "name": "check_user_exists",
                    "description": "Verifica si un usuario ya existe en la base de datos",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "description": "Email del usuario a verificar"},
                            "phone": {"type": "string", "description": "Teléfono del usuario a verificar"}
                        }
                    }
                },
                {
                    "name": "show_registration_form", 
                    "description": "Muestra formulario de registro cuando el usuario no existe",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversation_id": {"type": "string", "description": "ID de la conversación actual"}
                        },
                        "required": ["conversation_id"]
                    }
                },
                {
                    "name": "process_registration",
                    "description": "Procesa los datos de registro del nuevo paciente",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "name": {"type": "string", "description": "Nombre completo del paciente"},
                            "email": {"type": "string", "description": "Email del paciente"},
                            "phone": {"type": "string", "description": "Teléfono del paciente"},
                            "conversation_id": {"type": "string", "description": "ID de la conversación"},
                            "preferred_communication": {"type": "string", "enum": ["email", "sms", "whatsapp"], "description": "Canal preferido de comunicación"}
                        },
                        "required": ["name", "email", "phone", "conversation_id"]
                    }
                }
            ]
        }