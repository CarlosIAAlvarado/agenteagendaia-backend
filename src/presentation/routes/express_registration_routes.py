from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional
from datetime import datetime
from ..controllers.express_registration_controller import ExpressRegistrationController
from ...application.use_cases.express_registration_use_cases import ExpressRegistrationUseCases
from ...application.dto.express_registration_dto import (
    ExpressRegistrationDTO, ExpressRegistrationResponseDTO,
    ExpressRegistrationStatsDTO, QuickRegistrationFormDTO
)
from ...infrastructure.dependencies import get_user_use_cases, get_conversation_use_cases
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/register", tags=["Express Registration"])


def get_express_registration_use_cases(
    user_use_cases = Depends(get_user_use_cases),
    conversation_use_cases = Depends(get_conversation_use_cases)
) -> ExpressRegistrationUseCases:
    """Get ExpressRegistrationUseCases instance"""
    return ExpressRegistrationUseCases(
        user_use_cases._user_repo,
        conversation_use_cases._conversation_repo
    )


def get_express_registration_controller(
    express_registration_use_cases: ExpressRegistrationUseCases = Depends(get_express_registration_use_cases)
) -> ExpressRegistrationController:
    """Get ExpressRegistrationController instance"""
    return ExpressRegistrationController(express_registration_use_cases)


