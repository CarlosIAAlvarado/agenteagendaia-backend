from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class MetricsRepository:
    """Repository for storing and retrieving metrics data"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.metrics
        self.conversation_collection = database.conversations
        self.appointment_collection = database.appointments
        self.user_collection = database.users
        self.message_collection = database.messages
    
    async def store_metric(self, metric_name: str, value: Any, timestamp: datetime = None) -> bool:
        """Store a metric value"""
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            metric_doc = {
                "metric_name": metric_name,
                "value": value,
                "timestamp": timestamp,
                "date": timestamp.date(),
                "hour": timestamp.hour
            }
            
            await self.collection.insert_one(metric_doc)
            return True
            
        except Exception as e:
            logger.error(f"Error storing metric {metric_name}: {e}")
            return False
    
    async def get_metric_history(
        self, 
        metric_name: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric"""
        try:
            cursor = self.collection.find({
                "metric_name": metric_name,
                "timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("timestamp", 1)
            
            return await cursor.to_list(length=None)
            
        except Exception as e:
            logger.error(f"Error getting metric history for {metric_name}: {e}")
            return []
    
    async def calculate_avg_response_time(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Calculate average bot response time from conversation data"""
        try:
            # This would aggregate message timestamps to calculate response times
            # For now, return mock calculation
            pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_response_time": {"$avg": "$response_time_ms"}
                    }
                }
            ]
            
            result = await self.message_collection.aggregate(pipeline).to_list(length=1)
            
            if result:
                return result[0].get("avg_response_time", 850.0)
            
            return 850.0  # Default mock value
            
        except Exception as e:
            logger.error(f"Error calculating avg response time: {e}")
            return 850.0
    
    async def count_appointments_by_status(
        self, 
        status: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> int:
        """Count appointments by status in date range"""
        try:
            count = await self.appointment_collection.count_documents({
                "status": status,
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting appointments by status {status}: {e}")
            return 0
    
    async def count_conversations_by_status(
        self, 
        status: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> int:
        """Count conversations by status in date range"""
        try:
            count = await self.conversation_collection.count_documents({
                "status": status,
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting conversations by status {status}: {e}")
            return 0
    
    async def count_new_users(self, start_date: datetime, end_date: datetime) -> int:
        """Count new users registered in date range"""
        try:
            count = await self.user_collection.count_documents({
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting new users: {e}")
            return 0
    
    async def get_conversion_funnel(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, int]:
        """Get conversion funnel data"""
        try:
            # This would analyze conversation flow to determine conversion steps
            pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$current_step",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            result = await self.conversation_collection.aggregate(pipeline).to_list(length=None)
            
            funnel = {
                "started": 0,
                "service_selected": 0,
                "date_selected": 0,
                "confirmed": 0
            }
            
            for item in result:
                step = item["_id"]
                count = item["count"]
                
                if step in ["greeting", "service_selection"]:
                    funnel["started"] += count
                if step in ["date_time_selection", "professional_selection"]:
                    funnel["service_selected"] += count
                if step in ["appointment_scheduling", "confirmation"]:
                    funnel["date_selected"] += count
                if step == "confirmation":
                    funnel["confirmed"] += count
            
            return funnel
            
        except Exception as e:
            logger.error(f"Error getting conversion funnel: {e}")
            return {"started": 0, "service_selected": 0, "date_selected": 0, "confirmed": 0}
    
    async def get_satisfaction_ratings(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, int]:
        """Get customer satisfaction ratings distribution"""
        try:
            # This would query satisfaction survey responses
            # For now, return mock data
            return {
                "5_stars": 89,
                "4_stars": 42,
                "3_stars": 18,
                "2_stars": 5,
                "1_stars": 2,
                "total_responses": 156
            }
            
        except Exception as e:
            logger.error(f"Error getting satisfaction ratings: {e}")
            return {"total_responses": 0}
    
    async def get_daily_metrics_summary(self, date: datetime) -> Dict[str, Any]:
        """Get summary of metrics for a specific day"""
        try:
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            summary = {
                "date": date.date().isoformat(),
                "appointments_scheduled": await self.count_appointments_by_status("scheduled", day_start, day_end),
                "appointments_completed": await self.count_appointments_by_status("completed", day_start, day_end),
                "appointments_cancelled": await self.count_appointments_by_status("cancelled", day_start, day_end),
                "conversations_started": await self.count_conversations_by_status("active", day_start, day_end),
                "conversations_completed": await self.count_conversations_by_status("completed", day_start, day_end),
                "new_users": await self.count_new_users(day_start, day_end)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting daily metrics summary: {e}")
            return {}
    
    async def store_response_time_metric(self, conversation_id: str, response_time_ms: int):
        """Store response time metric for a conversation"""
        try:
            await self.store_metric(
                "bot_response_time",
                {
                    "conversation_id": conversation_id,
                    "response_time_ms": response_time_ms
                }
            )
            
        except Exception as e:
            logger.error(f"Error storing response time metric: {e}")
    
    async def get_metrics_trends(
        self, 
        metric_name: str, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get trend data for a metric over specified number of days"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "metric_name": metric_name,
                        "timestamp": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"}
                        },
                        "avg_value": {"$avg": "$value"},
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=None)
            return result
            
        except Exception as e:
            logger.error(f"Error getting metrics trends: {e}")
            return []