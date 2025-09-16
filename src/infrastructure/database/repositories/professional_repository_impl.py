from typing import List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from ....domain.entities.professional import Professional, WeekDay
from ....domain.value_objects.email import Email
from ....domain.value_objects.phone import Phone
from ....domain.repositories.professional_repository import IProfessionalRepository
from ..mappers.professional_mapper import ProfessionalMapper
from ..connection import get_database
import logging

logger = logging.getLogger(__name__)


class ProfessionalRepositoryImpl(IProfessionalRepository):
    """MongoDB implementation of IProfessionalRepository"""
    
    def __init__(self):
        self._collection_name = "professionals"
    
    async def _get_collection(self):
        """Get professionals collection from database"""
        db = await get_database()
        return db[self._collection_name]
    
    async def create(self, professional: Professional) -> Professional:
        """Create a new professional"""
        try:
            collection = await self._get_collection()
            professional_doc = ProfessionalMapper.to_document(professional)
            
            # Remove _id if it exists (let MongoDB generate it)
            if "_id" in professional_doc:
                del professional_doc["_id"]
            
            result = await collection.insert_one(professional_doc)
            
            # Update professional with generated ID
            professional.id = str(result.inserted_id)
            
            logger.info(f"Created professional with ID: {professional.id}")
            return professional
            
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error creating professional: {e}")
            if "email" in str(e):
                raise ValueError(f"Professional with email {professional.email.value} already exists")
            elif "phone" in str(e):
                raise ValueError(f"Professional with phone {professional.phone.value} already exists")
            raise ValueError("Professional with this email or phone already exists")
        except Exception as e:
            logger.error(f"Error creating professional: {e}")
            raise
    
    async def get_by_id(self, professional_id: str) -> Optional[Professional]:
        """Get professional by ID"""
        try:
            collection = await self._get_collection()
            
            doc = await collection.find_one({"_id": ObjectId(professional_id)})
            
            if doc:
                return ProfessionalMapper.from_document(doc)
            return None
            
        except InvalidId:
            logger.warning(f"Invalid professional ID format: {professional_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting professional by ID {professional_id}: {e}")
            raise
    
    async def get_by_email(self, email: Email) -> Optional[Professional]:
        """Get professional by email"""
        try:
            collection = await self._get_collection()
            
            doc = await collection.find_one({"email.value": email.value.lower()})
            
            if doc:
                return ProfessionalMapper.from_document(doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting professional by email {email.value}: {e}")
            raise
    
    async def get_by_phone(self, phone: Phone) -> Optional[Professional]:
        """Get professional by phone"""
        try:
            collection = await self._get_collection()
            
            doc = await collection.find_one({"phone.value": phone.value})
            
            if doc:
                return ProfessionalMapper.from_document(doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting professional by phone {phone.value}: {e}")
            raise
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Professional]:
        """Get all professionals with pagination"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)
            
            logger.info(f"Retrieved {len(docs)} professional documents from database")
            
            if not docs:
                logger.info("No professionals found in database")
                return []
            
            # Debug: log structure of first document
            if docs:
                logger.info(f"Sample document structure: {list(docs[0].keys()) if docs[0] else 'Empty document'}")
            
            professionals = []
            for doc in docs:
                try:
                    professional = ProfessionalMapper.from_document(doc)
                    professionals.append(professional)
                except Exception as map_error:
                    logger.error(f"Error mapping document to professional: {map_error}")
                    logger.error(f"Document causing error: {doc}")
                    # Skip this document and continue
                    continue
            
            return professionals
            
        except Exception as e:
            logger.error(f"Error getting all professionals: {e}")
            raise
    
    async def get_active_professionals(self, skip: int = 0, limit: int = 100) -> List[Professional]:
        """Get all active professionals"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({"is_active": True}).skip(skip).limit(limit).sort("name", 1)
            docs = await cursor.to_list(length=limit)
            
            return [ProfessionalMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting active professionals: {e}")
            raise
    
    async def get_by_service_id(self, service_id: str) -> List[Professional]:
        """Get professionals who provide a specific service"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "service_ids": service_id,
                "is_active": True
            }).sort("name", 1)
            
            docs = await cursor.to_list(length=None)
            
            return [ProfessionalMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting professionals by service ID {service_id}: {e}")
            raise
    
    async def get_by_specialization(self, specialization: str) -> List[Professional]:
        """Get professionals by specialization"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "specialization": {"$regex": specialization, "$options": "i"},
                "is_active": True
            }).sort("name", 1)
            
            docs = await cursor.to_list(length=None)
            
            return [ProfessionalMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting professionals by specialization '{specialization}': {e}")
            raise
    
    async def get_available_on_day(self, day: WeekDay) -> List[Professional]:
        """Get professionals available on a specific day"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "working_hours": {
                    "$elemMatch": {
                        "day": day.value,
                        "is_available": True
                    }
                },
                "is_active": True
            }).sort("name", 1)
            
            docs = await cursor.to_list(length=None)
            
            return [ProfessionalMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting professionals available on {day.value}: {e}")
            raise
    
    async def get_by_service_and_day(self, service_id: str, day: WeekDay) -> List[Professional]:
        """Get professionals who provide service and are available on specific day"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "$and": [
                    {"service_ids": service_id},
                    {
                        "working_hours": {
                            "$elemMatch": {
                                "day": day.value,
                                "is_available": True
                            }
                        }
                    },
                    {"is_active": True}
                ]
            }).sort("name", 1)
            
            docs = await cursor.to_list(length=None)
            
            return [ProfessionalMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting professionals by service {service_id} and day {day.value}: {e}")
            raise
    
    async def update(self, professional: Professional) -> Professional:
        """Update existing professional"""
        try:
            if not professional.id:
                raise ValueError("Professional ID is required for update")
            
            collection = await self._get_collection()
            update_doc = ProfessionalMapper.to_update_document(professional)
            
            result = await collection.update_one(
                {"_id": ObjectId(professional.id)},
                update_doc
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Professional with ID {professional.id} not found")
            
            logger.info(f"Updated professional with ID: {professional.id}")
            return professional
            
        except InvalidId:
            raise ValueError(f"Invalid professional ID format: {professional.id}")
        except Exception as e:
            logger.error(f"Error updating professional {professional.id}: {e}")
            raise
    
    async def delete(self, professional_id: str) -> bool:
        """Delete professional by ID"""
        try:
            collection = await self._get_collection()
            
            result = await collection.delete_one({"_id": ObjectId(professional_id)})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted professional with ID: {professional_id}")
            else:
                logger.warning(f"Professional with ID {professional_id} not found for deletion")
            
            return success
            
        except InvalidId:
            logger.warning(f"Invalid professional ID format: {professional_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting professional {professional_id}: {e}")
            raise
    
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Professional]:
        """Search professionals by name"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "$or": [
                    {"name": {"$regex": name, "$options": "i"}},
                    {"specialization": {"$regex": name, "$options": "i"}}
                ],
                "is_active": True
            }).skip(skip).limit(limit).sort("name", 1)
            
            docs = await cursor.to_list(length=limit)
            
            return [ProfessionalMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error searching professionals by name '{name}': {e}")
            raise
    
    async def exists_by_email(self, email: Email) -> bool:
        """Check if professional exists by email"""
        try:
            collection = await self._get_collection()
            
            count = await collection.count_documents({"email.value": email.value.lower()})
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking if professional exists by email {email.value}: {e}")
            raise
    
    async def exists_by_phone(self, phone: Phone) -> bool:
        """Check if professional exists by phone"""
        try:
            collection = await self._get_collection()
            
            count = await collection.count_documents({"phone.value": phone.value})
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking if professional exists by phone {phone.value}: {e}")
            raise
    
    async def count_total(self) -> int:
        """Count total professionals"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({})
            
        except Exception as e:
            logger.error(f"Error counting total professionals: {e}")
            raise
    
    async def count_active(self) -> int:
        """Count active professionals"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"is_active": True})
            
        except Exception as e:
            logger.error(f"Error counting active professionals: {e}")
            raise
    
    async def count_by_specialization(self, specialization: str) -> int:
        """Count professionals by specialization"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({
                "specialization": {"$regex": specialization, "$options": "i"},
                "is_active": True
            })
            
        except Exception as e:
            logger.error(f"Error counting professionals by specialization '{specialization}': {e}")
            raise