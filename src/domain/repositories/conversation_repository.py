from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..entities.conversation import Conversation, Message, ConversationStatus


class IConversationRepository(ABC):
    """Interface for Conversation repository following Repository pattern"""
    
    @abstractmethod
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation"""
        pass
    
    @abstractmethod
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        pass
    
    @abstractmethod
    async def get_active_conversation_by_user(self, user_id: str) -> Optional[Conversation]:
        """Get active conversation for user"""
        pass
    
    @abstractmethod
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update existing conversation"""
        pass
    
    @abstractmethod
    async def add_message(self, message: Message) -> Message:
        """Add message to conversation"""
        pass
    
    @abstractmethod
    async def get_conversation_messages(self, conversation_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a conversation"""
        pass
    
    @abstractmethod
    async def get_conversations_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Conversation]:
        """Get conversations for a user"""
        pass
    
    @abstractmethod
    async def get_conversations_by_status(self, status: ConversationStatus, skip: int = 0, limit: int = 50) -> List[Conversation]:
        """Get conversations by status"""
        pass
    
    @abstractmethod
    async def get_abandoned_conversations(self, timeout_minutes: int = 30) -> List[Conversation]:
        """Get conversations that should be marked as abandoned"""
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all its messages"""
        pass
    
    @abstractmethod
    async def count_conversations_by_status(self, status: ConversationStatus) -> int:
        """Count conversations by status"""
        pass
    
    @abstractmethod
    async def count_conversations_by_user(self, user_id: str) -> int:
        """Count conversations for a user"""
        pass
    
    @abstractmethod
    async def get_conversation_analytics(self, start_date: datetime, end_date: datetime) -> dict:
        """Get conversation analytics for date range"""
        pass