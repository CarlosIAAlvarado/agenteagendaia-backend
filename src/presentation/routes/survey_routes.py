from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..controllers.survey_controller import SurveyController
from ...application.use_cases.survey_use_cases import SurveyUseCases
from ...application.dto.survey_dto import (
    SurveyCreateDTO, SurveyResponseDTO, SurveySubmissionDTO, SurveyListResponseDTO,
    SurveyAnalyticsDTO, SurveyStatisticsDTO, SurveyCompletionDTO, SurveyFeedbackSummaryDTO
)
from ...infrastructure.database.repositories.survey_repository import SurveyRepository
from ...infrastructure.dependencies import get_appointment_use_cases, get_user_use_cases
from ...infrastructure.database.connection import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/surveys", tags=["Surveys & Satisfaction"])


def get_survey_repository():
    """Get SurveyRepository instance"""
    database = get_database()
    return SurveyRepository(database)


def get_survey_use_cases(
    appointment_use_cases = Depends(get_appointment_use_cases),
    user_use_cases = Depends(get_user_use_cases)
) -> SurveyUseCases:
    """Get SurveyUseCases instance"""
    survey_repository = get_survey_repository()
    
    return SurveyUseCases(
        survey_repository,
        appointment_use_cases._appointment_repo,
        user_use_cases._user_repo
    )


def get_survey_controller(
    survey_use_cases: SurveyUseCases = Depends(get_survey_use_cases)
) -> SurveyController:
    """Get SurveyController instance"""
    return SurveyController(survey_use_cases)


@router.post("/post-appointment", response_model=SurveyResponseDTO)
async def create_post_appointment_survey(
    appointment_id: str = Body(..., description="ID of the appointment"),
    user_id: str = Body(..., description="ID of the user"),
    service_id: Optional[str] = Body(None, description="ID of the service"),
    professional_id: Optional[str] = Body(None, description="ID of the professional"),
    controller: SurveyController = Depends(get_survey_controller)
) -> SurveyResponseDTO:
    """Create a post-appointment satisfaction survey"""
    return await controller.create_post_appointment_survey(
        appointment_id=appointment_id,
        user_id=user_id,
        service_id=service_id,
        professional_id=professional_id
    )


@router.post("/general", response_model=SurveyResponseDTO)
async def create_general_survey(
    survey_data: SurveyCreateDTO,
    controller: SurveyController = Depends(get_survey_controller)
) -> SurveyResponseDTO:
    """Create a general satisfaction survey"""
    return await controller.create_general_survey(survey_data)


@router.get("/complete/{completion_token}", response_model=SurveyCompletionDTO)
async def get_survey_for_completion(
    completion_token: str,
    controller: SurveyController = Depends(get_survey_controller)
) -> SurveyCompletionDTO:
    """Get survey for completion by token"""
    return await controller.get_survey_for_completion(completion_token)


@router.post("/submit", response_model=SurveyFeedbackSummaryDTO)
async def submit_survey(
    submission_data: SurveySubmissionDTO,
    controller: SurveyController = Depends(get_survey_controller)
) -> SurveyFeedbackSummaryDTO:
    """Submit survey responses"""
    return await controller.submit_survey(submission_data)


@router.post("/{survey_id}/send", response_model=SurveyResponseDTO)
async def send_survey(
    survey_id: str,
    controller: SurveyController = Depends(get_survey_controller)
) -> SurveyResponseDTO:
    """Send survey to user (mark as sent)"""
    return await controller.send_survey(survey_id)


@router.get("/users/{user_id}", response_model=SurveyListResponseDTO)
async def get_user_surveys(
    user_id: str,
    skip: int = Query(0, ge=0, description="Number of surveys to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of surveys to return"),
    controller: SurveyController = Depends(get_survey_controller)
) -> SurveyListResponseDTO:
    """Get surveys for a user"""
    return await controller.get_user_surveys(user_id, skip, limit)


@router.get("/analytics", response_model=SurveyAnalyticsDTO)
async def get_survey_analytics(
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DDTHH:MM:SS)"),
    end_date: str = Query(..., description="End date in ISO format (YYYY-MM-DDTHH:MM:SS)"),
    service_id: Optional[str] = Query(None, description="Filter by service ID"),
    professional_id: Optional[str] = Query(None, description="Filter by professional ID"),
    controller: SurveyController = Depends(get_survey_controller)
) -> SurveyAnalyticsDTO:
    """Get survey analytics for date range"""
    return await controller.get_survey_analytics(
        start_date=start_date,
        end_date=end_date,
        service_id=service_id,
        professional_id=professional_id
    )


@router.get("/statistics", response_model=SurveyStatisticsDTO)
async def get_survey_statistics(
    controller: SurveyController = Depends(get_survey_controller)
) -> SurveyStatisticsDTO:
    """Get overall survey statistics"""
    return await controller.get_survey_statistics()


@router.post("/admin/cleanup")
async def cleanup_expired_surveys(
    controller: SurveyController = Depends(get_survey_controller)
) -> Dict[str, Any]:
    """Clean up expired surveys (admin endpoint)"""
    return await controller.cleanup_expired_surveys()


