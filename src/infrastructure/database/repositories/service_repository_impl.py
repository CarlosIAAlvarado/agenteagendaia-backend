from typing import List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from ....domain.entities.service import Service, ServiceType, ServiceMode
from ....domain.repositories.service_repository import IServiceRepository
from ..mappers.service_mapper import ServiceMapper
from ..connection import get_database
import logging

logger = logging.getLogger(__name__)


class ServiceRepositoryImpl(IServiceRepository):
    """MongoDB implementation of IServiceRepository"""
    
    def __init__(self):
        self._collection_name = "services"
    
    async def _get_collection(self):
        """Get services collection from database"""
        db = await get_database()
        return db[self._collection_name]
    
    async def create(self, service: Service) -> Service:
        """Create a new service"""
        try:
            collection = await self._get_collection()
            service_doc = ServiceMapper.to_document(service)
            
            # Remove _id if it exists (let MongoDB generate it)
            if "_id" in service_doc:
                del service_doc["_id"]
            
            result = await collection.insert_one(service_doc)
            
            # Update service with generated ID
            service.id = str(result.inserted_id)
            
            logger.info(f"Created service with ID: {service.id}")
            return service
            
        except DuplicateKeyError:
            logger.error(f"Ya existe un servicio con el nombre '{service.name}'")
            raise ValueError(f"Ya existe un servicio con el nombre '{service.name}'. Por favor, elige un nombre diferente.")
        except Exception as e:
            logger.error(f"Error creating service: {e}")
            raise
    
    async def get_by_id(self, service_id: str) -> Optional[Service]:
        """Get service by ID"""
        try:
            collection = await self._get_collection()
            
            doc = await collection.find_one({"_id": ObjectId(service_id)})
            
            if doc:
                return ServiceMapper.from_document(doc)
            return None
            
        except InvalidId:
            logger.warning(f"Invalid service ID format: {service_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting service by ID {service_id}: {e}")
            raise
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get all services with pagination"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)
            
            return [ServiceMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting all services: {e}")
            raise
    
    async def get_active_services(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get all active services"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({"is_active": True}).skip(skip).limit(limit).sort("name", 1)
            docs = await cursor.to_list(length=limit)
            
            return [ServiceMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting active services: {e}")
            raise
    
    async def get_by_type(self, service_type: ServiceType, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get services by type"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "service_type": service_type.value,
                "is_active": True
            }).skip(skip).limit(limit).sort("name", 1)
            
            docs = await cursor.to_list(length=limit)
            
            return [ServiceMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting services by type {service_type.value}: {e}")
            raise
    
    async def get_by_mode(self, service_mode: ServiceMode, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get services by mode (presential/virtual/both)"""
        try:
            collection = await self._get_collection()
            
            filter_query = {"is_active": True}
            
            if service_mode == ServiceMode.BOTH:
                filter_query["service_mode"] = {"$in": [ServiceMode.BOTH.value]}
            else:
                filter_query["service_mode"] = {"$in": [service_mode.value, ServiceMode.BOTH.value]}
            
            cursor = collection.find(filter_query).skip(skip).limit(limit).sort("name", 1)
            docs = await cursor.to_list(length=limit)
            
            return [ServiceMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting services by mode {service_mode.value}: {e}")
            raise
    
    async def get_by_duration_range(self, min_duration: int, max_duration: int) -> List[Service]:
        """Get services by duration range"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "duration_minutes": {"$gte": min_duration, "$lte": max_duration},
                "is_active": True
            }).sort("duration_minutes", 1)
            
            docs = await cursor.to_list(length=None)
            
            return [ServiceMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting services by duration range {min_duration}-{max_duration}: {e}")
            raise
    
    async def get_by_price_range(self, min_price: float, max_price: float) -> List[Service]:
        """Get services by price range"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "price": {"$gte": min_price, "$lte": max_price, "$ne": None},
                "is_active": True
            }).sort("price", 1)
            
            docs = await cursor.to_list(length=None)
            
            return [ServiceMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting services by price range {min_price}-{max_price}: {e}")
            raise
    
    async def update(self, service: Service) -> Service:
        """Update existing service"""
        try:
            if not service.id:
                raise ValueError("Service ID is required for update")
            
            collection = await self._get_collection()
            update_doc = ServiceMapper.to_update_document(service)
            
            result = await collection.update_one(
                {"_id": ObjectId(service.id)},
                update_doc
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Service with ID {service.id} not found")
            
            logger.info(f"Updated service with ID: {service.id}")
            return service
            
        except InvalidId:
            raise ValueError(f"Invalid service ID format: {service.id}")
        except Exception as e:
            logger.error(f"Error updating service {service.id}: {e}")
            raise
    
    async def delete(self, service_id: str) -> bool:
        """Delete service by ID"""
        try:
            collection = await self._get_collection()
            
            result = await collection.delete_one({"_id": ObjectId(service_id)})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted service with ID: {service_id}")
            else:
                logger.warning(f"Service with ID {service_id} not found for deletion")
            
            return success
            
        except InvalidId:
            logger.warning(f"Invalid service ID format: {service_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting service {service_id}: {e}")
            raise
    
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Service]:
        """Search services by name"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "$or": [
                    {"name": {"$regex": name, "$options": "i"}},
                    {"description": {"$regex": name, "$options": "i"}}
                ],
                "is_active": True
            }).skip(skip).limit(limit).sort("name", 1)
            
            docs = await cursor.to_list(length=limit)
            
            return [ServiceMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error searching services by name '{name}': {e}")
            raise
    
    async def exists_by_name(self, name: str) -> bool:
        """Check if service exists by name"""
        try:
            collection = await self._get_collection()
            
            # Use exact case-sensitive match instead of regex for better performance and reliability
            count = await collection.count_documents({"name": name})
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking if service exists by name '{name}': {e}")
            raise
    
    async def count_total(self) -> int:
        """Count total services"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({})
            
        except Exception as e:
            logger.error(f"Error counting total services: {e}")
            raise
    
    async def count_active(self) -> int:
        """Count active services"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"is_active": True})
            
        except Exception as e:
            logger.error(f"Error counting active services: {e}")
            raise
    
    async def count_by_type(self, service_type: ServiceType) -> int:
        """Count services by type"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({
                "service_type": service_type.value,
                "is_active": True
            })
            
        except Exception as e:
            logger.error(f"Error counting services by type {service_type.value}: {e}")
            raise