@router.post("/express", response_model=ExpressRegistrationResponseDTO)
async def register_user_express(
    registration_data: ExpressRegistrationDTO,
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> ExpressRegistrationResponseDTO:
    """
    Register user with express form (3 required fields: name, email, phone)
    As specified in the PDF document for unregistered users in conversation flow.
    """
    return await controller.register_user(registration_data)


@router.get("/form", response_model=QuickRegistrationFormDTO)
async def get_registration_form(
    conversation_id: Optional[str] = Query(None, description="ID of current conversation"),
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> QuickRegistrationFormDTO:
    """Get registration form configuration for frontend rendering"""
    return await controller.get_registration_form(conversation_id)


@router.post("/validate")
async def validate_registration_data(
    email: str = Body(..., description="Email to validate"),
    phone: str = Body(..., description="Phone number to validate"),
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> Dict[str, Any]:
    """Validate registration data before submission (check for duplicates, etc.)"""
    return await controller.validate_registration_data(email, phone)


@router.post("/verify/{user_id}")
async def verify_user_registration(
    user_id: str,
    verification_code: str = Body(..., description="Verification code received by user"),
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> Dict[str, Any]:
    """Verify user registration with verification code"""
    return await controller.verify_registration(user_id, verification_code)


@router.post("/verify/{user_id}/resend")
async def resend_verification_code(
    user_id: str,
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> Dict[str, Any]:
    """Resend verification code to user"""
    return await controller.resend_verification(user_id)


@router.put("/preferences/{user_id}")
async def update_communication_preferences(
    user_id: str,
    preferences: Dict[str, Any] = Body(..., description="Communication preferences to update"),
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> Dict[str, Any]:
    """Update user communication preferences"""
    return await controller.update_communication_preferences(user_id, preferences)


@router.get("/statistics", response_model=ExpressRegistrationStatsDTO)
async def get_registration_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> ExpressRegistrationStatsDTO:
    """Get registration statistics for admin dashboard"""
    return await controller.get_registration_statistics(days)


@router.get("/analytics")
async def get_registration_analytics(
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> Dict[str, Any]:
    """Get comprehensive registration analytics"""
    return await controller.get_registration_analytics()


@router.get("/dashboard/overview")
async def get_registration_dashboard_overview(
    period_days: int = Query(30, ge=1, le=365, description="Period in days for analysis"),
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> Dict[str, Any]:
    """Get registration overview for admin dashboard"""
    try:
        # Get statistics
        stats = await controller.get_registration_statistics(period_days)
        
        # Get analytics
        analytics = await controller.get_registration_analytics()
        
        return {
            "period": {
                "days": period_days,
                "end_date": datetime.utcnow().isoformat(),
                "start_date": (datetime.utcnow() - datetime.timedelta(days=period_days)).isoformat()
            },
            "key_metrics": {
                "total_registrations": stats.total_registrations,
                "today_registrations": stats.today_registrations,
                "conversion_rate": stats.conversion_rate,
                "verification_rate": (stats.verified_users / stats.total_registrations * 100) if stats.total_registrations > 0 else 0,
                "average_completion_time": stats.average_form_completion_time
            },
            "growth": {
                "daily_average": stats.month_registrations / 30,
                "weekly_trend": "+12%" if stats.week_registrations > 80 else "-5%",
                "monthly_trend": "+25%" if stats.month_registrations > 200 else "+10%"
            },
            "channel_distribution": {
                "email": stats.preferred_channels["email"],
                "sms": stats.preferred_channels["sms"],
                "whatsapp": stats.preferred_channels["whatsapp"],
                "total": sum(stats.preferred_channels.values())
            },
            "user_lifecycle": {
                "registered": stats.total_registrations,
                "verified": stats.verified_users,
                "active": stats.active_users,
                "inactive": stats.verified_users - stats.active_users
            },
            "performance_indicators": {
                "form_completion_rate": "85%",  # Mock data
                "verification_success_rate": f"{(stats.verified_users / stats.total_registrations * 100):.1f}%",
                "user_activation_rate": f"{(stats.active_users / stats.verified_users * 100):.1f}%",
                "average_time_to_first_appointment": "2.5 días"  # Mock data
            },
            "insights": analytics["insights"],
            "recommendations": analytics["recommendations"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting registration dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving registration overview")


@router.get("/conversion/funnel")
async def get_registration_conversion_funnel(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    controller: ExpressRegistrationController = Depends(get_express_registration_controller)
) -> Dict[str, Any]:
    """Get registration conversion funnel data"""
    try:
        # Mock conversion funnel data
        # In a real implementation, this would query actual conversation -> registration data
        
        total_conversations = 850
        form_views = 680  # Users who saw the registration form
        form_starts = 520  # Users who started filling the form
        form_completes = 450  # Users who completed the form
        verifications = 380  # Users who verified their accounts
        first_appointments = 320  # Users who made their first appointment
        
        funnel_data = [
            {
                "step": "Conversación iniciada",
                "count": total_conversations,
                "percentage": 100.0,
                "drop_off": 0
            },
            {
                "step": "Formulario visto",
                "count": form_views,
                "percentage": round((form_views / total_conversations) * 100, 1),
                "drop_off": total_conversations - form_views
            },
            {
                "step": "Formulario iniciado",
                "count": form_starts,
                "percentage": round((form_starts / total_conversations) * 100, 1),
                "drop_off": form_views - form_starts
            },
            {
                "step": "Registro completado",
                "count": form_completes,
                "percentage": round((form_completes / total_conversations) * 100, 1),
                "drop_off": form_starts - form_completes
            },
            {
                "step": "Email verificado",
                "count": verifications,
                "percentage": round((verifications / total_conversations) * 100, 1),
                "drop_off": form_completes - verifications
            },
            {
                "step": "Primera cita agendada",
                "count": first_appointments,
                "percentage": round((first_appointments / total_conversations) * 100, 1),
                "drop_off": verifications - first_appointments
            }
        ]
        
        return {
            "period_days": days,
            "funnel": funnel_data,
            "summary": {
                "total_entry_point": total_conversations,
                "final_conversion": first_appointments,
                "overall_conversion_rate": round((first_appointments / total_conversations) * 100, 1),
                "biggest_drop_off": {
                    "step": "Formulario visto → Iniciado",
                    "drop_off_count": form_views - form_starts,
                    "drop_off_percentage": round(((form_views - form_starts) / form_views) * 100, 1)
                }
            },
            "optimization_opportunities": [
                "Reducir abandono en formulario visto → iniciado",
                "Mejorar tasa de verificación de email",
                "Optimizar flujo hacia primera cita",
                "Simplificar proceso de registro"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting registration conversion funnel: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving conversion funnel")


@router.get("/health")
async def registration_health_check() -> Dict[str, Any]:
    """Health check for registration service"""
    return {
        "status": "healthy",
        "service": "express_registration",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "express_3_field_registration",
            "email_verification",
            "communication_preferences",
            "duplicate_detection",
            "form_validation",
            "conversion_analytics",
            "user_lifecycle_tracking"
        ],
        "form_fields": [
            "name (required)",
            "email (required)",  
            "phone (required)",
            "privacy_policy_acceptance (required)",
            "communication_channel_preference (optional)"
        ]
    }