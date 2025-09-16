from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from ....domain.entities.patient import Patient
from ....domain.value_objects.email import Email
from ....domain.value_objects.phone import Phone


class UserMapper:
    """Maps between User domain entity and MongoDB document"""
    
    @staticmethod
    def to_document(user: Patient) -> Dict[str, Any]:
        """Convert User entity to MongoDB document"""
        doc = {
            "name": user.name,
            "email": {
                "value": user.email.value
            },
            "phone": {
                "value": user.phone.value,
                "country_code": user.phone.country_code
            },
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "preferences": user.preferences or {}  # Añadir preferences
        }
        
        if user.id is not None:
            doc["_id"] = ObjectId(user.id)
        
        return doc
    
    @staticmethod
    def from_document(doc: Dict[str, Any]) -> Patient:
        """Convert MongoDB document to User entity with robust format handling"""
        user_id = str(doc["_id"]) if "_id" in doc else None
        
        # Handle inconsistent email format
        email_data = doc["email"]
        if isinstance(email_data, dict) and "value" in email_data:
            # New format: {"value": "email@example.com"}
            email = Email(email_data["value"])
        else:
            # Legacy format: "email@example.com" 
            email = Email(str(email_data))
        
        # Handle inconsistent phone format  
        phone_data = doc["phone"]
        if isinstance(phone_data, dict) and "value" in phone_data:
            # New format: {"value": "+123456789", "country_code": "+57"}
            phone = Phone(
                value=phone_data["value"],
                country_code=phone_data.get("country_code", "+57")
            )
        else:
            # Legacy format: "+123456789"
            phone = Phone(
                value=str(phone_data),
                country_code="+57"
            )
        
        return Patient(
            id=user_id,
            name=doc["name"],
            email=email,
            phone=phone,
            is_active=doc.get("is_active", True),
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at"),
            preferences=doc.get("preferences", {})  # Añadir preferences
        )
    
    @staticmethod
    def to_update_document(user: Patient) -> Dict[str, Any]:
        """Convert User entity to MongoDB update document"""
        update_doc = {
            "$set": {
                "name": user.name,
                "email": {
                    "value": user.email.value
                },
                "phone": {
                    "value": user.phone.value,
                    "country_code": user.phone.country_code
                },
                "is_active": user.is_active,
                "updated_at": datetime.utcnow(),
                "preferences": user.preferences or {}  # Añadir preferences
            }
        }
        
        return update_doc