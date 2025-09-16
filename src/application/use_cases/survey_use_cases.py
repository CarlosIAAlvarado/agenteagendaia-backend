from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from ...domain.entities.survey import Survey, SurveyQuestion, SurveyResponse, SurveyStatus, SurveyType, QuestionType
from ...domain.repositories.survey_repository import ISurveyRepository
from ...domain.repositories.appointment_repository import IAppointmentRepository
from ...domain.repositories.user_repository import IUserRepository
import logging

logger = logging.getLogger(__name__)


class SurveyUseCases:
    """Use cases for survey functionality"""
    
    def __init__(
        self,
        survey_repository: ISurveyRepository,
        appointment_repository: IAppointmentRepository,
        user_repository: IUserRepository
    ):
        self._survey_repo = survey_repository
        self._appointment_repo = appointment_repository
        self._user_repo = user_repository
    
    async def create_post_appointment_survey(
        self,
        appointment_id: str,
        user_id: str,
        service_id: Optional[str] = None,
        professional_id: Optional[str] = None
    ) -> Survey:
        """Create a post-appointment satisfaction survey"""
        try:
            # Create default post-appointment questions
            questions = [
                SurveyQuestion(
                    id=str(uuid.uuid4()),
                    question_text="¿Cómo calificarías tu experiencia general con nuestro servicio?",
                    question_type=QuestionType.RATING,
                    is_required=True,
                    order=1
                ),
                SurveyQuestion(
                    id=str(uuid.uuid4()),
                    question_text="¿Qué tan probable es que recomiendes nuestro servicio a un amigo o colega?",
                    question_type=QuestionType.NPS,
                    is_required=True,
                    order=2
                ),
                SurveyQuestion(
                    id=str(uuid.uuid4()),
                    question_text="¿El profesional fue puntual?",
                    question_type=QuestionType.YES_NO,
                    is_required=True,
                    order=3
                ),
                SurveyQuestion(
                    id=str(uuid.uuid4()),
                    question_text="¿Cómo calificarías la calidad del servicio recibido?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["Excelente", "Muy bueno", "Bueno", "Regular", "Malo"],
                    is_required=True,
                    order=4
                ),
                SurveyQuestion(
                    id=str(uuid.uuid4()),
                    question_text="¿Tienes algún comentario adicional sobre tu experiencia?",
                    question_type=QuestionType.TEXT,
                    is_required=False,
                    order=5
                )
            ]
            
            # Set expiration date (7 days from now)
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            survey = Survey(
                id=None,
                title="Encuesta de Satisfacción Post-Servicio",
                description="Tu opinión es importante para nosotros. Por favor, tómate unos minutos para evaluar tu experiencia.",
                survey_type=SurveyType.POST_APPOINTMENT,
                status=SurveyStatus.PENDING,
                questions=questions,
                appointment_id=appointment_id,
                user_id=user_id,
                service_id=service_id,
                professional_id=professional_id,
                expires_at=expires_at,
                completion_token=str(uuid.uuid4())
            )
            
            created_survey = await self._survey_repo.create_survey(survey)
            logger.info(f"Created post-appointment survey: {created_survey.id}")
            
            return created_survey
            
        except Exception as e:
            logger.error(f"Error creating post-appointment survey: {e}")
            raise
    
    async def create_general_satisfaction_survey(
        self,
        user_id: str,
        title: str = "Encuesta de Satisfacción General",
        custom_questions: Optional[List[SurveyQuestion]] = None
    ) -> Survey:
        """Create a general satisfaction survey"""
        try:
            if custom_questions:
                questions = custom_questions
            else:
                # Default general satisfaction questions
                questions = [
                    SurveyQuestion(
                        id=str(uuid.uuid4()),
                        question_text="¿Cómo evaluarías nuestro servicio en general?",
                        question_type=QuestionType.RATING,
                        is_required=True,
                        order=1
                    ),
                    SurveyQuestion(
                        id=str(uuid.uuid4()),
                        question_text="¿Nos recomendarías a otros?",
                        question_type=QuestionType.NPS,
                        is_required=True,
                        order=2
                    ),
                    SurveyQuestion(
                        id=str(uuid.uuid4()),
                        question_text="¿Qué aspecto podríamos mejorar?",
                        question_type=QuestionType.MULTIPLE_CHOICE,
                        options=[
                            "Tiempo de respuesta",
                            "Calidad del servicio",
                            "Facilidad de agendamiento",
                            "Atención al cliente",
                            "Puntualidad",
                            "Otro"
                        ],
                        is_required=False,
                        order=3
                    ),
                    SurveyQuestion(
                        id=str(uuid.uuid4()),
                        question_text="Comentarios adicionales:",
                        question_type=QuestionType.TEXT,
                        is_required=False,
                        order=4
                    )
                ]
            
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            survey = Survey(
                id=None,
                title=title,
                description="Ayúdanos a mejorar nuestros servicios con tu feedback.",
                survey_type=SurveyType.GENERAL_SATISFACTION,
                status=SurveyStatus.PENDING,
                questions=questions,
                user_id=user_id,
                expires_at=expires_at,
                completion_token=str(uuid.uuid4())
            )
            
            created_survey = await self._survey_repo.create_survey(survey)
            logger.info(f"Created general satisfaction survey: {created_survey.id}")
            
            return created_survey
            
        except Exception as e:
            logger.error(f"Error creating general satisfaction survey: {e}")
            raise
    
    async def send_survey(self, survey_id: str) -> Survey:
        """Mark survey as sent"""
        try:
            survey = await self._survey_repo.get_survey_by_id(survey_id)
            if not survey:
                raise ValueError(f"Survey {survey_id} not found")
            
            survey.status = SurveyStatus.SENT
            survey.sent_at = datetime.utcnow()
            
            updated_survey = await self._survey_repo.update_survey(survey)
            logger.info(f"Survey sent: {survey_id}")
            
            return updated_survey
            
        except Exception as e:
            logger.error(f"Error sending survey {survey_id}: {e}")
            raise
    
    async def submit_survey_response(
        self,
        survey_id: Optional[str] = None,
        completion_token: Optional[str] = None,
        responses: List[Dict[str, Any]] = []
    ) -> Survey:
        """Submit responses to a survey"""
        try:
            # Get survey by ID or token
            if survey_id:
                survey = await self._survey_repo.get_survey_by_id(survey_id)
            elif completion_token:
                survey = await self._survey_repo.get_survey_by_token(completion_token)
            else:
                raise ValueError("Either survey_id or completion_token must be provided")
            
            if not survey:
                raise ValueError("Survey not found")
            
            if survey.is_expired():
                raise ValueError("Survey has expired")
            
            if survey.is_completed():
                raise ValueError("Survey already completed")
            
            # Validate and add responses
            for response_data in responses:
                question_id = response_data.get("question_id")
                response_value = response_data.get("response_value")
                response_text = response_data.get("response_text")
                
                # Validate question exists
                question = next((q for q in survey.questions if q.id == question_id), None)
                if not question:
                    raise ValueError(f"Question {question_id} not found in survey")
                
                # Validate required questions
                if question.is_required and (response_value is None or response_value == ""):
                    raise ValueError(f"Question '{question.question_text}' is required")
                
                # Create and add response
                survey_response = SurveyResponse(
                    id=None,
                    survey_id=survey.id,
                    question_id=question_id,
                    response_value=response_value,
                    response_text=response_text,
                    submitted_at=datetime.utcnow()
                )
                
                # Add to repository
                await self._survey_repo.add_response(survey_response)
                survey.add_response(survey_response)
            
            # Mark survey as completed
            survey.complete_survey()
            updated_survey = await self._survey_repo.update_survey(survey)
            
            logger.info(f"Survey completed: {survey.id}")
            return updated_survey
            
        except Exception as e:
            logger.error(f"Error submitting survey responses: {e}")
            raise
    
    async def get_survey_by_token(self, completion_token: str) -> Optional[Survey]:
        """Get survey for completion by token"""
        try:
            survey = await self._survey_repo.get_survey_by_token(completion_token)
            if not survey:
                return None
            
            if survey.is_expired():
                # Mark as expired
                survey.status = SurveyStatus.EXPIRED
                await self._survey_repo.update_survey(survey)
                return None
            
            return survey
            
        except Exception as e:
            logger.error(f"Error getting survey by token: {e}")
            return None
    
    async def get_user_surveys(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Survey]:
        """Get surveys for a user"""
        try:
            surveys = await self._survey_repo.get_surveys_by_user(user_id, skip, limit)
            return surveys
            
        except Exception as e:
            logger.error(f"Error getting user surveys {user_id}: {e}")
            raise
    
    async def get_satisfaction_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get satisfaction analytics"""
        try:
            analytics = await self._survey_repo.get_satisfaction_analytics(start_date, end_date)
            
            # Add additional metrics
            avg_satisfaction = await self._survey_repo.get_average_satisfaction_score(
                start_date, end_date
            )
            
            nps_analytics = await self._survey_repo.get_nps_analytics(start_date, end_date)
            
            # Combine results
            comprehensive_analytics = {
                **analytics,
                "average_satisfaction_score": avg_satisfaction,
                "nps_analytics": nps_analytics,
                "satisfaction_level": self._get_satisfaction_level(avg_satisfaction),
                "nps_category": self._get_nps_category(nps_analytics.get("average_nps", 0))
            }
            
            return comprehensive_analytics
            
        except Exception as e:
            logger.error(f"Error getting satisfaction analytics: {e}")
            raise
    
    async def cleanup_expired_surveys(self) -> int:
        """Mark expired surveys and return count"""
        try:
            expired_surveys = await self._survey_repo.get_expired_surveys()
            count = 0
            
            for survey in expired_surveys:
                survey.status = SurveyStatus.EXPIRED
                await self._survey_repo.update_survey(survey)
                count += 1
            
            if count > 0:
                logger.info(f"Marked {count} surveys as expired")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired surveys: {e}")
            raise
    
    async def get_survey_statistics(self) -> Dict[str, Any]:
        """Get overall survey statistics"""
        try:
            total_pending = await self._survey_repo.count_surveys_by_status(SurveyStatus.PENDING)
            total_sent = await self._survey_repo.count_surveys_by_status(SurveyStatus.SENT)
            total_completed = await self._survey_repo.count_surveys_by_status(SurveyStatus.COMPLETED)
            total_expired = await self._survey_repo.count_surveys_by_status(SurveyStatus.EXPIRED)
            
            total_surveys = total_pending + total_sent + total_completed + total_expired
            completion_rate = (total_completed / (total_sent + total_completed)) * 100 if (total_sent + total_completed) > 0 else 0
            
            return {
                "total_surveys": total_surveys,
                "pending": total_pending,
                "sent": total_sent,
                "completed": total_completed,
                "expired": total_expired,
                "completion_rate": round(completion_rate, 1),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting survey statistics: {e}")
            raise
    
    def _get_satisfaction_level(self, score: Optional[float]) -> str:
        """Get satisfaction level description"""
        if score is None:
            return "Sin datos"
        
        if score >= 80:
            return "Excelente"
        elif score >= 70:
            return "Muy bueno"
        elif score >= 60:
            return "Bueno"
        elif score >= 50:
            return "Regular"
        else:
            return "Necesita mejoras"
    
    def _get_nps_category(self, nps_score: float) -> str:
        """Get NPS category description"""
        if nps_score >= 50:
            return "Excelente"
        elif nps_score >= 0:
            return "Bueno"
        elif nps_score >= -50:
            return "Mejorable"
        else:
            return "Crítico"