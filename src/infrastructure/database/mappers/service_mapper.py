from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
import uuid
from ....domain.entities.service import Service, ServiceType, ServiceMode


class ServiceMapper:
    """Maps between Service domain entity and MongoDB document"""
    
    @staticmethod
    def to_document(service: Service) -> Dict[str, Any]:
        """Convert Service entity to MongoDB document"""
        doc = {
            "service_id": str(uuid.uuid4()),  # Generar service_id único
            "name": service.name,
            "description": service.description,
            "duration_minutes": service.duration_minutes,
            "service_type": service.service_type.value,
            "service_mode": service.service_mode.value,
            "price": service.price,
            "is_active": service.is_active,
            "created_at": service.created_at,
            "updated_at": service.updated_at
        }
        
        if service.id is not None:
            doc["_id"] = ObjectId(service.id)
        
        return doc
    
    @staticmethod
    def from_document(doc: Dict[str, Any]) -> Service:
        """Convert MongoDB document to Service entity"""
        service_id = str(doc["_id"]) if "_id" in doc else None
        
        return Service(
            id=service_id,
            name=doc["name"],
            description=doc["description"],
            duration_minutes=doc["duration_minutes"],
            service_type=ServiceType(doc["service_type"]),
            service_mode=ServiceMode(doc["service_mode"]),
            price=doc.get("price"),
            is_active=doc.get("is_active", True),
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at")
        )
    
    @staticmethod
    def to_update_document(service: Service) -> Dict[str, Any]:
        """Convert Service entity to MongoDB update document"""
        update_doc = {
            "$set": {
                "name": service.name,
                "description": service.description,
                "duration_minutes": service.duration_minutes,
                "service_type": service.service_type.value,
                "service_mode": service.service_mode.value,
                "price": service.price,
                "is_active": service.is_active,
                "updated_at": datetime.utcnow()
            }
        }
        
        return update_doc