from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from ....domain.entities.conversation import Conversation, Message, MessageRole, IntentType, ConversationStatus


class ConversationMapper:
    """Maps between Conversation/Message domain entities and MongoDB documents"""
    
    @staticmethod
    def to_document(conversation: Conversation) -> Dict[str, Any]:
        """Convert Conversation entity to MongoDB document"""
        doc = {
            "user_id": conversation.user_id,
            "status": conversation.status.value,
            "current_step": conversation.current_step,
            "context": conversation.context,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "completed_at": conversation.completed_at
        }
        
        if conversation.id is not None:
            doc["_id"] = ObjectId(conversation.id)
        
        return doc
    
    @staticmethod
    def from_document(doc: Dict[str, Any]) -> Conversation:
        """Convert MongoDB document to Conversation entity"""
        conversation_id = str(doc["_id"]) if "_id" in doc else None
        
        return Conversation(
            id=conversation_id,
            user_id=doc.get("user_id"),
            status=ConversationStatus(doc["status"]),
            current_step=doc.get("current_step", "greeting"),
            context=doc.get("context", {}),
            messages=[],  # Messages loaded separately
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at"),
            completed_at=doc.get("completed_at")
        )
    
    @staticmethod
    def to_update_document(conversation: Conversation) -> Dict[str, Any]:
        """Convert Conversation entity to MongoDB update document"""
        update_doc = {
            "$set": {
                "user_id": conversation.user_id,
                "status": conversation.status.value,
                "current_step": conversation.current_step,
                "context": conversation.context,
                "updated_at": datetime.utcnow(),
                "completed_at": conversation.completed_at
            }
        }
        
        return update_doc
    
    @staticmethod
    def message_to_document(message: Message) -> Dict[str, Any]:
        """Convert Message entity to MongoDB document"""
        doc = {
            "conversation_id": message.conversation_id,
            "role": message.role.value,
            "content": message.content,
            "intent": message.intent.value if message.intent else None,
            "confidence": message.confidence,
            "entities": message.entities,
            "metadata": message.metadata,
            "created_at": message.created_at
        }
        
        if message.id is not None:
            doc["_id"] = ObjectId(message.id)
        
        return doc
    
    @staticmethod
    def message_from_document(doc: Dict[str, Any]) -> Message:
        """Convert MongoDB document to Message entity"""
        message_id = str(doc["_id"]) if "_id" in doc else None
        
        intent = None
        if doc.get("intent"):
            intent = IntentType(doc["intent"])
        
        return Message(
            id=message_id,
            conversation_id=doc["conversation_id"],
            role=MessageRole(doc["role"]),
            content=doc["content"],
            intent=intent,
            confidence=doc.get("confidence"),
            entities=doc.get("entities", {}),
            metadata=doc.get("metadata", {}),
            created_at=doc["created_at"]
        )