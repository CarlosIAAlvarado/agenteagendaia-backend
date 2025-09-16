from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from ....domain.entities.survey import Survey, SurveyQuestion, SurveyResponse, SurveyStatus, SurveyType, QuestionType


class SurveyMapper:
    """Maps between Survey domain entities and MongoDB documents"""
    
    @staticmethod
    def to_document(survey: Survey) -> Dict[str, Any]:
        """Convert Survey entity to MongoDB document"""
        doc = {
            "title": survey.title,
            "description": survey.description,
            "survey_type": survey.survey_type.value,
            "status": survey.status.value,
            "questions": [SurveyMapper.question_to_dict(q) for q in survey.questions],
            "appointment_id": survey.appointment_id,
            "user_id": survey.user_id,
            "service_id": survey.service_id,
            "professional_id": survey.professional_id,
            "created_at": survey.created_at,
            "sent_at": survey.sent_at,
            "completed_at": survey.completed_at,
            "expires_at": survey.expires_at,
            "completion_token": survey.completion_token,
            "satisfaction_score": survey.calculate_satisfaction_score(),
            "nps_score": survey.get_nps_score()
        }
        
        if survey.id is not None:
            doc["_id"] = ObjectId(survey.id)
        
        return doc
    
    @staticmethod
    def from_document(doc: Dict[str, Any]) -> Survey:
        """Convert MongoDB document to Survey entity"""
        survey_id = str(doc["_id"]) if "_id" in doc else None
        
        questions = [
            SurveyMapper.question_from_dict(q) for q in doc.get("questions", [])
        ]
        
        return Survey(
            id=survey_id,
            title=doc["title"],
            description=doc["description"],
            survey_type=SurveyType(doc["survey_type"]),
            status=SurveyStatus(doc["status"]),
            questions=questions,
            appointment_id=doc.get("appointment_id"),
            user_id=doc.get("user_id"),
            service_id=doc.get("service_id"),
            professional_id=doc.get("professional_id"),
            created_at=doc["created_at"],
            sent_at=doc.get("sent_at"),
            completed_at=doc.get("completed_at"),
            expires_at=doc.get("expires_at"),
            completion_token=doc.get("completion_token"),
            responses=[]  # Responses loaded separately
        )
    
    @staticmethod
    def to_update_document(survey: Survey) -> Dict[str, Any]:
        """Convert Survey entity to MongoDB update document"""
        update_doc = {
            "$set": {
                "title": survey.title,
                "description": survey.description,
                "survey_type": survey.survey_type.value,
                "status": survey.status.value,
                "questions": [SurveyMapper.question_to_dict(q) for q in survey.questions],
                "appointment_id": survey.appointment_id,
                "user_id": survey.user_id,
                "service_id": survey.service_id,
                "professional_id": survey.professional_id,
                "sent_at": survey.sent_at,
                "completed_at": survey.completed_at,
                "expires_at": survey.expires_at,
                "completion_token": survey.completion_token,
                "satisfaction_score": survey.calculate_satisfaction_score(),
                "nps_score": survey.get_nps_score()
            }
        }
        
        return update_doc
    
    @staticmethod
    def question_to_dict(question: SurveyQuestion) -> Dict[str, Any]:
        """Convert SurveyQuestion to dictionary"""
        return {
            "id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type.value,
            "is_required": question.is_required,
            "options": question.options,
            "order": question.order
        }
    
    @staticmethod
    def question_from_dict(data: Dict[str, Any]) -> SurveyQuestion:
        """Convert dictionary to SurveyQuestion"""
        return SurveyQuestion(
            id=data.get("id"),
            question_text=data["question_text"],
            question_type=QuestionType(data["question_type"]),
            is_required=data.get("is_required", True),
            options=data.get("options"),
            order=data.get("order", 0)
        )
    
    @staticmethod
    def response_to_document(response: SurveyResponse) -> Dict[str, Any]:
        """Convert SurveyResponse entity to MongoDB document"""
        doc = {
            "survey_id": response.survey_id,
            "question_id": response.question_id,
            "response_value": response.response_value,
            "response_text": response.response_text,
            "submitted_at": response.submitted_at or datetime.utcnow()
        }
        
        if response.id is not None:
            doc["_id"] = ObjectId(response.id)
        
        return doc
    
    @staticmethod
    def response_from_document(doc: Dict[str, Any]) -> SurveyResponse:
        """Convert MongoDB document to SurveyResponse entity"""
        response_id = str(doc["_id"]) if "_id" in doc else None
        
        return SurveyResponse(
            id=response_id,
            survey_id=doc["survey_id"],
            question_id=doc["question_id"],
            response_value=doc["response_value"],
            response_text=doc.get("response_text"),
            submitted_at=doc["submitted_at"]
        )