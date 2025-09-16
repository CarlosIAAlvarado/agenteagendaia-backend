from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from ....domain.entities.survey import Survey, SurveyResponse, SurveyStatus, SurveyType
from ....domain.repositories.survey_repository import ISurveyRepository
from ..mappers.survey_mapper import SurveyMapper
import logging

logger = logging.getLogger(__name__)


class SurveyRepository(ISurveyRepository):
    """MongoDB implementation of Survey repository"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.surveys
        self.responses_collection = database.survey_responses
    
    async def create_survey(self, survey: Survey) -> Survey:
        """Create a new survey"""
        try:
            survey_doc = SurveyMapper.to_document(survey)
            result = await self.collection.insert_one(survey_doc)
            survey.id = str(result.inserted_id)
            
            logger.info(f"Created survey: {survey.id}")
            return survey
            
        except Exception as e:
            logger.error(f"Error creating survey: {e}")
            raise
    
    async def get_survey_by_id(self, survey_id: str) -> Optional[Survey]:
        """Get survey by ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(survey_id)})
            if not doc:
                return None
            
            survey = SurveyMapper.from_document(doc)
            
            # Load responses
            responses = await self.get_survey_responses(survey_id)
            survey.responses = responses
            
            return survey
            
        except Exception as e:
            logger.error(f"Error getting survey {survey_id}: {e}")
            return None
    
    async def get_survey_by_token(self, completion_token: str) -> Optional[Survey]:
        """Get survey by completion token"""
        try:
            doc = await self.collection.find_one({"completion_token": completion_token})
            if not doc:
                return None
            
            survey = SurveyMapper.from_document(doc)
            
            # Load responses
            responses = await self.get_survey_responses(survey.id)
            survey.responses = responses
            
            return survey
            
        except Exception as e:
            logger.error(f"Error getting survey by token: {e}")
            return None
    
    async def update_survey(self, survey: Survey) -> Survey:
        """Update existing survey"""
        try:
            update_doc = SurveyMapper.to_update_document(survey)
            
            await self.collection.update_one(
                {"_id": ObjectId(survey.id)},
                update_doc
            )
            
            logger.info(f"Updated survey: {survey.id}")
            return survey
            
        except Exception as e:
            logger.error(f"Error updating survey {survey.id}: {e}")
            raise
    
    async def delete_survey(self, survey_id: str) -> bool:
        """Delete survey and its responses"""
        try:
            # Delete survey responses first
            await self.responses_collection.delete_many({"survey_id": survey_id})
            
            # Delete survey
            result = await self.collection.delete_one({"_id": ObjectId(survey_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted survey: {survey_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting survey {survey_id}: {e}")
            return False
    
    async def add_response(self, response: SurveyResponse) -> SurveyResponse:
        """Add response to survey"""
        try:
            response_doc = SurveyMapper.response_to_document(response)
            result = await self.responses_collection.insert_one(response_doc)
            response.id = str(result.inserted_id)
            
            logger.info(f"Added response to survey {response.survey_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error adding survey response: {e}")
            raise
    
    async def get_survey_responses(self, survey_id: str) -> List[SurveyResponse]:
        """Get all responses for a survey"""
        try:
            cursor = self.responses_collection.find({"survey_id": survey_id})
            responses = []
            
            async for doc in cursor:
                response = SurveyMapper.response_from_document(doc)
                responses.append(response)
            
            return responses
            
        except Exception as e:
            logger.error(f"Error getting survey responses for {survey_id}: {e}")
            return []
    
    async def get_surveys_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Survey]:
        """Get surveys for a user"""
        try:
            cursor = self.collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).skip(skip).limit(limit)
            
            surveys = []
            async for doc in cursor:
                survey = SurveyMapper.from_document(doc)
                surveys.append(survey)
            
            return surveys
            
        except Exception as e:
            logger.error(f"Error getting surveys for user {user_id}: {e}")
            return []
    
    async def get_surveys_by_appointment(self, appointment_id: str) -> List[Survey]:
        """Get surveys for an appointment"""
        try:
            cursor = self.collection.find({"appointment_id": appointment_id})
            surveys = []
            
            async for doc in cursor:
                survey = SurveyMapper.from_document(doc)
                surveys.append(survey)
            
            return surveys
            
        except Exception as e:
            logger.error(f"Error getting surveys for appointment {appointment_id}: {e}")
            return []
    
    async def get_surveys_by_status(self, status: SurveyStatus, skip: int = 0, limit: int = 50) -> List[Survey]:
        """Get surveys by status"""
        try:
            cursor = self.collection.find(
                {"status": status.value}
            ).sort("created_at", -1).skip(skip).limit(limit)
            
            surveys = []
            async for doc in cursor:
                survey = SurveyMapper.from_document(doc)
                surveys.append(survey)
            
            return surveys
            
        except Exception as e:
            logger.error(f"Error getting surveys by status {status.value}: {e}")
            return []
    
    async def get_surveys_by_type(self, survey_type: SurveyType, skip: int = 0, limit: int = 50) -> List[Survey]:
        """Get surveys by type"""
        try:
            cursor = self.collection.find(
                {"survey_type": survey_type.value}
            ).sort("created_at", -1).skip(skip).limit(limit)
            
            surveys = []
            async for doc in cursor:
                survey = SurveyMapper.from_document(doc)
                surveys.append(survey)
            
            return surveys
            
        except Exception as e:
            logger.error(f"Error getting surveys by type {survey_type.value}: {e}")
            return []
    
    async def get_expired_surveys(self) -> List[Survey]:
        """Get surveys that have expired"""
        try:
            now = datetime.utcnow()
            cursor = self.collection.find({
                "expires_at": {"$lt": now},
                "status": {"$ne": SurveyStatus.EXPIRED.value}
            })
            
            surveys = []
            async for doc in cursor:
                survey = SurveyMapper.from_document(doc)
                surveys.append(survey)
            
            return surveys
            
        except Exception as e:
            logger.error(f"Error getting expired surveys: {e}")
            return []
    
    async def get_satisfaction_analytics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get satisfaction analytics for date range"""
        try:
            pipeline = [
                {
                    "$match": {
                        "status": SurveyStatus.COMPLETED.value,
                        "completed_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_surveys": {"$sum": 1},
                        "avg_satisfaction": {"$avg": "$satisfaction_score"},
                        "total_responses": {"$sum": {"$size": "$responses"}}
                    }
                }
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=1)
            
            if result:
                analytics = result[0]
                return {
                    "total_surveys": analytics.get("total_surveys", 0),
                    "average_satisfaction": round(analytics.get("avg_satisfaction", 0), 2),
                    "total_responses": analytics.get("total_responses", 0),
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                }
            
            return {
                "total_surveys": 0,
                "average_satisfaction": 0,
                "total_responses": 0,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting satisfaction analytics: {e}")
            return {"error": str(e)}
    
    async def count_surveys_by_status(self, status: SurveyStatus) -> int:
        """Count surveys by status"""
        try:
            count = await self.collection.count_documents({"status": status.value})
            return count
            
        except Exception as e:
            logger.error(f"Error counting surveys by status {status.value}: {e}")
            return 0
    
    async def get_average_satisfaction_score(
        self, 
        start_date: datetime, 
        end_date: datetime,
        service_id: Optional[str] = None,
        professional_id: Optional[str] = None
    ) -> Optional[float]:
        """Get average satisfaction score for period"""
        try:
            match_filter = {
                "status": SurveyStatus.COMPLETED.value,
                "completed_at": {"$gte": start_date, "$lte": end_date}
            }
            
            if service_id:
                match_filter["service_id"] = service_id
            if professional_id:
                match_filter["professional_id"] = professional_id
            
            pipeline = [
                {"$match": match_filter},
                {
                    "$group": {
                        "_id": None,
                        "avg_satisfaction": {"$avg": "$satisfaction_score"}
                    }
                }
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=1)
            
            if result and result[0]["avg_satisfaction"] is not None:
                return round(result[0]["avg_satisfaction"], 2)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting average satisfaction score: {e}")
            return None
    
    async def get_nps_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get Net Promoter Score analytics"""
        try:
            pipeline = [
                {
                    "$match": {
                        "status": SurveyStatus.COMPLETED.value,
                        "completed_at": {"$gte": start_date, "$lte": end_date},
                        "nps_score": {"$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_surveys": {"$sum": 1},
                        "avg_nps": {"$avg": "$nps_score"},
                        "promoters": {
                            "$sum": {"$cond": [{"$gte": ["$nps_score", 50]}, 1, 0]}
                        },
                        "passives": {
                            "$sum": {"$cond": [
                                {"$and": [{"$gte": ["$nps_score", 0]}, {"$lt": ["$nps_score", 50]}]},
                                1, 0
                            ]}
                        },
                        "detractors": {
                            "$sum": {"$cond": [{"$lt": ["$nps_score", 0]}, 1, 0]}
                        }
                    }
                }
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=1)
            
            if result:
                analytics = result[0]
                total = analytics.get("total_surveys", 0)
                
                return {
                    "total_surveys": total,
                    "average_nps": round(analytics.get("avg_nps", 0), 1),
                    "promoters": analytics.get("promoters", 0),
                    "passives": analytics.get("passives", 0),
                    "detractors": analytics.get("detractors", 0),
                    "promoter_percentage": round(analytics.get("promoters", 0) / total * 100, 1) if total > 0 else 0,
                    "detractor_percentage": round(analytics.get("detractors", 0) / total * 100, 1) if total > 0 else 0
                }
            
            return {
                "total_surveys": 0,
                "average_nps": 0,
                "promoters": 0,
                "passives": 0,
                "detractors": 0,
                "promoter_percentage": 0,
                "detractor_percentage": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting NPS analytics: {e}")
            return {"error": str(e)}