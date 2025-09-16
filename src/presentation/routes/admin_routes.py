from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..controllers.admin_controller import AdminController
from ...application.use_cases.appointment_use_cases import AppointmentUseCases
from ...application.use_cases.user_use_cases import UserUseCases
from ...application.use_cases.conversation_use_cases_v2 import ConversationUseCasesV2
from ...infrastructure.dependencies import (
    get_appointment_use_cases, get_user_use_cases, get_conversation_use_cases
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


def get_admin_controller(
    appointment_use_cases: AppointmentUseCases = Depends(get_appointment_use_cases),
    user_use_cases: UserUseCases = Depends(get_user_use_cases),
    conversation_use_cases: ConversationUseCasesV2 = Depends(get_conversation_use_cases)
) -> AdminController:
    """Dependency to get AdminController instance"""
    return AdminController(
        appointment_use_cases,
        user_use_cases,
        conversation_use_cases
    )


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Get dashboard overview with key metrics"""
    return await controller.get_dashboard_overview()


@router.get("/dashboard/appointments")
async def get_appointments_summary(
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    status: Optional[str] = Query(None, description="Filter by appointment status"),
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Get appointments summary with optional filters"""
    return await controller.get_appointments_summary(start_date, end_date, status)


@router.get("/dashboard/appointments/recent")
async def get_recent_appointments(
    limit: int = Query(20, ge=1, le=100, description="Number of recent appointments to return"),
    controller: AdminController = Depends(get_admin_controller)
) -> List[Dict[str, Any]]:
    """Get recent appointments for dashboard"""
    return await controller.get_recent_appointments(limit)


@router.get("/system/status")
async def get_system_status(
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Get system health and status"""
    return await controller.get_system_status()


@router.get("/configuration/availability")
async def get_availability_configuration(
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Get current availability configuration"""
    return await controller.get_availability_configuration()


@router.put("/configuration/availability")
async def update_availability_settings(
    settings: Dict[str, Any] = Body(..., description="Availability settings to update"),
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Update availability settings"""
    return await controller.update_availability_settings(settings)


@router.get("/insights/conversations")
async def get_conversation_insights(
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Get conversation insights and analytics"""
    return await controller.get_conversation_insights()


@router.get("/analytics/summary")
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Get comprehensive analytics summary"""
    try:
        # Combine multiple data sources for comprehensive analytics
        overview = await controller.get_dashboard_overview()
        
        end_date = datetime.utcnow()
        start_date = end_date.replace(day=1) if days >= 30 else end_date
        
        appointments = await controller.get_appointments_summary(
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        conversations = await controller.get_conversation_insights()
        
        return {
            "period_days": days,
            "overview": overview["overview"],
            "appointments": appointments["summary"],
            "conversations": conversations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving analytics")


@router.get("/reports/monthly")
async def get_monthly_report(
    year: int = Query(..., ge=2020, le=2030, description="Year for the report"),
    month: int = Query(..., ge=1, le=12, description="Month for the report"),
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Get monthly report with detailed metrics"""
    try:
        # Create date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Get data for the month
        appointments = await controller.get_appointments_summary(
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        return {
            "report_period": {
                "year": year,
                "month": month,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "appointments": appointments["summary"],
            "summary": {
                "total_appointments": appointments["summary"]["total_appointments"],
                "completion_rate": "85%",  # Placeholder calculation
                "cancellation_rate": "15%",  # Placeholder calculation
                "average_daily_appointments": appointments["summary"]["total_appointments"] // 30
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting monthly report: {e}")
        raise HTTPException(status_code=500, detail="Error generating monthly report")


@router.post("/actions/cleanup")
async def cleanup_system_data(
    action: str = Body(..., description="Cleanup action: 'conversations', 'logs', 'expired_tokens'"),
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Perform system cleanup actions"""
    try:
        if action == "conversations":
            # Clean up abandoned conversations
            conversation_use_cases = await get_conversation_use_cases()
            count = await conversation_use_cases.cleanup_abandoned_conversations()
            
            return {
                "action": "cleanup_conversations",
                "items_cleaned": count,
                "message": f"Se limpiaron {count} conversaciones abandonadas",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "action": action,
                "items_cleaned": 0,
                "message": f"Acción de limpieza '{action}' no implementada aún",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error performing cleanup action {action}: {e}")
        raise HTTPException(status_code=500, detail=f"Error performing cleanup: {str(e)}")


@router.get("/health")
async def admin_health_check() -> Dict[str, Any]:
    """Health check for admin service"""
    return {
        "status": "healthy",
        "service": "admin_dashboard",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }