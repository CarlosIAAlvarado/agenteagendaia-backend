from datetime import datetime, time
from typing import Dict, Any, Optional, List
from bson import ObjectId
from ....domain.entities.professional import Professional, WeekDay, WorkingHours
from ....domain.value_objects.email import Email
from ....domain.value_objects.phone import Phone


class ProfessionalMapper:
    """Maps between Professional domain entity and MongoDB document"""
    
    @staticmethod
    def to_document(professional: Professional) -> Dict[str, Any]:
        """Convert Professional entity to MongoDB document"""
        doc = {
            "name": professional.name,
            "email": {
                "value": professional.email.value
            },
            "phone": {
                "value": professional.phone.value,
                "country_code": professional.phone.country_code
            },
            "specialization": professional.specialization,
            "working_hours": [
                {
                    "day": wh.day.value,
                    "start_time": wh.start_time.isoformat(),
                    "end_time": wh.end_time.isoformat(),
                    "is_available": wh.is_available
                }
                for wh in professional.working_hours
            ],
            "service_ids": professional.service_ids,
            "is_active": professional.is_active,
            "created_at": professional.created_at,
            "updated_at": professional.updated_at
        }
        
        if professional.id is not None:
            doc["_id"] = ObjectId(professional.id)
        
        return doc
    
    @staticmethod
    def from_document(doc: Dict[str, Any]) -> Professional:
        """Convert MongoDB document to Professional entity"""
        professional_id = str(doc["_id"]) if "_id" in doc else None
        
        # Handle email - check if it's string or object
        email_value = doc["email"]
        if isinstance(email_value, str):
            email = Email(email_value)
        else:
            email = Email(email_value["value"])
        
        # Handle phone - check if it's string or object
        phone_value = doc["phone"]
        if isinstance(phone_value, str):
            phone = Phone(value=phone_value, country_code="+57")
        else:
            phone = Phone(
                value=phone_value["value"],
                country_code=phone_value.get("country_code", "+57")
            )
        
        # Handle specialization vs specialty field name
        specialization = doc.get("specialization", doc.get("specialty", "General"))
        
        # Convert working hours from schedule if available
        working_hours = []
        schedule_data = doc.get("schedule", {})
        if schedule_data:
            day_mapping = {
                "monday": WeekDay.MONDAY,
                "tuesday": WeekDay.TUESDAY,  
                "wednesday": WeekDay.WEDNESDAY,
                "thursday": WeekDay.THURSDAY,
                "friday": WeekDay.FRIDAY,
                "saturday": WeekDay.SATURDAY,
                "sunday": WeekDay.SUNDAY
            }
            
            for day_name, schedule in schedule_data.items():
                if day_name in day_mapping:
                    working_hours.append(WorkingHours(
                        day=day_mapping[day_name],
                        start_time=time.fromisoformat(schedule["start"]),
                        end_time=time.fromisoformat(schedule["end"]),
                        is_available=True
                    ))
        else:
            # Handle new working_hours format if present
            for wh_data in doc.get("working_hours", []):
                working_hours.append(WorkingHours(
                    day=WeekDay(wh_data["day"]),
                    start_time=time.fromisoformat(wh_data["start_time"]),
                    end_time=time.fromisoformat(wh_data["end_time"]),
                    is_available=wh_data.get("is_available", True)
                ))
        
        # Handle service_ids vs available_services
        service_ids = doc.get("service_ids", doc.get("available_services", []))
        
        return Professional(
            id=professional_id,
            name=doc["name"],
            email=email,
            phone=phone,
            specialization=specialization,
            working_hours=working_hours,
            service_ids=service_ids,
            is_active=doc.get("is_active", True),
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at")
        )
    
    @staticmethod
    def to_update_document(professional: Professional) -> Dict[str, Any]:
        """Convert Professional entity to MongoDB update document"""
        update_doc = {
            "$set": {
                "name": professional.name,
                "email": {
                    "value": professional.email.value
                },
                "phone": {
                    "value": professional.phone.value,
                    "country_code": professional.phone.country_code
                },
                "specialization": professional.specialization,
                "working_hours": [
                    {
                        "day": wh.day.value,
                        "start_time": wh.start_time.isoformat(),
                        "end_time": wh.end_time.isoformat(),
                        "is_available": wh.is_available
                    }
                    for wh in professional.working_hours
                ],
                "service_ids": professional.service_ids,
                "is_active": professional.is_active,
                "updated_at": datetime.utcnow()
            }
        }
        
        return update_doc