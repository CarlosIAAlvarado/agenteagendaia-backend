from typing import List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from ....domain.entities.patient import Patient
from ....domain.value_objects.email import Email
from ....domain.value_objects.phone import Phone
from ....domain.repositories.user_repository import IUserRepository
from ..mappers.user_mapper import UserMapper
from ..connection import get_database
import logging

logger = logging.getLogger(__name__)


class UserRepositoryImpl(IUserRepository):
    """MongoDB implementation of IUserRepository"""
    
    def __init__(self):
        self._collection_name = "users"
    
    async def _get_collection(self):
        """Get users collection from database"""
        db = await get_database()
        return db[self._collection_name]
    
    async def create(self, user: Patient) -> Patient:
        """Create a new user"""
        try:
            collection = await self._get_collection()
            user_doc = UserMapper.to_document(user)
            
            # Remove _id if it exists (let MongoDB generate it)
            if "_id" in user_doc:
                del user_doc["_id"]
            
            result = await collection.insert_one(user_doc)
            
            # Update user with generated ID
            user.id = str(result.inserted_id)
            
            logger.info(f"Created user with ID: {user.id}")
            return user
            
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error creating user: {e}")
            if "email" in str(e):
                raise ValueError(f"Patient with email {user.email.value} already exists")
            elif "phone" in str(e):
                raise ValueError(f"Patient with phone {user.phone.value} already exists")
            raise ValueError("Patient with this email or phone already exists")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_by_id(self, user_id: str) -> Optional[Patient]:
        """Get user by ID"""
        try:
            collection = await self._get_collection()
            
            doc = await collection.find_one({"_id": ObjectId(user_id)})
            
            if doc:
                return UserMapper.from_document(doc)
            return None
            
        except InvalidId:
            logger.warning(f"Invalid user ID format: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise
    
    async def get_by_email(self, email: Email) -> Optional[Patient]:
        """Get user by email"""
        try:
            collection = await self._get_collection()
            
            doc = await collection.find_one({"email.value": email.value.lower()})
            
            if doc:
                return UserMapper.from_document(doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email {email.value}: {e}")
            raise
    
    async def get_by_phone(self, phone: Phone) -> Optional[Patient]:
        """Get user by phone number"""
        try:
            collection = await self._get_collection()
            
            doc = await collection.find_one({"phone.value": phone.value})
            
            if doc:
                return UserMapper.from_document(doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by phone {phone.value}: {e}")
            raise
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Get all users with pagination"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)
            
            return [UserMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            raise
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Get all active users"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({"is_active": True}).skip(skip).limit(limit).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)
            
            return [UserMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            raise
    
    async def update(self, user: Patient) -> Patient:
        """Update existing user"""
        try:
            if not user.id:
                raise ValueError("Patient ID is required for update")
            
            collection = await self._get_collection()
            update_doc = UserMapper.to_update_document(user)
            
            result = await collection.update_one(
                {"_id": ObjectId(user.id)},
                update_doc
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Patient with ID {user.id} not found")
            
            logger.info(f"Updated user with ID: {user.id}")
            return user
            
        except InvalidId:
            raise ValueError(f"Invalid user ID format: {user.id}")
        except Exception as e:
            logger.error(f"Error updating user {user.id}: {e}")
            raise
    
    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        try:
            collection = await self._get_collection()
            
            result = await collection.delete_one({"_id": ObjectId(user_id)})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted user with ID: {user_id}")
            else:
                logger.warning(f"Patient with ID {user_id} not found for deletion")
            
            return success
            
        except InvalidId:
            logger.warning(f"Invalid user ID format: {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise
    
    async def exists_by_email(self, email: Email) -> bool:
        """Check if user exists by email"""
        try:
            collection = await self._get_collection()
            
            count = await collection.count_documents({"email.value": email.value.lower()})
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking if user exists by email {email.value}: {e}")
            raise
    
    async def exists_by_phone(self, phone: Phone) -> bool:
        """Check if user exists by phone"""
        try:
            collection = await self._get_collection()
            
            count = await collection.count_documents({"phone.value": phone.value})
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking if user exists by phone {phone.value}: {e}")
            raise
    
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Search users by name"""
        try:
            collection = await self._get_collection()
            
            # Use text search if available, otherwise regex
            cursor = collection.find({
                "name": {"$regex": name, "$options": "i"}
            }).skip(skip).limit(limit).sort("name", 1)
            
            docs = await cursor.to_list(length=limit)
            
            return [UserMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error searching users by name '{name}': {e}")
            raise
    
    async def count_total(self) -> int:
        """Count total users"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({})
            
        except Exception as e:
            logger.error(f"Error counting total users: {e}")
            raise
    
    async def count_active(self) -> int:
        """Count active users"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"is_active": True})
            
        except Exception as e:
            logger.error(f"Error counting active users: {e}")
            raise