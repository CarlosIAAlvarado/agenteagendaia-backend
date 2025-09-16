from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import logging
from ...application.use_cases.conversation_use_cases_v2 import ConversationUseCasesV2
from ...application.dto.conversation_dto import ChatMessageDTO, ConversationCreateDTO
from ...infrastructure.dependencies import get_conversation_use_cases

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_conversations: Dict[str, str] = {}  # user_id -> conversation_id
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and add to active connections"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user: {user_id}")
    
    def disconnect(self, user_id: str):
        """Remove connection from active connections"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_conversations:
            del self.user_conversations[user_id]
        logger.info(f"WebSocket disconnected for user: {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                # Remove disconnected connection
                self.disconnect(user_id)


manager = ConnectionManager()


class ChatWebSocketHandler:
    """Handles WebSocket communication for chat"""
    
    def __init__(self, conversation_use_cases: ConversationUseCasesV2):
        self.conversation_use_cases = conversation_use_cases
    
    async def handle_websocket(self, websocket: WebSocket, user_id: str):
        """Handle WebSocket connection for chat"""
        await manager.connect(websocket, user_id)
        
        try:
            # Check if user has active conversation, if not create one
            conversation_id = await self._ensure_conversation(user_id)
            manager.user_conversations[user_id] = conversation_id
            
            # Send initial connection confirmation
            await manager.send_personal_message({
                "type": "connection_established",
                "conversation_id": conversation_id,
                "message": "Conexión establecida. ¡Hola! ¿En qué puedo ayudarte hoy?"
            }, user_id)
            
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                await self._handle_message(user_id, conversation_id, message_data)
                
        except WebSocketDisconnect:
            manager.disconnect(user_id)
            logger.info(f"WebSocket disconnected for user: {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            manager.disconnect(user_id)
    
    async def _ensure_conversation(self, user_id: str) -> str:
        """Ensure user has an active conversation"""
        try:
            # Try to get existing active conversation
            conversations = await self.conversation_use_cases.get_user_conversations(user_id, 0, 1)
            
            if conversations and conversations[0].status == "active":
                return conversations[0].id
            
            # Create new conversation
            conversation_data = ConversationCreateDTO(
                user_id=user_id,
                channel="websocket"
            )
            
            conversation = await self.conversation_use_cases.start_conversation(conversation_data)
            return conversation.id
            
        except Exception as e:
            logger.error(f"Error ensuring conversation for user {user_id}: {e}")
            raise
    
    async def _handle_message(self, user_id: str, conversation_id: str, message_data: dict):
        """Handle incoming message from WebSocket"""
        try:
            message_type = message_data.get("type", "chat_message")
            
            if message_type == "chat_message":
                await self._handle_chat_message(user_id, conversation_id, message_data)
            elif message_type == "typing_indicator":
                await self._handle_typing_indicator(user_id, message_data)
            elif message_type == "quick_reply":
                await self._handle_quick_reply(user_id, conversation_id, message_data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")
            await manager.send_personal_message({
                "type": "error",
                "message": "Error procesando el mensaje. Por favor, intenta de nuevo."
            }, user_id)
    
    async def _handle_chat_message(self, user_id: str, conversation_id: str, message_data: dict):
        """Handle regular chat message"""
        try:
            content = message_data.get("content", "").strip()
            if not content:
                return
            
            # Create message DTO
            chat_message = ChatMessageDTO(
                content=content,
                user_id=user_id,
                metadata=message_data.get("metadata", {})
            )
            
            # Process message through conversation use cases
            response = await self.conversation_use_cases.send_message(conversation_id, chat_message)
            
            # Send AI response back to user
            await manager.send_personal_message({
                "type": "ai_response",
                "conversation_id": conversation_id,
                "message": response.message,
                "intent": response.intent,
                "confidence": response.confidence,
                "context": response.context,
                "step": response.step,
                "timestamp": response.timestamp,
                "suggestions": response.suggestions
            }, user_id)
            
            # Send quick replies if available
            await self._send_quick_replies(user_id, conversation_id)
            
        except Exception as e:
            logger.error(f"Error handling chat message from user {user_id}: {e}")
            await manager.send_personal_message({
                "type": "error",
                "message": "Error procesando el mensaje. Por favor, intenta de nuevo."
            }, user_id)
    
    async def _handle_typing_indicator(self, user_id: str, message_data: dict):
        """Handle typing indicator (could be used for analytics)"""
        # For now, just log typing indicators
        is_typing = message_data.get("is_typing", False)
        logger.debug(f"User {user_id} typing: {is_typing}")
    
    async def _handle_quick_reply(self, user_id: str, conversation_id: str, message_data: dict):
        """Handle quick reply selection"""
        try:
            reply_value = message_data.get("value", "")
            reply_text = message_data.get("text", reply_value)
            
            # Treat quick reply as regular message
            await self._handle_chat_message(user_id, conversation_id, {
                "content": reply_text,
                "metadata": {
                    "source": "quick_reply",
                    "reply_value": reply_value
                }
            })
            
        except Exception as e:
            logger.error(f"Error handling quick reply from user {user_id}: {e}")
    
    async def _send_quick_replies(self, user_id: str, conversation_id: str):
        """Send available quick replies to user"""
        try:
            # Get conversation to check current step
            conversation = await self.conversation_use_cases.get_conversation_by_id(conversation_id)
            if not conversation:
                return
            
            quick_replies = []
            step = conversation.current_step
            
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
            
            if quick_replies:
                await manager.send_personal_message({
                    "type": "quick_replies",
                    "conversation_id": conversation_id,
                    "replies": quick_replies
                }, user_id)
                
        except Exception as e:
            logger.error(f"Error sending quick replies to user {user_id}: {e}")


async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    conversation_use_cases: ConversationUseCasesV2 = Depends(get_conversation_use_cases)
):
    """WebSocket endpoint for real-time chat"""
    handler = ChatWebSocketHandler(conversation_use_cases)
    await handler.handle_websocket(websocket, user_id)