from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from bson.errors import InvalidId
from ....domain.entities.conversation import Conversation, Message, MessageRole, IntentType, ConversationStatus
from ....domain.repositories.conversation_repository import IConversationRepository
from ..mappers.conversation_mapper import ConversationMapper
from ..connection import get_database
import logging

logger = logging.getLogger(__name__)


class ConversationRepositoryImpl(IConversationRepository):
    """MongoDB implementation of IConversationRepository"""
    
    def __init__(self):
        self._conversations_collection = "conversations"
        self._messages_collection = "messages"
    
    async def _get_conversations_collection(self):
        """Get conversations collection from database"""
        db = await get_database()
        return db[self._conversations_collection]
    
    async def _get_messages_collection(self):
        """Get messages collection from database"""
        db = await get_database()
        return db[self._messages_collection]
    
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation"""
        try:
            collection = await self._get_conversations_collection()
            conversation_doc = ConversationMapper.to_document(conversation)
            
            # Remove _id if it exists (let MongoDB generate it)
            if "_id" in conversation_doc:
                del conversation_doc["_id"]
            
            result = await collection.insert_one(conversation_doc)
            
            # Update conversation with generated ID
            conversation.id = str(result.inserted_id)
            
            logger.info(f"Created conversation with ID: {conversation.id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        try:
            collection = await self._get_conversations_collection()
            
            doc = await collection.find_one({"_id": ObjectId(conversation_id)})
            
            if doc is not None:
                conversation = ConversationMapper.from_document(doc)
                # Load messages
                conversation.messages = await self.get_conversation_messages(conversation_id)
                return conversation
            return None
            
        except InvalidId:
            logger.warning(f"Invalid conversation ID format: {conversation_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting conversation by ID {conversation_id}: {e}")
            raise
    
    async def get_active_conversation_by_user(self, user_id: str) -> Optional[Conversation]:
        """Get active conversation for user"""
        try:
            collection = await self._get_conversations_collection()
            
            doc = await collection.find_one({
                "user_id": user_id,
                "status": ConversationStatus.ACTIVE.value
            })
            
            if doc is not None:
                conversation = ConversationMapper.from_document(doc)
                conversation.messages = await self.get_conversation_messages(conversation.id)
                return conversation
            return None
            
        except Exception as e:
            logger.error(f"Error getting active conversation for user {user_id}: {e}")
            raise
    
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update existing conversation"""
        try:
            if conversation.id is None:
                raise ValueError("Conversation ID is required for update")
            
            collection = await self._get_conversations_collection()
            update_doc = ConversationMapper.to_update_document(conversation)
            
            result = await collection.update_one(
                {"_id": ObjectId(conversation.id)},
                update_doc
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Conversation with ID {conversation.id} not found")
            
            logger.info(f"Updated conversation with ID: {conversation.id}")
            return conversation
            
        except InvalidId:
            raise ValueError(f"Invalid conversation ID format: {conversation.id}")
        except Exception as e:
            logger.error(f"Error updating conversation {conversation.id}: {e}")
            raise
    
    async def add_message(self, message: Message) -> Message:
        """Add message to conversation"""
        try:
            collection = await self._get_messages_collection()
            message_doc = ConversationMapper.message_to_document(message)
            
            # Remove _id if it exists (let MongoDB generate it)
            if "_id" in message_doc:
                del message_doc["_id"]
            
            result = await collection.insert_one(message_doc)
            
            # Update message with generated ID
            message.id = str(result.inserted_id)
            
            logger.info(f"Added message with ID: {message.id}")
            return message
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 100
    ) -> List[Message]:
        """Get messages for a conversation"""
        try:
            collection = await self._get_messages_collection()
            
            cursor = collection.find({
                "conversation_id": conversation_id
            }).sort("created_at", 1).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            
            return [ConversationMapper.message_from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            return []
    
    async def get_conversations_by_user(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Conversation]:
        """Get conversations for a user"""
        try:
            collection = await self._get_conversations_collection()
            
            cursor = collection.find({
                "user_id": user_id
            }).sort("created_at", -1).skip(skip).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            
            conversations = []
            for doc in docs:
                conversation = ConversationMapper.from_document(doc)
                # Load recent messages (last 5)
                conversation.messages = await self.get_conversation_messages(
                    conversation.id, limit=5
                )
                conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {e}")
            return []
    
    async def get_conversations_by_status(
        self, 
        status: ConversationStatus, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Conversation]:
        """Get conversations by status"""
        try:
            collection = await self._get_conversations_collection()
            
            cursor = collection.find({
                "status": status.value
            }).sort("updated_at", -1).skip(skip).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            
            return [ConversationMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting conversations by status {status.value}: {e}")
            return []
    
    async def get_abandoned_conversations(self, timeout_minutes: int = 30) -> List[Conversation]:
        """Get conversations that should be marked as abandoned"""
        try:
            collection = await self._get_conversations_collection()
            
            timeout_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            
            cursor = collection.find({
                "status": ConversationStatus.ACTIVE.value,
                "updated_at": {"$lt": timeout_time}
            })
            
            docs = await cursor.to_list(length=None)
            
            return [ConversationMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting abandoned conversations: {e}")
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all its messages"""
        try:
            conversations_collection = await self._get_conversations_collection()
            messages_collection = await self._get_messages_collection()
            
            # Delete messages first
            await messages_collection.delete_many({"conversation_id": conversation_id})
            
            # Delete conversation
            result = await conversations_collection.delete_one({"_id": ObjectId(conversation_id)})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted conversation with ID: {conversation_id}")
            else:
                logger.warning(f"Conversation with ID {conversation_id} not found for deletion")
            
            return success
            
        except InvalidId:
            logger.warning(f"Invalid conversation ID format: {conversation_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            raise
    
    async def count_conversations_by_status(self, status: ConversationStatus) -> int:
        """Count conversations by status"""
        try:
            collection = await self._get_conversations_collection()
            return await collection.count_documents({"status": status.value})
            
        except Exception as e:
            logger.error(f"Error counting conversations by status {status.value}: {e}")
            return 0
    
    async def count_conversations_by_user(self, user_id: str) -> int:
        """Count conversations for a user"""
        try:
            collection = await self._get_conversations_collection()
            return await collection.count_documents({"user_id": user_id})
            
        except Exception as e:
            logger.error(f"Error counting conversations for user {user_id}: {e}")
            return 0
    
    async def get_conversation_analytics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> dict:
        """Get conversation analytics for date range"""
        try:
            collection = await self._get_conversations_collection()
            
            pipeline = [
                {
                    "$match": {
                        "created_at": {
                            "$gte": start_date,
                            "$lte": end_date
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "avg_duration": {"$avg": "$duration_minutes"}
                    }
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            analytics = {}
            for result in results:
                status = result["_id"]
                analytics[status] = {
                    "count": result["count"],
                    "avg_duration": result.get("avg_duration", 0)
                }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {e}")
            return {}