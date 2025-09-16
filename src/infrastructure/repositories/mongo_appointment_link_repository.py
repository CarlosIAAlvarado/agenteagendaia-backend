"""
MongoDB implementation of AppointmentLinkRepository
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from ...domain.entities.appointment_link import AppointmentLink, LinkAction, LinkStatus
from ...domain.repositories.appointment_link_repository import AppointmentLinkRepository
from ..exceptions import RepositoryError, EntityNotFound

logger = logging.getLogger(__name__)


class MongoAppointmentLinkRepository(AppointmentLinkRepository):
    """MongoDB implementation of appointment link repository"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self._db = database
        self._collection: AsyncIOMotorCollection = database.appointment_links
        self._security_collection: AsyncIOMotorCollection = database.link_security_events
    
    async def create_indexes(self) -> None:
        """Create database indexes for optimal performance"""
        indexes = [
            IndexModel([("link_id", ASCENDING)], unique=True),
            IndexModel([("secure_token", ASCENDING)], unique=True),
            IndexModel([("appointment_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("action", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("used_at", DESCENDING)]),
            IndexModel([("appointment_id", ASCENDING), ("action", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("status", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING), ("status", ASCENDING)])
        ]
        
        # Security events indexes
        security_indexes = [
            IndexModel([("link_id", ASCENDING)]),
            IndexModel([("event_type", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("ip_address", ASCENDING)]),
            IndexModel([("link_id", ASCENDING), ("timestamp", DESCENDING)])
        ]
        
        try:
            await self._collection.create_indexes(indexes)
            await self._security_collection.create_indexes(security_indexes)
            logger.info("Appointment link database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating appointment link indexes: {e}")
            raise RepositoryError(f"Failed to create database indexes: {e}")
    
    async def create_link(self, link: AppointmentLink) -> AppointmentLink:
        """Create a new appointment link"""
        try:
            link_data = link.to_dict()
            result = await self._collection.insert_one(link_data)
            
            if result.inserted_id:
                logger.info(f"Created appointment link: {link.link_id}")
                return link
            else:
                raise RepositoryError("Failed to create appointment link")
                
        except DuplicateKeyError:
            raise RepositoryError("Appointment link with this ID already exists")
        except Exception as e:
            logger.error(f"Error creating appointment link: {e}")
            raise RepositoryError(f"Failed to create appointment link: {e}")
    
    async def get_link_by_id(self, link_id: str) -> Optional[AppointmentLink]:
        """Get appointment link by ID"""
        try:
            document = await self._collection.find_one({"link_id": link_id})
            
            if document:
                # Remove MongoDB's _id field
                document.pop("_id", None)
                return AppointmentLink.from_dict(document)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting appointment link by ID {link_id}: {e}")
            raise RepositoryError(f"Failed to get appointment link: {e}")
    
    async def get_link_by_token(self, secure_token: str) -> Optional[AppointmentLink]:
        """Get appointment link by secure token"""
        try:
            document = await self._collection.find_one({"secure_token": secure_token})
            
            if document:
                # Remove MongoDB's _id field
                document.pop("_id", None)
                return AppointmentLink.from_dict(document)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting appointment link by token: {e}")
            raise RepositoryError(f"Failed to get appointment link: {e}")
    
    async def get_links_by_appointment(
        self, 
        appointment_id: str,
        action: Optional[LinkAction] = None,
        status: Optional[LinkStatus] = None
    ) -> List[AppointmentLink]:
        """Get all links for a specific appointment"""
        try:
            query = {"appointment_id": appointment_id}
            
            if action:
                query["action"] = action.value
            if status:
                query["status"] = status.value
            
            cursor = self._collection.find(query).sort("created_at", DESCENDING)
            documents = await cursor.to_list(length=None)
            
            links = []
            for doc in documents:
                doc.pop("_id", None)
                links.append(AppointmentLink.from_dict(doc))
            
            return links
            
        except Exception as e:
            logger.error(f"Error getting links for appointment {appointment_id}: {e}")
            raise RepositoryError(f"Failed to get appointment links: {e}")
    
    async def get_links_by_user(
        self,
        user_id: str,
        action: Optional[LinkAction] = None,
        status: Optional[LinkStatus] = None,
        limit: int = 50
    ) -> List[AppointmentLink]:
        """Get all links for a specific user"""
        try:
            query = {"user_id": user_id}
            
            if action:
                query["action"] = action.value
            if status:
                query["status"] = status.value
            
            cursor = self._collection.find(query).sort("created_at", DESCENDING).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            links = []
            for doc in documents:
                doc.pop("_id", None)
                links.append(AppointmentLink.from_dict(doc))
            
            return links
            
        except Exception as e:
            logger.error(f"Error getting links for user {user_id}: {e}")
            raise RepositoryError(f"Failed to get user links: {e}")
    
    async def update_link(self, link: AppointmentLink) -> AppointmentLink:
        """Update an existing appointment link"""
        try:
            link_data = link.to_dict()
            link_data.pop("link_id", None)  # Don't update the ID
            
            result = await self._collection.update_one(
                {"link_id": link.link_id},
                {"$set": link_data}
            )
            
            if result.matched_count == 0:
                raise EntityNotFound(f"Appointment link {link.link_id} not found")
            
            logger.info(f"Updated appointment link: {link.link_id}")
            return link
            
        except EntityNotFound:
            raise
        except Exception as e:
            logger.error(f"Error updating appointment link {link.link_id}: {e}")
            raise RepositoryError(f"Failed to update appointment link: {e}")
    
    async def delete_link(self, link_id: str) -> bool:
        """Delete an appointment link"""
        try:
            result = await self._collection.delete_one({"link_id": link_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted appointment link: {link_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting appointment link {link_id}: {e}")
            raise RepositoryError(f"Failed to delete appointment link: {e}")
    
    async def expire_old_links(self, before_date: Optional[datetime] = None) -> int:
        """Mark expired links as expired"""
        try:
            if before_date is None:
                before_date = datetime.utcnow()
            
            result = await self._collection.update_many(
                {
                    "expires_at": {"$lt": before_date},
                    "status": {"$ne": LinkStatus.EXPIRED.value}
                },
                {"$set": {"status": LinkStatus.EXPIRED.value}}
            )
            
            logger.info(f"Marked {result.modified_count} links as expired")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Error expiring old links: {e}")
            raise RepositoryError(f"Failed to expire links: {e}")
    
    async def get_expired_links(self, limit: int = 100) -> List[AppointmentLink]:
        """Get expired links for cleanup"""
        try:
            cursor = self._collection.find(
                {"status": LinkStatus.EXPIRED.value}
            ).sort("expires_at", ASCENDING).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            links = []
            for doc in documents:
                doc.pop("_id", None)
                links.append(AppointmentLink.from_dict(doc))
            
            return links
            
        except Exception as e:
            logger.error(f"Error getting expired links: {e}")
            raise RepositoryError(f"Failed to get expired links: {e}")
    
    async def get_active_links_count(
        self,
        user_id: Optional[str] = None,
        action: Optional[LinkAction] = None
    ) -> int:
        """Get count of active links"""
        try:
            query = {"status": LinkStatus.ACTIVE.value}
            
            if user_id:
                query["user_id"] = user_id
            if action:
                query["action"] = action.value
            
            count = await self._collection.count_documents(query)
            return count
            
        except Exception as e:
            logger.error(f"Error counting active links: {e}")
            raise RepositoryError(f"Failed to count active links: {e}")
    
    async def get_link_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get analytics data for links in date range"""
        try:
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
                        "_id": {
                            "action": "$action",
                            "status": "$status"
                        },
                        "count": {"$sum": 1},
                        "total_usage": {"$sum": "$usage_count"}
                    }
                }
            ]
            
            cursor = self._collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            analytics = {
                "total_links": 0,
                "by_action": {},
                "by_status": {},
                "total_usage": 0,
                "period_start": start_date,
                "period_end": end_date
            }
            
            for result in results:
                action = result["_id"]["action"]
                status = result["_id"]["status"]
                count = result["count"]
                usage = result["total_usage"]
                
                analytics["total_links"] += count
                analytics["total_usage"] += usage
                
                if action not in analytics["by_action"]:
                    analytics["by_action"][action] = 0
                analytics["by_action"][action] += count
                
                if status not in analytics["by_status"]:
                    analytics["by_status"][status] = 0
                analytics["by_status"][status] += count
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting link analytics: {e}")
            raise RepositoryError(f"Failed to get link analytics: {e}")
    
    async def get_usage_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get link usage statistics"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get basic statistics
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
                        "_id": None,
                        "total_created": {"$sum": 1},
                        "total_used": {
                            "$sum": {
                                "$cond": [{"$gt": ["$usage_count", 0]}, 1, 0]
                            }
                        },
                        "total_expired": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "expired"]}, 1, 0]
                            }
                        },
                        "avg_usage_count": {"$avg": "$usage_count"},
                        "total_usage_events": {"$sum": "$usage_count"}
                    }
                }
            ]
            
            cursor = self._collection.aggregate(pipeline)
            results = await cursor.to_list(length=1)
            
            if results:
                stats = results[0]
                total_created = stats["total_created"]
                total_used = stats["total_used"]
                
                return {
                    "period_days": days,
                    "total_links_created": total_created,
                    "total_links_used": total_used,
                    "total_links_expired": stats["total_expired"],
                    "usage_rate": (total_used / total_created * 100) if total_created > 0 else 0,
                    "average_usage_per_link": stats["avg_usage_count"],
                    "total_usage_events": stats["total_usage_events"],
                    "period_start": start_date,
                    "period_end": end_date
                }
            
            return {
                "period_days": days,
                "total_links_created": 0,
                "total_links_used": 0,
                "total_links_expired": 0,
                "usage_rate": 0,
                "average_usage_per_link": 0,
                "total_usage_events": 0,
                "period_start": start_date,
                "period_end": end_date
            }
            
        except Exception as e:
            logger.error(f"Error getting usage statistics: {e}")
            raise RepositoryError(f"Failed to get usage statistics: {e}")
    
    async def bulk_create_links(self, links: List[AppointmentLink]) -> List[AppointmentLink]:
        """Create multiple appointment links in batch"""
        try:
            if not links:
                return []
            
            documents = [link.to_dict() for link in links]
            result = await self._collection.insert_many(documents)
            
            if result.inserted_ids:
                logger.info(f"Bulk created {len(links)} appointment links")
                return links
            else:
                raise RepositoryError("Failed to bulk create appointment links")
                
        except Exception as e:
            logger.error(f"Error bulk creating appointment links: {e}")
            raise RepositoryError(f"Failed to bulk create appointment links: {e}")
    
    async def bulk_update_status(self, link_ids: List[str], new_status: LinkStatus) -> int:
        """Update status for multiple links"""
        try:
            if not link_ids:
                return 0
            
            result = await self._collection.update_many(
                {"link_id": {"$in": link_ids}},
                {"$set": {"status": new_status.value}}
            )
            
            logger.info(f"Bulk updated {result.modified_count} links to status {new_status.value}")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Error bulk updating link status: {e}")
            raise RepositoryError(f"Failed to bulk update link status: {e}")
    
    async def search_links(
        self,
        criteria: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search links with complex criteria"""
        try:
            query = {}
            
            # Build query from criteria
            if "user_id" in criteria:
                query["user_id"] = criteria["user_id"]
            
            if "appointment_id" in criteria:
                query["appointment_id"] = criteria["appointment_id"]
            
            if "action" in criteria:
                query["action"] = criteria["action"]
            
            if "status" in criteria:
                query["status"] = criteria["status"]
            
            if "date_range" in criteria:
                date_range = criteria["date_range"]
                query["created_at"] = {
                    "$gte": date_range.get("start"),
                    "$lte": date_range.get("end")
                }
            
            # Get total count
            total_count = await self._collection.count_documents(query)
            
            # Get paginated results
            cursor = self._collection.find(query).sort("created_at", DESCENDING).skip(offset).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            links = []
            for doc in documents:
                doc.pop("_id", None)
                links.append(AppointmentLink.from_dict(doc))
            
            return {
                "links": links,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(links)) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error searching links: {e}")
            raise RepositoryError(f"Failed to search links: {e}")
    
    async def get_security_events(self, link_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get security events for a specific link"""
        try:
            cursor = self._security_collection.find(
                {"link_id": link_id}
            ).sort("timestamp", DESCENDING).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            events = []
            for doc in documents:
                doc.pop("_id", None)
                events.append(doc)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting security events for link {link_id}: {e}")
            raise RepositoryError(f"Failed to get security events: {e}")
    
    async def log_security_event(
        self,
        link_id: str,
        event_type: str,
        details: Dict[str, Any]
    ) -> bool:
        """Log a security event for a link"""
        try:
            event_data = {
                "link_id": link_id,
                "event_type": event_type,
                "timestamp": datetime.utcnow(),
                "details": details
            }
            
            result = await self._security_collection.insert_one(event_data)
            
            if result.inserted_id:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error logging security event for link {link_id}: {e}")
            return False