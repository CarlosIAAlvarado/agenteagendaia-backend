from typing import List, Optional
from datetime import datetime, date
from bson import ObjectId
from bson.errors import InvalidId
from ....domain.entities.appointment import Appointment, AppointmentStatus
from ....domain.value_objects.time_slot import TimeSlot
from ....domain.repositories.appointment_repository import IAppointmentRepository
from ..mappers.appointment_mapper import AppointmentMapper
from ..connection import get_database
import logging

logger = logging.getLogger(__name__)


class AppointmentRepositoryImpl(IAppointmentRepository):
    """MongoDB implementation of IAppointmentRepository"""
    
    def __init__(self):
        self._collection_name = "appointments"
    
    async def _get_collection(self):
        """Get appointments collection from database"""
        db = await get_database()
        return db[self._collection_name]
    
    async def create(self, appointment: Appointment) -> Appointment:
        """Create a new appointment"""
        try:
            collection = await self._get_collection()
            appointment_doc = AppointmentMapper.to_document(appointment)
            
            # Remove _id if it exists (let MongoDB generate it)
            if "_id" in appointment_doc:
                del appointment_doc["_id"]
            
            result = await collection.insert_one(appointment_doc)
            
            # Update appointment with generated ID
            appointment.id = str(result.inserted_id)
            
            logger.info(f"Created appointment with ID: {appointment.id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            raise
    
    async def get_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID"""
        try:
            collection = await self._get_collection()
            
            doc = await collection.find_one({"_id": ObjectId(appointment_id)})
            
            if doc:
                return AppointmentMapper.from_document(doc)
            return None
            
        except InvalidId:
            logger.warning(f"Invalid appointment ID format: {appointment_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting appointment by ID {appointment_id}: {e}")
            raise
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get all appointments with pagination and related data"""
        try:
            collection = await self._get_collection()

            # Aggregation pipeline to join with related collections
            pipeline = [
                # Sort by created_at descending
                {"$sort": {"created_at": -1}},

                # Skip and limit for pagination
                {"$skip": skip},
                {"$limit": limit},

                # Convert string IDs to ObjectIds and then lookup
                {
                    "$addFields": {
                        "user_object_id": {
                            "$cond": {
                                "if": {"$eq": [{"$type": "$user_id"}, "string"]},
                                "then": {"$toObjectId": "$user_id"},
                                "else": "$user_id"
                            }
                        },
                        "service_object_id": {
                            "$cond": {
                                "if": {"$eq": [{"$type": "$service_id"}, "string"]},
                                "then": {"$toObjectId": "$service_id"},
                                "else": "$service_id"
                            }
                        },
                        "professional_object_id": {
                            "$cond": {
                                "if": {
                                    "$and": [
                                        {"$ne": ["$professional_id", None]},
                                        {"$eq": [{"$type": "$professional_id"}, "string"]}
                                    ]
                                },
                                "then": {"$toObjectId": "$professional_id"},
                                "else": "$professional_id"
                            }
                        }
                    }
                },

                # Lookup user information
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "user_object_id",
                        "foreignField": "_id",
                        "as": "user_info"
                    }
                },

                # Lookup service information
                {
                    "$lookup": {
                        "from": "services",
                        "localField": "service_object_id",
                        "foreignField": "_id",
                        "as": "service_info"
                    }
                },

                # Lookup professional information
                {
                    "$lookup": {
                        "from": "professionals",
                        "localField": "professional_object_id",
                        "foreignField": "_id",
                        "as": "professional_info"
                    }
                },

                # Add fields from the lookups
                {
                    "$addFields": {
                        "user_name": {"$ifNull": [{"$arrayElemAt": ["$user_info.name", 0]}, "Usuario no encontrado"]},
                        "user_email": {"$ifNull": [{"$arrayElemAt": ["$user_info.email", 0]}, ""]},
                        "service_name": {"$ifNull": [{"$arrayElemAt": ["$service_info.name", 0]}, "Servicio no encontrado"]},
                        "service_duration": {"$ifNull": [{"$arrayElemAt": ["$service_info.duration", 0]}, 30]},
                        "service_price": {"$ifNull": [{"$arrayElemAt": ["$service_info.price", 0]}, 0]},
                        "professional_name": {"$ifNull": [{"$arrayElemAt": ["$professional_info.name", 0]}, "Por asignar"]},
                        "professional_email": {"$ifNull": [{"$arrayElemAt": ["$professional_info.email", 0]}, ""]}
                    }
                },

                # Remove the lookup arrays and auxiliary fields
                {
                    "$project": {
                        "user_info": 0,
                        "service_info": 0,
                        "professional_info": 0,
                        "user_object_id": 0,
                        "service_object_id": 0,
                        "professional_object_id": 0
                    }
                }
            ]

            cursor = collection.aggregate(pipeline)
            docs = await cursor.to_list(length=None)

            logger.info(f"Aggregation returned {len(docs)} documents")
            if docs:
                logger.info(f"First document keys: {list(docs[0].keys())}")
                logger.info(f"First document user_name: {docs[0].get('user_name', 'NOT_FOUND')}")

            # Process documents with additional fields
            appointments = []
            for doc in docs:
                appointment = AppointmentMapper.from_document(doc)
                # Add the resolved fields
                appointment.user_name = doc.get('user_name', 'Usuario no encontrado')
                appointment.user_email = doc.get('user_email', '')
                appointment.service_name = doc.get('service_name', 'Servicio no encontrado')
                appointment.professional_name = doc.get('professional_name', 'Por asignar')
                appointments.append(appointment)

            logger.info(f"Successfully processed {len(appointments)} appointments with joins")
            return appointments

        except Exception as e:
            logger.error(f"Error getting all appointments with joins: {e}")
            logger.error(f"Aggregation pipeline failed, falling back to simple query")
            # Fallback to simple query without joins
            try:
                cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
                docs = await cursor.to_list(length=limit)
                return [AppointmentMapper.from_document(doc) for doc in docs]
            except:
                raise
    
    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments by user ID"""
        try:
            collection = await self._get_collection()
            
            # Sort by appointment_date first, then created_at as fallback
            cursor = collection.find({"user_id": user_id}).skip(skip).limit(limit).sort([
                ("appointment_date", -1),
                ("created_at", -1)
            ])
            docs = await cursor.to_list(length=limit)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting appointments by user ID {user_id}: {e}")
            raise
    
    async def get_by_professional_id(self, professional_id: str, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments by professional ID"""
        try:
            collection = await self._get_collection()
            
            # Sort by appointment_date first, then created_at as fallback
            cursor = collection.find({"professional_id": professional_id}).skip(skip).limit(limit).sort([
                ("appointment_date", 1),
                ("created_at", 1)
            ])
            docs = await cursor.to_list(length=limit)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting appointments by professional ID {professional_id}: {e}")
            raise
    
    async def get_by_service_id(self, service_id: str, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments by service ID"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({"service_id": service_id}).skip(skip).limit(limit).sort([("appointment_date", -1), ("created_at", -1)])
            docs = await cursor.to_list(length=limit)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting appointments by service ID {service_id}: {e}")
            raise
    
    async def get_by_status(self, status: AppointmentStatus, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments by status"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({"status": status.value}).skip(skip).limit(limit).sort([("appointment_date", 1), ("created_at", 1)])
            docs = await cursor.to_list(length=limit)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting appointments by status {status.value}: {e}")
            raise
    
    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Appointment]:
        """Get appointments within date range"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "appointment_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort([("appointment_date", 1), ("created_at", 1)])
            
            docs = await cursor.to_list(length=None)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting appointments by date range {start_date} - {end_date}: {e}")
            raise
    
    async def get_by_date(self, appointment_date: date) -> List[Appointment]:
        """Get appointments for a specific date"""
        try:
            start_datetime = datetime.combine(appointment_date, datetime.min.time())
            end_datetime = datetime.combine(appointment_date, datetime.max.time())
            
            return await self.get_by_date_range(start_datetime, end_datetime)
            
        except Exception as e:
            logger.error(f"Error getting appointments by date {appointment_date}: {e}")
            raise
    
    async def get_professional_appointments_by_date(self, professional_id: str, appointment_date: date) -> List[Appointment]:
        """Get professional's appointments for a specific date"""
        try:
            collection = await self._get_collection()
            
            start_datetime = datetime.combine(appointment_date, datetime.min.time())
            end_datetime = datetime.combine(appointment_date, datetime.max.time())
            
            cursor = collection.find({
                "professional_id": professional_id,
                "appointment_date": {
                    "$gte": start_datetime,
                    "$lte": end_datetime
                }
            }).sort([("appointment_date", 1), ("created_at", 1)])
            
            docs = await cursor.to_list(length=None)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting professional appointments by date {professional_id} - {appointment_date}: {e}")
            raise
    
    async def get_user_upcoming_appointments(self, user_id: str) -> List[Appointment]:
        """Get user's upcoming appointments"""
        try:
            collection = await self._get_collection()
            
            now = datetime.utcnow()
            
            cursor = collection.find({
                "user_id": user_id,
                "appointment_date": {"$gte": now},
                "status": {"$nin": [AppointmentStatus.CANCELLED.value, AppointmentStatus.COMPLETED.value]}
            }).sort([("appointment_date", 1), ("created_at", 1)])
            
            docs = await cursor.to_list(length=None)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting user upcoming appointments {user_id}: {e}")
            raise
    
    async def get_professional_upcoming_appointments(self, professional_id: str) -> List[Appointment]:
        """Get professional's upcoming appointments"""
        try:
            collection = await self._get_collection()
            
            now = datetime.utcnow()
            
            cursor = collection.find({
                "professional_id": professional_id,
                "appointment_date": {"$gte": now},
                "status": {"$nin": [AppointmentStatus.CANCELLED.value]}
            }).sort([("appointment_date", 1), ("created_at", 1)])
            
            docs = await cursor.to_list(length=None)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting professional upcoming appointments {professional_id}: {e}")
            raise
    
    async def get_overlapping_appointments(self, professional_id: str, time_slot: TimeSlot) -> List[Appointment]:
        """Get appointments that overlap with given time slot for a professional"""
        try:
            collection = await self._get_collection()
            
            # For appointment_date-based overlap checking, we need to calculate end time
            appointment_end_time = time_slot.end_time
            
            cursor = collection.find({
                "professional_id": professional_id,
                "status": {"$nin": [AppointmentStatus.CANCELLED.value]},
                "appointment_date": {
                    "$gte": time_slot.start_time,
                    "$lt": appointment_end_time
                }
            }).sort([("appointment_date", 1), ("created_at", 1)])
            
            docs = await cursor.to_list(length=None)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting overlapping appointments: {e}")
            raise
    
    async def get_appointments_needing_confirmation(self) -> List[Appointment]:
        """Get appointments that need confirmation"""
        try:
            collection = await self._get_collection()
            
            cursor = collection.find({
                "status": AppointmentStatus.SCHEDULED.value
            }).sort([("appointment_date", 1), ("created_at", 1)])
            
            docs = await cursor.to_list(length=None)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting appointments needing confirmation: {e}")
            raise
    
    async def get_past_due_appointments(self) -> List[Appointment]:
        """Get appointments that are past their scheduled time"""
        try:
            collection = await self._get_collection()
            
            now = datetime.utcnow()
            
            cursor = collection.find({
                "appointment_date": {"$lt": now},
                "status": {"$nin": [
                    AppointmentStatus.COMPLETED.value,
                    AppointmentStatus.CANCELLED.value,
                    AppointmentStatus.NO_SHOW.value
                ]}
            }).sort([("appointment_date", 1), ("created_at", 1)])
            
            docs = await cursor.to_list(length=None)
            
            return [AppointmentMapper.from_document(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting past due appointments: {e}")
            raise
    
    async def update(self, appointment: Appointment) -> Appointment:
        """Update existing appointment"""
        try:
            if not appointment.id:
                raise ValueError("Appointment ID is required for update")
            
            collection = await self._get_collection()
            update_doc = AppointmentMapper.to_update_document(appointment)
            
            result = await collection.update_one(
                {"_id": ObjectId(appointment.id)},
                update_doc
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Appointment with ID {appointment.id} not found")
            
            logger.info(f"Updated appointment with ID: {appointment.id}")
            return appointment
            
        except InvalidId:
            raise ValueError(f"Invalid appointment ID format: {appointment.id}")
        except Exception as e:
            logger.error(f"Error updating appointment {appointment.id}: {e}")
            raise
    
    async def delete(self, appointment_id: str) -> bool:
        """Delete appointment by ID"""
        try:
            collection = await self._get_collection()
            
            result = await collection.delete_one({"_id": ObjectId(appointment_id)})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted appointment with ID: {appointment_id}")
            else:
                logger.warning(f"Appointment with ID {appointment_id} not found for deletion")
            
            return success
            
        except InvalidId:
            logger.warning(f"Invalid appointment ID format: {appointment_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting appointment {appointment_id}: {e}")
            raise
    
    async def exists_conflict(self, professional_id: str, time_slot: TimeSlot, exclude_appointment_id: Optional[str] = None) -> bool:
        """Check if there's a scheduling conflict for professional"""
        try:
            collection = await self._get_collection()
            
            # For appointment_date-based conflict checking
            query = {
                "professional_id": professional_id,
                "status": {"$nin": [AppointmentStatus.CANCELLED.value]},
                "appointment_date": {
                    "$gte": time_slot.start_time,
                    "$lt": time_slot.end_time
                }
            }
            
            if exclude_appointment_id:
                query["_id"] = {"$ne": ObjectId(exclude_appointment_id)}
            
            count = await collection.count_documents(query)
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking conflict: {e}")
            raise
    
    async def count_total(self) -> int:
        """Count total appointments"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({})
            
        except Exception as e:
            logger.error(f"Error counting total appointments: {e}")
            raise
    
    async def count_by_status(self, status: AppointmentStatus) -> int:
        """Count appointments by status"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"status": status.value})
            
        except Exception as e:
            logger.error(f"Error counting appointments by status {status.value}: {e}")
            raise
    
    async def count_by_user(self, user_id: str) -> int:
        """Count appointments by user"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"user_id": user_id})
            
        except Exception as e:
            logger.error(f"Error counting appointments by user {user_id}: {e}")
            raise
    
    async def count_by_professional(self, professional_id: str) -> int:
        """Count appointments by professional"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"professional_id": professional_id})
            
        except Exception as e:
            logger.error(f"Error counting appointments by professional {professional_id}: {e}")
            raise
    
    async def count_by_date_range(self, start_date: datetime, end_date: datetime) -> int:
        """Count appointments within date range"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({
                "appointment_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
            
        except Exception as e:
            logger.error(f"Error counting appointments by date range {start_date} - {end_date}: {e}")
            raise
    
    async def count_by_professional_and_date(self, professional_id: str, target_date: date) -> int:
        """Count appointments for a professional on a specific date (excluding cancelled)"""
        try:
            collection = await self._get_collection()
            
            # Convert date to datetime range (start and end of day)
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            return await collection.count_documents({
                "professional_id": professional_id,
                "appointment_date": {
                    "$gte": start_datetime,
                    "$lte": end_datetime
                },
                "status": {"$ne": AppointmentStatus.CANCELLED.value}  # Exclude cancelled appointments
            })
            
        except Exception as e:
            logger.error(f"Error counting appointments by professional {professional_id} on date {target_date}: {e}")
            raise
    
    async def count_by_service(self, service_id: str) -> int:
        """Count appointments by service"""
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"service_id": service_id})
        except Exception as e:
            logger.error(f"Error counting appointments by service {service_id}: {e}")
            raise
    
    async def get_by_date_range_paginated(self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments within date range with pagination"""
        try:
            collection = await self._get_collection()
            cursor = collection.find({
                "appointment_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).skip(skip).limit(limit).sort("appointment_date", 1)
            
            documents = await cursor.to_list(length=limit)
            return [self._document_to_appointment(doc) for doc in documents]
        except Exception as e:
            logger.error(f"Error getting appointments by date range paginated {start_date} - {end_date}: {e}")
            raise

    async def get_by_professional_and_date_range(self, professional_id: str, start_date: date, end_date: date) -> List[Appointment]:
        """Get appointments for a professional within a date range"""
        try:
            collection = await self._get_collection()

            # Convert dates to datetime range
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            cursor = collection.find({
                "professional_id": professional_id,
                "appointment_date": {
                    "$gte": start_datetime,
                    "$lte": end_datetime
                }
            }).sort("appointment_date", 1)

            documents = await cursor.to_list(length=None)
            return [self._document_to_appointment(doc) for doc in documents]

        except Exception as e:
            logger.error(f"Error getting appointments by professional {professional_id} and date range {start_date} - {end_date}: {e}")
            raise