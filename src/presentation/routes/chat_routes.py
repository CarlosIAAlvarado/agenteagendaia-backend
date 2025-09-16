from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime
from ..controllers.chat_controller import ChatController
from ...application.dto.conversation_dto import (
    ChatMessageDTO, ChatResponseDTO, ConversationCreateDTO, ConversationResponseDTO,
    ConversationListResponseDTO, EscalationRequestDTO, ConversationAnalyticsDTO,
    ConversationSearchDTO, UserRegistrationDTO, UserRegistrationResponseDTO
)
from ...application.use_cases.conversation_use_cases_v2 import ConversationUseCasesV2
from ...infrastructure.dependencies import get_conversation_use_cases
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_controller(
    conversation_use_cases: ConversationUseCasesV2 = Depends(get_conversation_use_cases)
) -> ChatController:
    """Dependency to get ChatController instance"""
    return ChatController(conversation_use_cases)


@router.post("/conversations", response_model=ConversationResponseDTO)
async def start_conversation(
    conversation_data: ConversationCreateDTO,
    controller: ChatController = Depends(get_chat_controller)
) -> ConversationResponseDTO:
    """Start a new conversation"""
    return await controller.start_conversation(conversation_data)


@router.post("/register-user-form", response_model=UserRegistrationResponseDTO)
async def register_user_from_form_v2(
    registration_data: UserRegistrationDTO,
    controller: ChatController = Depends(get_chat_controller)
) -> UserRegistrationResponseDTO:
    """Register user directly from form data - structured data approach (v2)"""
    logger.info(f"🔥 ENDPOINT V2 CALLED: register_user_from_form with data: {registration_data}")
    return await controller.register_user_from_form(registration_data)


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponseDTO)
async def send_message(
    conversation_id: str,
    message_data: ChatMessageDTO,
    controller: ChatController = Depends(get_chat_controller)
) -> ChatResponseDTO:
    """Send message to conversation and get AI response"""
    return await controller.send_message(conversation_id, message_data)




@router.get("/conversations/{conversation_id}", response_model=ConversationResponseDTO)
async def get_conversation(
    conversation_id: str,
    controller: ChatController = Depends(get_chat_controller)
) -> ConversationResponseDTO:
    """Get conversation by ID"""
    return await controller.get_conversation(conversation_id)


@router.get("/users/{user_id}/conversations", response_model=ConversationListResponseDTO)
async def get_user_conversations(
    user_id: str,
    skip: int = Query(0, ge=0, description="Number of conversations to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of conversations to return"),
    controller: ChatController = Depends(get_chat_controller)
) -> ConversationListResponseDTO:
    """Get conversations for a user"""
    return await controller.get_user_conversations(user_id, skip, limit)


@router.post("/conversations/{conversation_id}/end", response_model=ConversationResponseDTO)
async def end_conversation(
    conversation_id: str,
    controller: ChatController = Depends(get_chat_controller)
) -> ConversationResponseDTO:
    """End an active conversation"""
    return await controller.end_conversation(conversation_id)


@router.post("/conversations/{conversation_id}/escalate", response_model=ConversationResponseDTO)
async def escalate_conversation(
    conversation_id: str,
    escalation_data: EscalationRequestDTO,
    controller: ChatController = Depends(get_chat_controller)
) -> ConversationResponseDTO:
    """Escalate conversation to human agent"""
    return await controller.escalate_conversation(conversation_id, escalation_data)


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200, description="Number of messages to return"),
    controller: ChatController = Depends(get_chat_controller)
) -> List[dict]:
    """Get messages for a conversation"""
    return await controller.get_conversation_messages(conversation_id, limit)


@router.get("/analytics/conversations", response_model=ConversationAnalyticsDTO)
async def get_conversation_analytics(
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DDTHH:MM:SS)"),
    end_date: str = Query(..., description="End date in ISO format (YYYY-MM-DDTHH:MM:SS)"),
    controller: ChatController = Depends(get_chat_controller)
) -> ConversationAnalyticsDTO:
    """Get conversation analytics for date range"""
    return await controller.get_conversation_analytics(start_date, end_date)


@router.post("/admin/cleanup")
async def cleanup_abandoned_conversations(
    controller: ChatController = Depends(get_chat_controller)
) -> dict:
    """Clean up abandoned conversations (admin endpoint)"""
    return await controller.cleanup_abandoned_conversations()


@router.post("/conversations/search", response_model=ConversationListResponseDTO)
async def search_conversations(
    search_params: ConversationSearchDTO,
    controller: ChatController = Depends(get_chat_controller)
) -> ConversationListResponseDTO:
    """Search conversations with filters"""
    return await controller.search_conversations(search_params)


@router.get("/conversations/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: str,
    controller: ChatController = Depends(get_chat_controller)
) -> dict:
    """Get conversation context"""
    return await controller.get_conversation_context(conversation_id)


@router.get("/conversations/{conversation_id}/quick-replies")
async def get_quick_replies(
    conversation_id: str,
    controller: ChatController = Depends(get_chat_controller)
) -> List[dict]:
    """Get suggested quick replies based on conversation context"""
    return await controller.get_quick_replies(conversation_id)


@router.get("/health")
async def chat_health_check() -> dict:
    """Health check for chat service"""
    return {
        "status": "healthy",
        "service": "chat",
        "timestamp": datetime.utcnow().isoformat()
    }


