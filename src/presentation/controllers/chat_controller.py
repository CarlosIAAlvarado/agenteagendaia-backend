from fastapi import HTTPException, status
from typing import Optional, List
from datetime import datetime
from ...application.use_cases.conversation_use_cases_v2 import ConversationUseCasesV2
from ...application.dto.conversation_dto import (
    ChatMessageDTO, ChatResponseDTO, ConversationCreateDTO, ConversationResponseDTO,
    ConversationListResponseDTO, EscalationRequestDTO, ConversationAnalyticsDTO,
    ConversationSearchDTO, UserRegistrationDTO, UserRegistrationResponseDTO
)
import logging

logger = logging.getLogger(__name__)


class ChatController:
    """Controller for Chat and Conversation endpoints"""
    
    def __init__(self, conversation_use_cases: ConversationUseCasesV2):
        self.conversation_use_cases = conversation_use_cases
    
    async def start_conversation(self, conversation_data: ConversationCreateDTO) -> ConversationResponseDTO:
        """Start a new conversation"""
        try:
            conversation = await self.conversation_use_cases.start_conversation(conversation_data)
            
            # The use case already handles the initial greeting - no need to send another message
            return conversation
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error starting conversation"
            )
    
    async def send_message(self, conversation_id: str, message_data: ChatMessageDTO) -> ChatResponseDTO:
        try:
            # DEBUG: CONFIRMACIÓN ABSOLUTA DE QUE NUESTRO CÓDIGO SE EJECUTA
            logger.info("[CRITICAL] CHAT CONTROLLER RUNNING - CODE UPDATED")
            logger.info(f"[CRITICAL] MESSAGE RECEIVED: '{message_data.content}'")
            
            response = await self.conversation_use_cases.send_message(conversation_id, message_data)
            
            logger.info(f"[CRITICAL] RESPONSE FROM USE_CASES: '{response.message}'")
            return response
        except ValueError as e:
            logger.warning("Chat validation error: " + str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error("Error sending message: " + str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing message"
            )
    
    async def get_conversation(self, conversation_id: str) -> ConversationResponseDTO:
        """Get conversation by ID"""
        try:
            conversation = await self.conversation_use_cases.get_conversation_by_id(conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {conversation_id} not found"
                )
            return conversation
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving conversation"
            )
    
    async def get_user_conversations(
        self, 
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> ConversationListResponseDTO:
        """Get conversations for a user"""
        try:
            if skip < 0 or limit <= 0 or limit > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination parameters"
                )
            
            conversations = await self.conversation_use_cases.get_user_conversations(
                user_id, skip, limit
            )
            
            return ConversationListResponseDTO(
                conversations=conversations,
                total=len(conversations),  # In a real scenario, get actual total count
                skip=skip,
                limit=limit
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user conversations {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user conversations"
            )
    
    async def end_conversation(self, conversation_id: str) -> ConversationResponseDTO:
        """End an active conversation"""
        try:
            conversation = await self.conversation_use_cases.end_conversation(conversation_id)
            return conversation
            
        except ValueError as e:
            logger.warning(f"Error ending conversation: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error ending conversation {conversation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error ending conversation"
            )
    
    async def escalate_conversation(
        self, 
        conversation_id: str, 
        escalation_data: EscalationRequestDTO
    ) -> ConversationResponseDTO:
        """Escalate conversation to human agent"""
        try:
            conversation = await self.conversation_use_cases.escalate_conversation(
                conversation_id, escalation_data.reason
            )
            return conversation
            
        except ValueError as e:
            logger.warning(f"Error escalating conversation: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error escalating conversation {conversation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error escalating conversation"
            )
    
    async def get_conversation_messages(
        self, 
        conversation_id: str,
        limit: int = 50
    ) -> List[dict]:
        """Get messages for a conversation"""
        try:
            if limit <= 0 or limit > 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid limit parameter (1-200)"
                )
            
            conversation = await self.conversation_use_cases.get_conversation_by_id(conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {conversation_id} not found"
                )
            
            # Use the public method from use cases
            return await self.conversation_use_cases.get_conversation_messages(conversation_id, limit)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation messages {conversation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving messages"
            )
    
    async def get_conversation_analytics(
        self,
        start_date: str,
        end_date: str
    ) -> ConversationAnalyticsDTO:
        """Get conversation analytics for date range"""
        try:
            # Parse dates
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
            
            if start_dt >= end_dt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date must be before end date"
                )
            
            analytics = await self.conversation_use_cases.get_conversation_analytics(
                start_dt, end_dt
            )
            
            return ConversationAnalyticsDTO(**analytics)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving analytics"
            )
    
    async def cleanup_abandoned_conversations(self) -> dict:
        """Clean up abandoned conversations (admin endpoint)"""
        try:
            count = await self.conversation_use_cases.cleanup_abandoned_conversations()
            
            return {
                "message": f"Cleaned up {count} abandoned conversations",
                "count": count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up abandoned conversations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error cleaning up conversations"
            )
    
    async def search_conversations(self, search_params: ConversationSearchDTO) -> ConversationListResponseDTO:
        """Search conversations with filters"""
        try:
            # This would be implemented with proper search functionality
            # For now, return empty results
            return ConversationListResponseDTO(
                conversations=[],
                total=0,
                skip=search_params.skip,
                limit=search_params.limit
            )
            
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error searching conversations"
            )
    
    async def get_conversation_context(self, conversation_id: str) -> dict:
        """Get conversation context"""
        try:
            conversation = await self.conversation_use_cases.get_conversation_by_id(conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {conversation_id} not found"
                )
            
            return {
                "conversation_id": conversation_id,
                "context": conversation.context if hasattr(conversation, 'context') else {},
                "step": conversation.current_step if hasattr(conversation, 'current_step') else "unknown",
                "status": conversation.status
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation context {conversation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving conversation context"
            )
    
    async def get_quick_replies(self, conversation_id: str) -> List[dict]:
        """Get suggested quick replies based on conversation context"""
        try:
            conversation = await self.conversation_use_cases.get_conversation_by_id(conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {conversation_id} not found"
                )
            
            # Generate quick replies based on current step
            quick_replies = []
            
            step = conversation.current_step if hasattr(conversation, 'current_step') else "greeting"
            
            if step == "greeting":
                quick_replies = [
                    {"text": "Agendar cita", "value": "agendar", "action": "select"},
                    {"text": "Ver mis citas", "value": "consultar", "action": "select"},
                    {"text": "Cancelar cita", "value": "cancelar", "action": "select"}
                ]
            elif step == "service_selection":
                quick_replies = [
                    {"text": "Consulta médica", "value": "consulta_medica", "action": "select"},
                    {"text": "Servicio de belleza", "value": "belleza", "action": "select"},
                    {"text": "Ver todos los servicios", "value": "ver_servicios", "action": "navigate"}
                ]
            elif step == "appointment_scheduling":
                quick_replies = [
                    {"text": "Esta semana", "value": "esta_semana", "action": "select"},
                    {"text": "Próximo mes", "value": "proximo_mes", "action": "select"},
                    {"text": "En la mañana", "value": "manana", "action": "select"},
                    {"text": "En la tarde", "value": "tarde", "action": "select"}
                ]
            
            return quick_replies
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting quick replies for {conversation_id}: {e}")
            return []
    
    async def register_user_from_form(self, registration_data: UserRegistrationDTO) -> UserRegistrationResponseDTO:
        """Register user directly from form data - bypassing AI processing"""
        try:
            logger.info(f"Registering user from form: {registration_data.name}, {registration_data.email}")
            
            # Get the conversation first to validate it exists
            conversation = await self.conversation_use_cases.get_conversation_by_id(registration_data.conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {registration_data.conversation_id} not found"
                )
            
            # Create user directly in database
            from ...domain.entities.patient import Patient
            from ...domain.value_objects.email import Email
            from ...domain.value_objects.phone import Phone
            from ...infrastructure.dependencies import get_user_repository
            
            user_repo = await get_user_repository()
            
            # Create the user entity
            new_user = User(
                id=None,
                name=registration_data.name,
                email=Email(registration_data.email),
                phone=Phone(registration_data.phone),
                created_at=datetime.utcnow()
            )
            
            # Try to create the user
            try:
                created_user = await user_repo.create(new_user)
                logger.info(f"User created successfully: {created_user.id}")
                
                # Update conversation context directly - no AI processing
                from ...infrastructure.dependencies import get_conversation_repository
                conv_repo = await get_conversation_repository()
                
                # Get the actual conversation entity
                conversation_entity = await conv_repo.get_conversation_by_id(registration_data.conversation_id)
                if conversation_entity:
                    # Update context with user data
                    conversation_entity.update_context("user_id", created_user.id)
                    conversation_entity.update_context("user_name", created_user.name)
                    conversation_entity.update_context("user_email", created_user.email.value)
                    conversation_entity.update_context("user_phone", created_user.phone.value)
                    conversation_entity.update_context("user_created", True)
                    conversation_entity.update_context("registration_method", "form")
                    
                    # Move to next step - service selection
                    conversation_entity.update_step("service_selection")
                    
                    # Save updated conversation
                    await conv_repo.update_conversation(conversation_entity)
                    logger.info(f"Updated conversation {registration_data.conversation_id} with user data")
                
                return UserRegistrationResponseDTO(
                    user_id=created_user.id,
                    name=created_user.name,
                    email=created_user.email.value,
                    phone=created_user.phone.value,
                    success=True,
                    message=f"Usuario {created_user.name} registrado exitosamente",
                    conversation_updated=True
                )
                
            except ValueError as ve:
                # Handle duplicate user error
                if "already exists" in str(ve).lower():
                    logger.warning(f"User already exists: {registration_data.email}")
                    
                    # Find existing user
                    existing_user = await user_repo.find_by_email(Email(registration_data.email))
                    if existing_user:
                        # Update conversation with existing user
                        from ...infrastructure.dependencies import get_conversation_repository
                        conv_repo = await get_conversation_repository()
                        
                        conversation_entity = await conv_repo.get_conversation_by_id(registration_data.conversation_id)
                        if conversation_entity:
                            conversation_entity.update_context("user_id", existing_user.id)
                            conversation_entity.update_context("user_name", existing_user.name)
                            conversation_entity.update_context("user_email", existing_user.email.value)
                            conversation_entity.update_context("user_phone", existing_user.phone.value)
                            conversation_entity.update_context("user_found", True)
                            conversation_entity.update_context("registration_method", "form")
                            conversation_entity.update_step("service_selection")
                            await conv_repo.update_conversation(conversation_entity)
                        
                        return UserRegistrationResponseDTO(
                            user_id=existing_user.id,
                            name=existing_user.name,
                            email=existing_user.email.value,
                            phone=existing_user.phone.value,
                            success=True,
                            message=f"Bienvenido de nuevo {existing_user.name}",
                            conversation_updated=True
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="El correo ya está registrado pero no se pudo encontrar el usuario"
                        )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Error de validación: {str(ve)}"
                    )
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error registering user from form: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al registrar usuario: {str(e)}"
            )