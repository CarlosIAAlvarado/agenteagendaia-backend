from fastapi import HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ...application.use_cases.appointment_use_cases import AppointmentUseCases
from ...application.use_cases.user_use_cases import UserUseCases
from ...application.use_cases.conversation_use_cases_v2 import ConversationUseCasesV2
from ...application.dto.appointment_dto import AppointmentResponseDTO
from ...application.dto.user_dto import UserResponseDTO
from ...application.dto.conversation_dto import ConversationResponseDTO
import logging

logger = logging.getLogger(__name__)


class AdminController:
    """Controller for Admin Dashboard functionality"""
    
    def __init__(
        self,
        appointment_use_cases: AppointmentUseCases,
        user_use_cases: UserUseCases,
        conversation_use_cases: ConversationUseCasesV2
    ):
        self.appointment_use_cases = appointment_use_cases
        self.user_use_cases = user_use_cases
        self.conversation_use_cases = conversation_use_cases
    
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get dashboard overview with key metrics"""
        try:
            today = datetime.utcnow()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # Get basic counts
            total_appointments = await self._get_appointment_count_by_period(month_ago, today)
            total_users = await self._get_user_count()
            active_conversations = await self._get_active_conversation_count()
            
            # Get today's appointments
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            today_appointments = await self._get_appointment_count_by_period(today_start, today_end)
            
            # Get week stats
            week_appointments = await self._get_appointment_count_by_period(week_ago, today)
            
            # Get revenue if applicable (placeholder for now)
            estimated_revenue = total_appointments * 50  # Assumindo $50 por cita promedio
            
            return {
                "overview": {
                    "total_appointments_month": total_appointments,
                    "total_users": total_users,
                    "active_conversations": active_conversations,
                    "today_appointments": today_appointments,
                    "week_appointments": week_appointments,
                    "estimated_revenue": estimated_revenue
                },
                "period": {
                    "start_date": month_ago.isoformat(),
                    "end_date": today.isoformat()
                },
                "generated_at": today.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving dashboard data"
            )
    
    async def get_appointments_summary(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get appointments summary with filters"""
        try:
            # Parse dates or use defaults
            if not start_date:
                start_dt = datetime.utcnow() - timedelta(days=30)
            else:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            
            if not end_date:
                end_dt = datetime.utcnow()
            else:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Get appointments (this would need to be implemented in use cases)
            appointments_by_status = {
                "scheduled": await self._get_appointment_count_by_status("scheduled", start_dt, end_dt),
                "completed": await self._get_appointment_count_by_status("completed", start_dt, end_dt),
                "cancelled": await self._get_appointment_count_by_status("cancelled", start_dt, end_dt),
                "no_show": await self._get_appointment_count_by_status("no_show", start_dt, end_dt)
            }
            
            total = sum(appointments_by_status.values())
            
            return {
                "summary": {
                    "total_appointments": total,
                    "by_status": appointments_by_status,
                    "period": {
                        "start_date": start_dt.isoformat(),
                        "end_date": end_dt.isoformat()
                    }
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error getting appointments summary: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving appointments data"
            )
    
    async def get_recent_appointments(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent appointments for dashboard"""
        try:
            # This would need to be implemented in appointment use cases
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting recent appointments: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving recent appointments"
            )
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system health and status"""
        try:
            # Check database connectivity and system health
            current_time = datetime.utcnow()
            
            # Basic health checks
            db_status = "healthy"  # Would implement actual DB check
            ai_service_status = "healthy"  # Would implement actual AI service check
            
            # Get system load metrics (placeholder)
            system_metrics = {
                "cpu_usage": "25%",
                "memory_usage": "60%",
                "disk_usage": "45%",
                "uptime_hours": 72
            }
            
            return {
                "status": "operational",
                "services": {
                    "database": db_status,
                    "ai_service": ai_service_status,
                    "api": "healthy"
                },
                "metrics": system_metrics,
                "last_check": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def get_availability_configuration(self) -> Dict[str, Any]:
        """Get current availability configuration"""
        try:
            # Return mock data for now since we don't have professional and service use cases
            availability_config = {
                "professionals": [],
                "services": [],
                "general_settings": {
                    "booking_window_days": 30,
                    "min_advance_hours": 2,
                    "max_daily_appointments": 20
                }
            }
            
            return availability_config
            
        except Exception as e:
            logger.error(f"Error getting availability configuration: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving availability configuration"
            )
    
    async def update_availability_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update availability settings"""
        try:
            # This would implement actual settings update
            # For now, just return success response
            
            updated_settings = {
                "booking_window_days": settings.get("booking_window_days", 30),
                "min_advance_hours": settings.get("min_advance_hours", 2),
                "max_daily_appointments": settings.get("max_daily_appointments", 20),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            return {
                "success": True,
                "settings": updated_settings,
                "message": "Configuración actualizada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error updating availability settings: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating availability settings"
            )
    
    async def get_conversation_insights(self) -> Dict[str, Any]:
        """Get conversation insights for admin"""
        try:
            # Get conversation analytics
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            analytics = await self.conversation_use_cases.get_conversation_analytics(
                start_date, end_date
            )
            
            # Add additional insights
            insights = {
                "total_conversations": analytics.get("total_conversations", 0),
                "by_status": analytics.get("by_status", {}),
                "common_intents": {
                    "AGENDAR_CITA": 45,
                    "CONSULTAR_CITA": 25,
                    "CANCELAR_CITA": 20,
                    "AYUDA": 10
                },
                "avg_conversation_duration": "3.5 min",
                "resolution_rate": "85%",
                "escalation_rate": "15%"
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting conversation insights: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving conversation insights"
            )
    
    # Helper methods
    async def _get_appointment_count_by_period(self, start_date: datetime, end_date: datetime) -> int:
        """Get appointment count for a specific period"""
        # This would be implemented with actual repository call
        # For now, return mock data
        return 150
    
    async def _get_user_count(self) -> int:
        """Get total user count"""
        # This would be implemented with actual repository call
        return 500
    
    async def _get_active_conversation_count(self) -> int:
        """Get active conversation count"""
        # This would be implemented with actual repository call
        return 25
    
    async def _get_appointment_count_by_status(
        self, 
        appointment_status: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> int:
        """Get appointment count by status and period"""
        # This would be implemented with actual repository call
        status_counts = {
            "scheduled": 80,
            "completed": 120,
            "cancelled": 30,
            "no_show": 20
        }
        return status_counts.get(appointment_status, 0)