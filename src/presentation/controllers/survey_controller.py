from fastapi import HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ...application.use_cases.survey_use_cases import SurveyUseCases
from ...application.dto.survey_dto import (
    SurveyCreateDTO, SurveyResponseDTO, SurveySubmissionDTO, SurveyListResponseDTO,
    SurveyAnalyticsDTO, SurveyStatisticsDTO, SurveyCompletionDTO, SurveyFeedbackSummaryDTO
)
import logging

logger = logging.getLogger(__name__)


class SurveyController:
    """Controller for Survey endpoints"""
    
    def __init__(self, survey_use_cases: SurveyUseCases):
        self.survey_use_cases = survey_use_cases
    
    async def create_post_appointment_survey(
        self,
        appointment_id: str,
        user_id: str,
        service_id: Optional[str] = None,
        professional_id: Optional[str] = None
    ) -> SurveyResponseDTO:
        """Create a post-appointment satisfaction survey"""
        try:
            survey = await self.survey_use_cases.create_post_appointment_survey(
                appointment_id=appointment_id,
                user_id=user_id,
                service_id=service_id,
                professional_id=professional_id
            )
            
            return self._survey_to_response_dto(survey)
            
        except Exception as e:
            logger.error(f"Error creating post-appointment survey: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating survey"
            )
    
    async def create_general_survey(self, survey_data: SurveyCreateDTO) -> SurveyResponseDTO:
        """Create a general satisfaction survey"""
        try:
            survey = await self.survey_use_cases.create_general_satisfaction_survey(
                user_id=survey_data.user_id,
                title=survey_data.title
            )
            
            return self._survey_to_response_dto(survey)
            
        except Exception as e:
            logger.error(f"Error creating general survey: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating survey"
            )
    
    async def get_survey_for_completion(self, completion_token: str) -> SurveyCompletionDTO:
        """Get survey for completion by token"""
        try:
            survey = await self.survey_use_cases.get_survey_by_token(completion_token)
            
            if not survey:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Survey not found or expired"
                )
            
            return SurveyCompletionDTO(
                survey_id=survey.id,
                completion_token=survey.completion_token,
                title=survey.title,
                questions=[
                    {
                        "id": q.id,
                        "question_text": q.question_text,
                        "question_type": q.question_type.value,
                        "is_required": q.is_required,
                        "options": q.options,
                        "order": q.order
                    } for q in survey.questions
                ],
                expires_at=survey.expires_at.isoformat() if survey.expires_at else "",
                is_expired=survey.is_expired()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting survey for completion: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving survey"
            )
    
    async def submit_survey(self, submission_data: SurveySubmissionDTO) -> SurveyFeedbackSummaryDTO:
        """Submit survey responses"""
        try:
            survey = await self.survey_use_cases.submit_survey_response(
                survey_id=submission_data.survey_id,
                completion_token=submission_data.completion_token,
                responses=[
                    {
                        "question_id": r.question_id,
                        "response_value": r.response_value,
                        "response_text": r.response_text
                    } for r in submission_data.responses
                ]
            )
            
            # Generate feedback summary
            key_feedback = []
            recommendations = []
            
            if survey.satisfaction_score:
                if survey.satisfaction_score >= 80:
                    key_feedback.append("Excelente nivel de satisfacción")
                    recommendations.append("Mantener el alto nivel de servicio")
                elif survey.satisfaction_score >= 60:
                    key_feedback.append("Buen nivel de satisfacción")
                    recommendations.append("Identificar áreas de mejora específicas")
                else:
                    key_feedback.append("Nivel de satisfacción mejorable")
                    recommendations.append("Revisar procesos y entrenamientos")
            
            if survey.get_nps_score():
                nps = survey.get_nps_score()
                if nps >= 50:
                    key_feedback.append("Excelente NPS - Clientes promotores")
                elif nps >= 0:
                    key_feedback.append("NPS positivo - Clientes satisfechos")
                else:
                    key_feedback.append("NPS negativo - Atención urgente requerida")
            
            return SurveyFeedbackSummaryDTO(
                survey_id=survey.id,
                title=survey.title,
                completion_date=survey.completed_at.isoformat() if survey.completed_at else "",
                satisfaction_score=survey.satisfaction_score,
                nps_score=survey.get_nps_score(),
                key_feedback=key_feedback,
                recommendations=recommendations
            )
            
        except ValueError as e:
            logger.warning(f"Survey submission validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error submitting survey: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error submitting survey"
            )
    
    async def get_user_surveys(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> SurveyListResponseDTO:
        """Get surveys for a user"""
        try:
            if skip < 0 or limit <= 0 or limit > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination parameters"
                )
            
            surveys = await self.survey_use_cases.get_user_surveys(user_id, skip, limit)
            
            survey_dtos = [self._survey_to_response_dto(survey) for survey in surveys]
            
            return SurveyListResponseDTO(
                surveys=survey_dtos,
                total=len(survey_dtos),  # In a real scenario, get actual total count
                skip=skip,
                limit=limit
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user surveys {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user surveys"
            )
    
    async def get_survey_analytics(
        self,
        start_date: str,
        end_date: str,
        service_id: Optional[str] = None,
        professional_id: Optional[str] = None
    ) -> SurveyAnalyticsDTO:
        """Get survey analytics for date range"""
        try:
            # Parse dates
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
            
            if start_dt >= end_dt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date must be before end date"
                )
            
            analytics = await self.survey_use_cases.get_satisfaction_analytics(
                start_dt, end_dt
            )
            
            return SurveyAnalyticsDTO(
                total_surveys=analytics.get("total_surveys", 0),
                completed_surveys=analytics.get("total_surveys", 0),  # Assuming all are completed for analytics
                average_satisfaction=analytics.get("average_satisfaction_score", 0.0) or 0.0,
                average_nps=analytics.get("nps_analytics", {}).get("average_nps", 0.0),
                completion_rate=85.0,  # Mock completion rate
                promoters=analytics.get("nps_analytics", {}).get("promoters", 0),
                passives=analytics.get("nps_analytics", {}).get("passives", 0),
                detractors=analytics.get("nps_analytics", {}).get("detractors", 0),
                promoter_percentage=analytics.get("nps_analytics", {}).get("promoter_percentage", 0.0),
                detractor_percentage=analytics.get("nps_analytics", {}).get("detractor_percentage", 0.0),
                satisfaction_level=analytics.get("satisfaction_level", "Sin datos"),
                nps_category=analytics.get("nps_category", "Sin datos"),
                period={
                    "start_date": start_date,
                    "end_date": end_date
                },
                generated_at=datetime.utcnow().isoformat()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting survey analytics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving survey analytics"
            )
    
    async def get_survey_statistics(self) -> SurveyStatisticsDTO:
        """Get overall survey statistics"""
        try:
            stats = await self.survey_use_cases.get_survey_statistics()
            
            return SurveyStatisticsDTO(**stats)
            
        except Exception as e:
            logger.error(f"Error getting survey statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving survey statistics"
            )
    
    async def cleanup_expired_surveys(self) -> Dict[str, Any]:
        """Clean up expired surveys (admin endpoint)"""
        try:
            count = await self.survey_use_cases.cleanup_expired_surveys()
            
            return {
                "message": f"Marked {count} surveys as expired",
                "count": count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up expired surveys: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error cleaning up surveys"
            )
    
    async def send_survey(self, survey_id: str) -> SurveyResponseDTO:
        """Send survey to user"""
        try:
            survey = await self.survey_use_cases.send_survey(survey_id)
            
            return self._survey_to_response_dto(survey)
            
        except ValueError as e:
            logger.warning(f"Error sending survey: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error sending survey {survey_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error sending survey"
            )
    
    def _survey_to_response_dto(self, survey) -> SurveyResponseDTO:
        """Convert survey entity to response DTO"""
        return SurveyResponseDTO(
            id=survey.id,
            title=survey.title,
            description=survey.description,
            survey_type=survey.survey_type.value,
            status=survey.status.value,
            questions=[
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "question_type": q.question_type.value,
                    "is_required": q.is_required,
                    "options": q.options,
                    "order": q.order
                } for q in survey.questions
            ],
            appointment_id=survey.appointment_id,
            user_id=survey.user_id,
            service_id=survey.service_id,
            professional_id=survey.professional_id,
            created_at=survey.created_at.isoformat() if survey.created_at else "",
            sent_at=survey.sent_at.isoformat() if survey.sent_at else None,
            completed_at=survey.completed_at.isoformat() if survey.completed_at else None,
            expires_at=survey.expires_at.isoformat() if survey.expires_at else None,
            satisfaction_score=survey.calculate_satisfaction_score(),
            nps_score=survey.get_nps_score(),
            response_count=len(survey.responses) if survey.responses else 0
        )