from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from ....domain.entities.appointment import Appointment, AppointmentStatus


class AppointmentMapper:
    """Maps between Appointment domain entity and MongoDB document"""
    
    @staticmethod
    def to_document(appointment: Appointment) -> Dict[str, Any]:
        """Convert Appointment entity to MongoDB document - ONLY ESSENTIAL FIELDS"""
        doc = {
            "user_id": appointment.user_id,
            "service_id": appointment.service_id,
            "professional_id": appointment.professional_id,
            "appointment_date": appointment.appointment_date,
            "status": appointment.status.value,
            "notes": appointment.notes,
            "created_at": appointment.created_at,
            "updated_at": appointment.updated_at,
            "duration_minutes": appointment.duration_minutes,
            "price": appointment.price
        }
        
        # Only include _id if it exists
        if appointment.id is not None:
            doc["_id"] = ObjectId(appointment.id)
        
        return doc
    
    @staticmethod
    def from_document(doc: Dict[str, Any]) -> Appointment:
        """Convert MongoDB document to Appointment entity - ONLY ESSENTIAL FIELDS"""
        appointment_id = str(doc["_id"]) if "_id" in doc else None
        
        return Appointment(
            user_id=doc["user_id"],
            service_id=doc["service_id"],
            id=appointment_id,
            professional_id=doc.get("professional_id"),
            status=AppointmentStatus(doc["status"]),
            appointment_date=doc.get("appointment_date"),
            notes=doc.get("notes"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
            duration_minutes=doc.get("duration_minutes"),
            price=doc.get("price")
        )
    
    @staticmethod
    def to_update_document(appointment: Appointment) -> Dict[str, Any]:
        """Convert Appointment entity to MongoDB update document - ONLY ESSENTIAL FIELDS"""
        set_fields = {
            "user_id": appointment.user_id,
            "service_id": appointment.service_id,
            "professional_id": appointment.professional_id,
            "appointment_date": appointment.appointment_date,
            "status": appointment.status.value,
            "notes": appointment.notes,
            "updated_at": appointment.updated_at,
            "duration_minutes": appointment.duration_minutes,
            "price": appointment.price
        }
        
        update_doc = {"$set": set_fields}
        return update_doc