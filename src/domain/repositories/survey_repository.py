from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..entities.survey import Survey, SurveyResponse, SurveyStatus, SurveyType


class ISurveyRepository(ABC):
    """Interface for Survey repository following Repository pattern"""
    
    @abstractmethod
    async def create_survey(self, survey: Survey) -> Survey:
        """Create a new survey"""
        pass
    
    @abstractmethod
    async def get_survey_by_id(self, survey_id: str) -> Optional[Survey]:
        """Get survey by ID"""
        pass
    
    @abstractmethod
    async def get_survey_by_token(self, completion_token: str) -> Optional[Survey]:
        """Get survey by completion token"""
        pass
    
    @abstractmethod
    async def update_survey(self, survey: Survey) -> Survey:
        """Update existing survey"""
        pass
    
    @abstractmethod
    async def delete_survey(self, survey_id: str) -> bool:
        """Delete survey"""
        pass
    
    @abstractmethod
    async def add_response(self, response: SurveyResponse) -> SurveyResponse:
        """Add response to survey"""
        pass
    
    @abstractmethod
    async def get_survey_responses(self, survey_id: str) -> List[SurveyResponse]:
        """Get all responses for a survey"""
        pass
    
    @abstractmethod
    async def get_surveys_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Survey]:
        """Get surveys for a user"""
        pass
    
    @abstractmethod
    async def get_surveys_by_appointment(self, appointment_id: str) -> List[Survey]:
        """Get surveys for an appointment"""
        pass
    
    @abstractmethod
    async def get_surveys_by_status(self, status: SurveyStatus, skip: int = 0, limit: int = 50) -> List[Survey]:
        """Get surveys by status"""
        pass
    
    @abstractmethod
    async def get_surveys_by_type(self, survey_type: SurveyType, skip: int = 0, limit: int = 50) -> List[Survey]:
        """Get surveys by type"""
        pass
    
    @abstractmethod
    async def get_expired_surveys(self) -> List[Survey]:
        """Get surveys that have expired"""
        pass
    
    @abstractmethod
    async def get_satisfaction_analytics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get satisfaction analytics for date range"""
        pass
    
    @abstractmethod
    async def count_surveys_by_status(self, status: SurveyStatus) -> int:
        """Count surveys by status"""
        pass
    
    @abstractmethod
    async def get_average_satisfaction_score(
        self, 
        start_date: datetime, 
        end_date: datetime,
        service_id: Optional[str] = None,
        professional_id: Optional[str] = None
    ) -> Optional[float]:
        """Get average satisfaction score for period"""
        pass
    
    @abstractmethod
    async def get_nps_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get Net Promoter Score analytics"""
        pass