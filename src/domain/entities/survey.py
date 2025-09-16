from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass


class SurveyStatus(Enum):
    """Survey status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    COMPLETED = "completed"
    EXPIRED = "expired"


class SurveyType(Enum):
    """Survey type enumeration"""
    POST_APPOINTMENT = "post_appointment"
    SERVICE_FEEDBACK = "service_feedback"
    GENERAL_SATISFACTION = "general_satisfaction"


class QuestionType(Enum):
    """Question type enumeration"""
    RATING = "rating"  # 1-5 stars
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    YES_NO = "yes_no"
    NPS = "nps"  # Net Promoter Score (0-10)


@dataclass
class SurveyQuestion:
    """Survey question entity"""
    id: Optional[str]
    question_text: str
    question_type: QuestionType
    is_required: bool = True
    options: Optional[List[str]] = None  # For multiple choice questions
    order: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "question_text": self.question_text,
            "question_type": self.question_type.value,
            "is_required": self.is_required,
            "options": self.options,
            "order": self.order
        }


@dataclass
class SurveyResponse:
    """Survey response entity"""
    id: Optional[str]
    survey_id: str
    question_id: str
    response_value: Any  # Can be int, str, bool depending on question type
    response_text: Optional[str] = None  # For additional comments
    submitted_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "survey_id": self.survey_id,
            "question_id": self.question_id,
            "response_value": self.response_value,
            "response_text": self.response_text,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None
        }


@dataclass
class Survey:
    """Survey entity"""
    id: Optional[str]
    title: str
    description: str
    survey_type: SurveyType
    status: SurveyStatus
    questions: List[SurveyQuestion]
    
    # Targeting
    appointment_id: Optional[str] = None
    user_id: Optional[str] = None
    service_id: Optional[str] = None
    professional_id: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Response tracking
    responses: List[SurveyResponse] = None
    completion_token: Optional[str] = None  # Unique token for anonymous completion
    
    def __post_init__(self):
        if self.responses is None:
            self.responses = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def add_response(self, response: SurveyResponse) -> None:
        """Add a response to the survey"""
        self.responses.append(response)
    
    def is_completed(self) -> bool:
        """Check if survey is completed"""
        return self.status == SurveyStatus.COMPLETED
    
    def is_expired(self) -> bool:
        """Check if survey is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def complete_survey(self) -> None:
        """Mark survey as completed"""
        self.status = SurveyStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def calculate_satisfaction_score(self) -> Optional[float]:
        """Calculate overall satisfaction score from responses"""
        if not self.responses:
            return None
        
        rating_responses = [
            r for r in self.responses 
            if r.question_id and any(
                q.question_type in [QuestionType.RATING, QuestionType.NPS] 
                for q in self.questions 
                if q.id == r.question_id
            )
        ]
        
        if not rating_responses:
            return None
        
        total_score = 0
        max_possible_score = 0
        
        for response in rating_responses:
            question = next((q for q in self.questions if q.id == response.question_id), None)
            if question:
                if question.question_type == QuestionType.RATING:
                    # Rating questions are 1-5
                    total_score += float(response.response_value)
                    max_possible_score += 5.0
                elif question.question_type == QuestionType.NPS:
                    # NPS questions are 0-10
                    total_score += float(response.response_value)
                    max_possible_score += 10.0
        
        if max_possible_score == 0:
            return None
        
        # Return as percentage
        return (total_score / max_possible_score) * 100
    
    def get_nps_score(self) -> Optional[int]:
        """Calculate Net Promoter Score from NPS questions"""
        nps_responses = []
        
        for response in self.responses:
            question = next((q for q in self.questions if q.id == response.question_id), None)
            if question and question.question_type == QuestionType.NPS:
                nps_responses.append(int(response.response_value))
        
        if not nps_responses:
            return None
        
        # Calculate NPS: % Promoters (9-10) - % Detractors (0-6)
        promoters = len([r for r in nps_responses if r >= 9])
        detractors = len([r for r in nps_responses if r <= 6])
        total = len(nps_responses)
        
        if total == 0:
            return None
        
        nps = ((promoters - detractors) / total) * 100
        return round(nps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert survey to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "survey_type": self.survey_type.value,
            "status": self.status.value,
            "questions": [q.to_dict() for q in self.questions],
            "appointment_id": self.appointment_id,
            "user_id": self.user_id,
            "service_id": self.service_id,
            "professional_id": self.professional_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "responses": [r.to_dict() for r in self.responses] if self.responses else [],
            "completion_token": self.completion_token,
            "satisfaction_score": self.calculate_satisfaction_score(),
            "nps_score": self.get_nps_score()
        }