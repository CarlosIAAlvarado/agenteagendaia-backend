from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator
from enum import Enum


class QuestionTypeDTO(str, Enum):
    """Question type enumeration for DTOs"""
    RATING = "rating"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    YES_NO = "yes_no"
    NPS = "nps"


class SurveyTypeDTO(str, Enum):
    """Survey type enumeration for DTOs"""
    POST_APPOINTMENT = "post_appointment"
    SERVICE_FEEDBACK = "service_feedback"
    GENERAL_SATISFACTION = "general_satisfaction"


class SurveyStatusDTO(str, Enum):
    """Survey status enumeration for DTOs"""
    PENDING = "pending"
    SENT = "sent"
    COMPLETED = "completed"
    EXPIRED = "expired"


class SurveyQuestionCreateDTO(BaseModel):
    """DTO for creating survey questions"""
    question_text: str
    question_type: QuestionTypeDTO
    is_required: bool = True
    options: Optional[List[str]] = None
    order: int = 0
    
    @validator('question_text')
    def validate_question_text(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Question text must be at least 5 characters long')
        return v.strip()
    
    @validator('options')
    def validate_options(cls, v, values):
        if values.get('question_type') == QuestionTypeDTO.MULTIPLE_CHOICE:
            if not v or len(v) < 2:
                raise ValueError('Multiple choice questions must have at least 2 options')
        return v


class SurveyQuestionResponseDTO(BaseModel):
    """DTO for survey question in responses"""
    id: str
    question_text: str
    question_type: QuestionTypeDTO
    is_required: bool
    options: Optional[List[str]] = None
    order: int
    
    class Config:
        from_attributes = True


class SurveyCreateDTO(BaseModel):
    """DTO for creating surveys"""
    title: str
    description: str
    survey_type: SurveyTypeDTO
    questions: List[SurveyQuestionCreateDTO]
    appointment_id: Optional[str] = None
    user_id: Optional[str] = None
    service_id: Optional[str] = None
    professional_id: Optional[str] = None
    expires_in_days: int = 7
    
    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Survey title must be at least 3 characters long')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Survey description must be at least 10 characters long')
        return v.strip()
    
    @validator('questions')
    def validate_questions(cls, v):
        if not v or len(v) < 1:
            raise ValueError('Survey must have at least 1 question')
        if len(v) > 20:
            raise ValueError('Survey cannot have more than 20 questions')
        return v
    
    @validator('expires_in_days')
    def validate_expires_in_days(cls, v):
        if v < 1 or v > 365:
            raise ValueError('Survey expiration must be between 1 and 365 days')
        return v


class SurveyResponseSubmissionDTO(BaseModel):
    """DTO for submitting survey responses"""
    question_id: str
    response_value: Any
    response_text: Optional[str] = None
    
    @validator('response_value')
    def validate_response_value(cls, v):
        if v is None:
            raise ValueError('Response value is required')
        return v


class SurveySubmissionDTO(BaseModel):
    """DTO for submitting complete survey"""
    survey_id: Optional[str] = None
    completion_token: Optional[str] = None
    responses: List[SurveyResponseSubmissionDTO]
    
    @validator('responses')
    def validate_responses(cls, v):
        if not v or len(v) < 1:
            raise ValueError('At least one response is required')
        return v
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.survey_id and not self.completion_token:
            raise ValueError('Either survey_id or completion_token must be provided')


class SurveyResponseDTO(BaseModel):
    """DTO for survey responses"""
    id: str
    survey_id: str
    question_id: str
    response_value: Any
    response_text: Optional[str] = None
    submitted_at: str
    
    class Config:
        from_attributes = True


class SurveyResponseDTO(BaseModel):
    """DTO for survey entity responses"""
    id: str
    title: str
    description: str
    survey_type: SurveyTypeDTO
    status: SurveyStatusDTO
    questions: List[SurveyQuestionResponseDTO]
    
    # Targeting
    appointment_id: Optional[str] = None
    user_id: Optional[str] = None
    service_id: Optional[str] = None
    professional_id: Optional[str] = None
    
    # Metadata
    created_at: str
    sent_at: Optional[str] = None
    completed_at: Optional[str] = None
    expires_at: Optional[str] = None
    
    # Analytics
    satisfaction_score: Optional[float] = None
    nps_score: Optional[int] = None
    response_count: int = 0
    
    class Config:
        from_attributes = True


class SurveyListResponseDTO(BaseModel):
    """DTO for survey list responses"""
    surveys: List[SurveyResponseDTO]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class SurveyAnalyticsDTO(BaseModel):
    """DTO for survey analytics"""
    total_surveys: int
    completed_surveys: int
    average_satisfaction: float
    average_nps: float
    completion_rate: float
    
    # NPS breakdown
    promoters: int
    passives: int
    detractors: int
    promoter_percentage: float
    detractor_percentage: float
    
    # Satisfaction levels
    satisfaction_level: str
    nps_category: str
    
    # Period
    period: Dict[str, str]
    generated_at: str
    
    class Config:
        from_attributes = True


class SurveyStatisticsDTO(BaseModel):
    """DTO for survey statistics"""
    total_surveys: int
    pending: int
    sent: int
    completed: int
    expired: int
    completion_rate: float
    generated_at: str
    
    class Config:
        from_attributes = True


class SurveyCompletionDTO(BaseModel):
    """DTO for survey completion confirmation"""
    survey_id: str
    completion_token: str
    title: str
    questions: List[SurveyQuestionResponseDTO]
    expires_at: str
    is_expired: bool = False
    
    class Config:
        from_attributes = True


class SurveyFeedbackSummaryDTO(BaseModel):
    """DTO for survey feedback summary"""
    survey_id: str
    title: str
    completion_date: str
    satisfaction_score: Optional[float] = None
    nps_score: Optional[int] = None
    key_feedback: List[str] = []
    recommendations: List[str] = []
    
    class Config:
        from_attributes = True