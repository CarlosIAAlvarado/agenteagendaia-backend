# -*- coding: utf-8 -*-
"""
Conversation Use Cases v3.0 - Arquitectura con Agente IA Unificado
Sistema inteligente donde OpenAI GPT-4o-mini controla todo el flujo conversacional
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ...domain.entities.conversation import Conversation, Message, MessageRole, ConversationStatus
from ...domain.repositories.conversation_repository import IConversationRepository
from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.service_repository import IServiceRepository
from ...domain.repositories.professional_repository import IProfessionalRepository
from ...domain.repositories.appointment_repository import IAppointmentRepository
from ...domain.services.availability_service import AvailabilityDomainService
from ...infrastructure.ai.agenda_ia_agent import AgendaIAAgent, AgentContext
from ..dto.conversation_dto import (
    ChatMessageDTO, ChatResponseDTO, ConversationCreateDTO, ConversationResponseDTO
)

logger = logging.getLogger(__name__)


class ConversationUseCasesV2:
    """
    Use cases for conversation management with Unified AI Agent

    OpenAI GPT-4o-mini maneja todo:
    - Conversación natural fluida
    - Detección automática de intenciones
    - Function Calling para herramientas específicas
    - Gestión completa del flujo conversacional
    """
    
    def __init__(
        self,
        conversation_repository: IConversationRepository,
        user_repository: IUserRepository,
        service_repository: IServiceRepository,
        professional_repository: IProfessionalRepository,
        appointment_repository: IAppointmentRepository,
        availability_service: AvailabilityDomainService,
        ai_agent=None
    ):
        self._conversation_repo = conversation_repository
        self._user_repo = user_repository
        self._service_repo = service_repository
        self._professional_repo = professional_repository
        self._appointment_repo = appointment_repository
        self._availability_service = availability_service
        
        # Usar el agente IA unificado desde dependencies o crear uno nuevo si es necesario
        logger.info("🔧 Initializing AI Agent for conversation management")
        if ai_agent:
            self._ai_agent = ai_agent
            logger.info("✅ AI Agent from dependencies loaded successfully with all tools")
        else:
            logger.info("📦 Creating new AI Agent instance with repositories")
            try:
                self._ai_agent = AgendaIAAgent(
                    user_repo=self._user_repo,
                    conversation_repo=self._conversation_repo,
                    service_repo=self._service_repo,
                    professional_repo=self._professional_repo,
                    appointment_repo=self._appointment_repo
                )
                logger.info("✅ AI Agent initialized successfully with all tools")
            except Exception as e:
                logger.error(f"❌ Error initializing AI Agent: {e}")
                self._ai_agent = None
    
    async def start_conversation(
        self, 
        conversation_data: ConversationCreateDTO
    ) -> ConversationResponseDTO:
        """Start a new conversation with AI agent context"""
        try:
            # Check for existing active conversation
            if conversation_data.user_id:
                existing_conversation = await self._conversation_repo.get_active_conversation_by_user(
                    conversation_data.user_id
                )
                if existing_conversation:
                    return self._conversation_to_dto(existing_conversation)
            
            # Create new conversation
            conversation = Conversation(
                id=None,
                user_id=conversation_data.user_id,
                status=ConversationStatus.ACTIVE,
                current_step="greeting",
                context={},
                created_at=datetime.utcnow()
            )
            
            created_conversation = await self._conversation_repo.create_conversation(conversation)
            
            # Crear contexto del agente para el saludo inicial
            
            agent_context = AgentContext(
                user_id=created_conversation.user_id,
                conversation_id=created_conversation.id
            )
            agent_context.current_step = created_conversation.current_step
            agent_context.context_data = created_conversation.context
            
            # Generar saludo natural con el agente IA
            greeting_response, enhanced_context = await self._ai_agent.process_message(
                "Hola",
                agent_context
            )
            
            # Extraer contexto de la respuesta de IA
            updated_context = enhanced_context.context_data if hasattr(enhanced_context, 'context_data') else {}
            
            # Update conversation context
            for key, value in updated_context.items():
                created_conversation.update_context(key, value)
            
            # Create initial greeting message
            greeting_message = Message(
                id=None,
                conversation_id=created_conversation.id,
                role=MessageRole.ASSISTANT,
                content=greeting_response,
                created_at=datetime.utcnow()
            )
            
            # Save message
            await self._conversation_repo.add_message(greeting_message)
            await self._conversation_repo.update_conversation(created_conversation)
            
            logger.info(f"Started conversation: {created_conversation.id}")
            
            return self._conversation_to_dto(created_conversation)
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            raise
    
    async def send_message(
        self, 
        conversation_id: str, 
        message_data: ChatMessageDTO
    ) -> ChatResponseDTO:
        """Process user message with AI agent"""
        try:
            # Get conversation
            conversation = await self._conversation_repo.get_conversation_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            if conversation.status != ConversationStatus.ACTIVE:
                raise ValueError(f"Conversation {conversation_id} is not active")
            
            # Save user message
            user_message = Message(
                id=None,
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=message_data.content,
                created_at=datetime.utcnow()
            )
            await self._conversation_repo.add_message(user_message)
            
            # FLUJO DIRECTO: El mensaje va directo al agente de OpenAI
            from ...infrastructure.ai.agenda_ia_agent import AgentContext
            
            # Crear contexto del agente
            agent_context = AgentContext(
                user_id=conversation.user_id,
                conversation_id=conversation.id
            )
            # Usar contexto real de conversación para mantener continuidad
            agent_context.current_step = conversation.current_step
            agent_context.context_data = conversation.context

            # DEBUG: Log del contexto que se está cargando
            logger.info(f"[CONTEXT_LOAD] Loading context from conversation: {conversation.context}")
            logger.info(f"[CONTEXT_LOAD] User registered in context: {conversation.context.get('user_registered', False)}")
            logger.info(f"[CONTEXT_LOAD] Skip registration: {conversation.context.get('skip_registration_detection', False)}")
            
            # *** CARGAR HISTORIAL CONVERSACIONAL DESDE DB ***
            # Obtener mensajes previos de la conversación para contexto
            previous_messages = await self._conversation_repo.get_conversation_messages(conversation_id, limit=20)
            
            # Añadir mensajes al contexto del agente (excluyendo el mensaje actual que recién guardamos)
            for msg in previous_messages:
                if msg.content != message_data.content:  # Evitar duplicar el mensaje actual
                    agent_context.add_message(
                        role=msg.role.value,
                        content=msg.content
                    )
            
            logger.info(f"🔥 LOADED CONVERSATION HISTORY: {len(previous_messages)} messages")
            logger.info(f"🔥 AGENT CONTEXT HISTORY: {len(agent_context.conversation_history)} messages")
            logger.info(f"🔥 USING REAL CONTEXT - Step: {conversation.current_step}")
            
            # DEBUG: Log antes de llamar OpenAI
            logger.info(f"🔥 ABOUT TO CALL OPENAI with message: '{message_data.content}'")
            logger.info(f"🔥 AI Agent available: {self._ai_agent is not None}")
            
            # INTERCEPTAR MENSAJES ESPECIALES ANTES DE OPENAI
            if message_data.content.startswith("REGISTRO:") or message_data.content.startswith("FORM_SUBMISSION:"):
                logger.info("🔧 INTERCEPTED REGISTRATION MESSAGE - Processing registration data")
                # El agente procesará esto y devolverá el resultado sin pasar por OpenAI
            
            # Procesar mensaje (el agente detectará patrones internamente)
            ai_response, enhanced_context = await self._ai_agent.process_message(
                message_data.content,
                agent_context
            )
            
            # DEBUG: Log después de OpenAI
            logger.info(f"🔥 OPENAI RESPONSE: '{ai_response}'")
            logger.info(f"🔥 Enhanced context: {enhanced_context.context_data if hasattr(enhanced_context, 'context_data') else 'No context'}")
            
            # Obtener intent del contexto procesado por OpenAI
            intent_data = {"intent": "CONVERSACION_CASUAL", "entities": {}}
            if hasattr(enhanced_context, 'context_data') and 'main_intent' in enhanced_context.context_data:
                intent_data = {
                    "intent": enhanced_context.context_data['main_intent'],
                    "entities": enhanced_context.context_data.get('user_data', {})
                }
            
            # Usar contexto actualizado del agente
            updated_context = enhanced_context.context_data if hasattr(enhanced_context, 'context_data') else {}
            
            # IMPORTANTE: Si el usuario fue registrado o verificado, actualizar contexto de conversación
            if updated_context.get('user_registered', False):
                logger.info("✅ User registered detected - Updating conversation context")
                conversation.user_id = updated_context.get('user_id', conversation.user_id)
                conversation.update_context("user_registered", True)
                conversation.update_context("registration_completed", True)
                conversation.update_context("skip_registration_detection", True)
                
                # Limpiar tool_response para evitar re-renderizado del formulario
                updated_context['tool_response'] = {}
                updated_context['display_type'] = None
                updated_context['form_config'] = None
            
            # CORREGIR: Si el usuario fue verificado (ya existía), también actualizar conversation.user_id
            elif updated_context.get('user_verified', False) and updated_context.get('user_id'):
                logger.info("✅ User verified detected - Updating conversation with user_id")
                conversation.user_id = updated_context.get('user_id')
                conversation.update_context("user_verified", True)
                conversation.update_context("skip_registration_detection", True)

            # 🔧 LIMPIEZA ESPECIAL: Si la cita fue confirmada, limpiar TODOS los datos del selector
            elif updated_context.get('appointment_confirmed', False):
                logger.info("✅ Appointment confirmed - CLEANING ALL selector data to prevent calendar redisplay")

                # 🧹 LIMPIEZA COMPLETA de datos que causan re-renderizado del calendario
                updated_context['tool_response'] = None
                updated_context['available_slots'] = None
                updated_context['service_data'] = None
                updated_context['slot_config'] = None
                updated_context['time_slots'] = None
                updated_context['tool_data'] = None
                updated_context['catalog_config'] = None
                updated_context['service_catalog'] = None
                updated_context['display_type'] = 'confirmation'

                logger.info("🧹 Cleaned calendar data - Only confirmation should display")
            
            # Update conversation
            for key, value in updated_context.items():
                conversation.update_context(key, value)
            
            if "step" in updated_context:
                conversation.update_step(updated_context["step"])
            
            await self._conversation_repo.update_conversation(conversation)
            
            # Save AI response (solo si no es un registro completado que ya se añadió)
            if not (updated_context.get('user_registered', False) and updated_context.get('tool_used') == 'express_registration_completed'):
                ai_message = Message(
                    id=None,
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=ai_response,
                    created_at=datetime.utcnow()
                )
                await self._conversation_repo.add_message(ai_message)
            
            logger.info(f"Message processed for conversation: {conversation_id}")
            
            # Función auxiliar para acceder al contexto (compatible con dict y AgentContext)
            def safe_get_context(context, key, default=None):
                if hasattr(context, 'get_context'):
                    return context.get_context(key) or default
                elif isinstance(context, dict):
                    return context.get(key, default)
                else:
                    return default

            # Extract tool response if a tool was used
            tool_response = safe_get_context(updated_context, 'tool_response') or {}
            logger.info(f"🔧 [DEBUG_1] INITIAL tool_response: {tool_response}")
            logger.info(f"🔧 [DEBUG_1] updated_context type: {type(updated_context)}")
            logger.info(f"🔧 [DEBUG_1] display_type in context: {safe_get_context(updated_context, 'display_type')}")
            logger.info(f"🔧 [DEBUG_1] tool_data in context: {safe_get_context(updated_context, 'tool_data')}")
            logger.info(f"🔧 [DEBUG_1] tool_used in context: {safe_get_context(updated_context, 'tool_used')}")

            # Función auxiliar para actualizar contexto de manera segura
            def safe_update_context(context, key, value):
                if hasattr(context, 'update_context'):
                    context.update_context(key, value)
                elif isinstance(context, dict):
                    context[key] = value

            # Si el usuario ya está registrado, NO enviar datos de formulario de REGISTRO
            # Pero SÍ permitir otros display_types como service_catalog
            if safe_get_context(updated_context, 'user_registered') or safe_get_context(updated_context, 'registration_completed'):
                logger.info(f"🔧 [DEBUG_2] User is registered, checking display_type: {safe_get_context(updated_context, 'display_type')}")

                # Solo limpiar form_config si es un formulario de registro
                if safe_get_context(updated_context, 'display_type') == 'interactive_form':
                    tool_response = {}
                    safe_update_context(updated_context, 'display_type', None)
                    safe_update_context(updated_context, 'form_config', None)
                    logger.info("🔧 USER REGISTERED - Clearing registration form data from response")
                else:
                    logger.info(f"🔧 [DEBUG_2] NOT clearing data - display_type is: {safe_get_context(updated_context, 'display_type')}")
                    # IMPORTANT: NO clear tool_response when display_type is NOT 'interactive_form'
                    # This preserves service_catalog and other display types

                # Para otros display_types (como service_catalog), mantener los datos
                logger.info(f"🔧 User ID in conversation: {conversation.user_id}")

            logger.info(f"🔧 [DEBUG_3] AFTER user check - tool_response: {tool_response}")
            logger.info(f"🔧 [DEBUG_3] AFTER user check - display_type: {safe_get_context(updated_context, 'display_type')}")

            # DEBUG: Log del tool_response que se va a enviar
            logger.info(f"🔧 FINAL TOOL RESPONSE TO FRONTEND: {tool_response}")
            logger.info(f"🔧 USER REGISTERED STATUS: {safe_get_context(updated_context, 'user_registered')}")
            logger.info(f"🔧 TOOL USED: {safe_get_context(updated_context, 'tool_used')}")

            # Construir respuesta final
            final_tool_data = safe_get_context(updated_context, 'tool_data') or tool_response or {}
            final_display_type = safe_get_context(updated_context, 'display_type') or (tool_response.get('display_type') if tool_response else None)

            # 🔧 FIX TEMPORAL: Si tool_used es service_consultation y hay catalog_config, FORZAR display_type
            tool_used = safe_get_context(updated_context, 'tool_used')
            if tool_used == 'service_consultation' and final_tool_data and final_tool_data.get('catalog_config'):
                final_display_type = 'service_catalog'
                logger.info("🔧 [FIX] FORCING display_type = 'service_catalog' due to service_consultation tool")

            logger.info(f"🔧 [DEBUG_4] FINAL DATA TO FRONTEND:")
            logger.info(f"🔧 [DEBUG_4]   tool_data: {final_tool_data}")
            logger.info(f"🔧 [DEBUG_4]   display_type: {final_display_type}")
            logger.info(f"🔧 [DEBUG_4]   tool_used: {safe_get_context(updated_context, 'tool_used')}")

            response_dto = ChatResponseDTO(
                message=ai_response,
                conversation_id=conversation_id,
                intent=intent_data.get('intent', 'OTRO'),
                confidence=intent_data.get('confidence', 0.0),
                context=conversation.context,
                step=conversation.current_step,
                timestamp=datetime.utcnow().isoformat(),
                # New tool-based architecture fields
                tool_used=safe_get_context(updated_context, 'tool_used'),
                tool_type=safe_get_context(updated_context, 'tool_type'),
                tool_data=final_tool_data,
                conversation_type=safe_get_context(updated_context, 'conversation_type') or 'natural',
                ai_enhanced=safe_get_context(updated_context, 'ai_enhanced') or False,
                # Interactive form fields - Priorizar updated_context sobre tool_response vacío
                display_type=final_display_type,
                form_config=safe_get_context(updated_context, 'form_config') or (tool_response.get('form_config') if tool_response else None),
                ai_continues_after=safe_get_context(updated_context, 'ai_continues_after') or (tool_response.get('ai_continues_after') if tool_response else False)
            )

            logger.info(f"🔧 [DEBUG_5] RESPONSE DTO CREATED - display_type: {response_dto.display_type}")
            logger.info(f"🔧 [DEBUG_5] RESPONSE DTO CREATED - tool_data keys: {list(response_dto.tool_data.keys()) if response_dto.tool_data else 'None'}")

            return response_dto
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(f"Full error traceback:", exc_info=True)
            return ChatResponseDTO(
                message=f"ERROR DEBUG: {str(e)} - Revisa los logs del backend",
                conversation_id=conversation_id,
                intent="ERROR",
                confidence=0.0,
                context={"error_details": str(e)},
                step="error",
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[ConversationResponseDTO]:
        """Get conversation by ID"""
        try:
            conversation = await self._conversation_repo.get_conversation_by_id(conversation_id)
            if not conversation:
                return None
            
            return self._conversation_to_dto(conversation)
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            raise
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[ConversationResponseDTO]:
        """Get conversations for a user"""
        try:
            conversations = await self._conversation_repo.get_conversations_by_user(
                user_id, skip, limit
            )
            
            return [self._conversation_to_dto(conv) for conv in conversations]
            
        except Exception as e:
            logger.error(f"Error getting user conversations {user_id}: {e}")
            raise
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 50
    ) -> List[dict]:
        """Get messages for a conversation"""
        try:
            conversation = await self._conversation_repo.get_conversation_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            messages = await self._conversation_repo.get_conversation_messages(conversation_id, limit)
            
            messages_list = []
            for msg in messages:
                messages_list.append({
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "intent": msg.intent.value if msg.intent else None,
                    "confidence": msg.confidence,
                    "entities": msg.entities,
                    "metadata": msg.metadata,
                    "created_at": msg.created_at.isoformat()
                })
            
            return messages_list
            
        except Exception as e:
            logger.error(f"Error getting conversation messages {conversation_id}: {e}")
            raise
    
    async def end_conversation(self, conversation_id: str) -> ConversationResponseDTO:
        """End an active conversation"""
        try:
            conversation = await self._conversation_repo.get_conversation_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            conversation.complete_conversation(success=True)
            
            closing_message = Message(
                id=None,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content="¡Gracias por usar AGENDA IA! ¿Hay algo más en lo que pueda ayudarte?",
                created_at=datetime.utcnow()
            )
            
            await self._conversation_repo.add_message(closing_message)
            await self._conversation_repo.update_conversation(conversation)
            
            logger.info(f"Ended conversation: {conversation_id}")
            
            return self._conversation_to_dto(conversation)
            
        except Exception as e:
            logger.error(f"Error ending conversation {conversation_id}: {e}")
            raise
    
    def _conversation_to_dto(self, conversation: Conversation) -> ConversationResponseDTO:
        """Convert conversation entity to DTO"""
        return ConversationResponseDTO(
            id=str(conversation.id),
            user_id=conversation.user_id,
            status=conversation.status.value,
            current_step=conversation.current_step,
            context=conversation.context,
            message_count=len(conversation.messages),
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat() if conversation.updated_at else None,
            completed_at=conversation.completed_at.isoformat() if conversation.completed_at else None,
            duration_minutes=conversation.get_duration_minutes()
        )