@router.get("/dashboard/overview")
async def get_survey_dashboard_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    controller: SurveyController = Depends(get_survey_controller)
) -> Dict[str, Any]:
    """Get comprehensive survey overview for dashboard"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date.replace(day=1) if days >= 30 else end_date
        
        # Get analytics
        analytics = await controller.get_survey_analytics(
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        # Get statistics
        statistics = await controller.get_survey_statistics()
        
        return {
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "analytics": {
                "satisfaction": {
                    "average_score": analytics.average_satisfaction,
                    "level": analytics.satisfaction_level,
                    "total_responses": analytics.total_surveys
                },
                "nps": {
                    "score": analytics.average_nps,
                    "category": analytics.nps_category,
                    "promoters": analytics.promoters,
                    "detractors": analytics.detractors,
                    "promoter_percentage": analytics.promoter_percentage
                }
            },
            "statistics": {
                "total_surveys": statistics.total_surveys,
                "completion_rate": statistics.completion_rate,
                "pending": statistics.pending,
                "completed": statistics.completed
            },
            "insights": [
                f"Nivel de satisfacción: {analytics.satisfaction_level}",
                f"Categoría NPS: {analytics.nps_category}",
                f"Tasa de completación: {statistics.completion_rate}%",
                f"Encuestas pendientes: {statistics.pending}"
            ],
            "recommendations": [
                "Aumentar seguimiento a encuestas pendientes" if statistics.pending > 10 else "Buen control de encuestas pendientes",
                "Mejorar experiencia del usuario" if analytics.average_satisfaction < 70 else "Mantener alto nivel de satisfacción",
                "Implementar acciones para convertir detractores" if analytics.detractor_percentage > 20 else "Excelente distribución NPS"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting survey dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving survey overview")


@router.get("/satisfaction/trends")
async def get_satisfaction_trends(
    days: int = Query(30, ge=7, le=365, description="Number of days for trend analysis"),
    controller: SurveyController = Depends(get_survey_controller)
) -> Dict[str, Any]:
    """Get satisfaction score trends over time"""
    try:
        # This would typically query historical data
        # For now, generate mock trend data
        from datetime import timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generate weekly trend data
        trend_data = []
        weeks = days // 7
        
        for i in range(weeks):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            
            # Mock satisfaction data with some variation
            base_satisfaction = 75.0
            variation = (i % 4 - 1.5) * 5  # Creates some ups and downs
            satisfaction_score = max(50.0, min(95.0, base_satisfaction + variation))
            
            trend_data.append({
                "period": f"Semana {i+1}",
                "start_date": week_start.date().isoformat(),
                "end_date": week_end.date().isoformat(),
                "satisfaction_score": round(satisfaction_score, 1),
                "survey_count": 15 + (i % 3) * 5,  # Mock survey count
                "nps_score": round(satisfaction_score - 25, 1)  # Mock NPS
            })
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "trends": trend_data,
            "summary": {
                "average_satisfaction": sum(d["satisfaction_score"] for d in trend_data) / len(trend_data) if trend_data else 0,
                "trend_direction": "up" if trend_data and trend_data[-1]["satisfaction_score"] > trend_data[0]["satisfaction_score"] else "down",
                "total_surveys": sum(d["survey_count"] for d in trend_data),
                "best_week": max(trend_data, key=lambda x: x["satisfaction_score"]) if trend_data else None
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting satisfaction trends: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving satisfaction trends")


@router.get("/feedback/summary")
async def get_feedback_summary(
    days: int = Query(7, ge=1, le=30, description="Number of recent days to analyze"),
    controller: SurveyController = Depends(get_survey_controller)
) -> Dict[str, Any]:
    """Get recent feedback summary and insights"""
    try:
        # Mock recent feedback data
        recent_feedback = {
            "total_responses": 45,
            "average_satisfaction": 4.2,
            "common_themes": [
                {"theme": "Puntualidad", "mentions": 28, "sentiment": "positive"},
                {"theme": "Calidad del servicio", "mentions": 35, "sentiment": "positive"},
                {"theme": "Facilidad de agendamiento", "mentions": 22, "sentiment": "positive"},
                {"theme": "Tiempo de espera", "mentions": 12, "sentiment": "negative"},
                {"theme": "Comunicación", "mentions": 18, "sentiment": "neutral"}
            ],
            "satisfaction_distribution": {
                "5_stars": 18,
                "4_stars": 15,
                "3_stars": 8,
                "2_stars": 3,
                "1_stars": 1
            },
            "nps_distribution": {
                "promoters": 25,  # 9-10
                "passives": 15,   # 7-8
                "detractors": 5   # 0-6
            },
            "top_compliments": [
                "Excelente atención y profesionalismo",
                "Muy puntual y eficiente",
                "Fácil de agendar citas",
                "Personal muy amable",
                "Instalaciones limpias y cómodas"
            ],
            "improvement_areas": [
                "Reducir tiempo de espera",
                "Mejorar comunicación previa",
                "Ampliar horarios disponibles",
                "Mejorar sistema de notificaciones"
            ]
        }
        
        # Calculate NPS
        total_nps_responses = sum(recent_feedback["nps_distribution"].values())
        nps_score = ((recent_feedback["nps_distribution"]["promoters"] - 
                     recent_feedback["nps_distribution"]["detractors"]) / 
                     total_nps_responses * 100) if total_nps_responses > 0 else 0
        
        return {
            "period": f"Últimos {days} días",
            "summary": recent_feedback,
            "calculated_metrics": {
                "nps_score": round(nps_score, 1),
                "satisfaction_percentage": round((recent_feedback["average_satisfaction"] / 5) * 100, 1),
                "response_rate": "68%",  # Mock response rate
                "completion_time_avg": "2.3 minutos"
            },
            "insights": [
                "Alta satisfacción general con el servicio",
                "Puntualidad es el aspecto mejor valorado",
                "Oportunidad de mejora en tiempos de espera",
                "NPS indica clientes muy satisfechos"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting feedback summary: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving feedback summary")


@router.get("/health")
async def survey_health_check() -> Dict[str, Any]:
    """Health check for survey service"""
    return {
        "status": "healthy",
        "service": "surveys",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "post_appointment_surveys",
            "general_satisfaction_surveys",
            "anonymous_completion",
            "nps_scoring",
            "satisfaction_analytics",
            "feedback_trends",
            "automatic_expiration"
        ]
    }