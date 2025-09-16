"""
Link Management Controller
Handles HTTP requests for appointment link management
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ...application.use_cases.link_management_use_cases import LinkManagementUseCases
from ...application.dto.link_management_dto import (
    GenerateLinkDTO, AppointmentLinkResponseDTO, ValidateLinkDTO,
    LinkValidationResponseDTO, RescheduleRequestDTO, CancelRequestDTO,
    LinkActionResponseDTO, BulkLinkGenerationDTO, BulkLinkResponseDTO,
    LinkAnalyticsDTO, LinkDashboardDTO
)
from ...infrastructure.exceptions import EntityNotFound, BusinessLogicError

logger = logging.getLogger(__name__)


class LinkManagementController:
    """Controller for appointment link management operations"""
    
    def __init__(self, link_use_cases: LinkManagementUseCases):
        self._link_use_cases = link_use_cases
    
    async def generate_link(
        self,
        request: GenerateLinkDTO
    ) -> AppointmentLinkResponseDTO:
        """Generate a secure appointment management link"""
        try:
            logger.info(f"Generating {request.action.value} link for appointment {request.appointment_id}")
            
            return await self._link_use_cases.generate_appointment_link(request)
            
        except (EntityNotFound, BusinessLogicError) as e:
            logger.warning(f"Business logic error generating link: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating link: {e}")
            raise BusinessLogicError("Internal error generating appointment link")
    
    async def validate_link(
        self,
        token: str,
        user_agent: str = None,
        ip_address: str = None
    ) -> LinkValidationResponseDTO:
        """Validate a secure appointment link"""
        try:
            logger.info(f"Validating appointment link token")
            
            request = ValidateLinkDTO(
                link_token=token,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            return await self._link_use_cases.validate_link(request)
            
        except Exception as e:
            logger.error(f"Unexpected error validating link: {e}")
            return LinkValidationResponseDTO(
                is_valid=False,
                status="invalid",
                error_message="Internal error validating link"
            )
    
    async def reschedule_appointment(
        self,
        request: RescheduleRequestDTO
    ) -> LinkActionResponseDTO:
        """Reschedule appointment via secure link"""
        try:
            logger.info(f"Processing reschedule request via link")
            
            return await self._link_use_cases.reschedule_via_link(request)
            
        except (EntityNotFound, BusinessLogicError) as e:
            logger.warning(f"Business logic error rescheduling appointment: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error rescheduling appointment: {e}")
            raise BusinessLogicError("Internal error rescheduling appointment")
    
    async def cancel_appointment(
        self,
        request: CancelRequestDTO
    ) -> LinkActionResponseDTO:
        """Cancel appointment via secure link"""
        try:
            logger.info(f"Processing cancellation request via link")
            
            return await self._link_use_cases.cancel_via_link(request)
            
        except (EntityNotFound, BusinessLogicError) as e:
            logger.warning(f"Business logic error cancelling appointment: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error cancelling appointment: {e}")
            raise BusinessLogicError("Internal error cancelling appointment")
    
    async def bulk_generate_links(
        self,
        request: BulkLinkGenerationDTO
    ) -> BulkLinkResponseDTO:
        """Generate multiple appointment links in batch"""
        try:
            logger.info(f"Bulk generating links for {len(request.appointment_ids)} appointments")
            
            return await self._link_use_cases.bulk_generate_links(request)
            
        except BusinessLogicError as e:
            logger.warning(f"Business logic error bulk generating links: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error bulk generating links: {e}")
            raise BusinessLogicError("Internal error generating links")
    
    async def get_link_analytics(
        self,
        days: int = 30
    ) -> LinkAnalyticsDTO:
        """Get comprehensive link usage analytics"""
        try:
            logger.info(f"Getting link analytics for {days} days")
            
            if days < 1 or days > 365:
                raise BusinessLogicError("Days parameter must be between 1 and 365")
            
            return await self._link_use_cases.get_link_analytics(days)
            
        except BusinessLogicError as e:
            logger.warning(f"Business logic error getting analytics: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting link analytics: {e}")
            raise BusinessLogicError("Internal error retrieving analytics")
    
    async def get_dashboard_overview(
        self,
        period_days: int = 30
    ) -> LinkDashboardDTO:
        """Get link management dashboard overview"""
        try:
            logger.info(f"Getting link dashboard overview for {period_days} days")
            
            # Get analytics
            analytics = await self._link_use_cases.get_link_analytics(period_days)
            
            # Calculate derived metrics
            total_actions = analytics.total_links_used
            reschedule_rate = (analytics.action_breakdown.get("reschedule", 0) / total_actions * 100) if total_actions > 0 else 0
            cancel_rate = (analytics.action_breakdown.get("cancel", 0) / total_actions * 100) if total_actions > 0 else 0
            
            # Mock recent activity (in real implementation, get from database)
            recent_activity = [
                {
                    "type": "reschedule",
                    "appointment_id": "apt_001",
                    "user_name": "Juan Pérez",
                    "timestamp": (datetime.utcnow() - datetime.timedelta(minutes=15)).isoformat(),
                    "details": "Reagendado para mañana 10:00 AM"
                },
                {
                    "type": "cancel",
                    "appointment_id": "apt_002", 
                    "user_name": "María García",
                    "timestamp": (datetime.utcnow() - datetime.timedelta(hours=2)).isoformat(),
                    "details": "Cancelado por emergencia personal"
                },
                {
                    "type": "reschedule",
                    "appointment_id": "apt_003",
                    "user_name": "Carlos López",
                    "timestamp": (datetime.utcnow() - datetime.timedelta(hours=4)).isoformat(),
                    "details": "Reagendado para la próxima semana"
                }
            ]
            
            # Mock security alerts
            security_alerts = [
                {
                    "type": "suspicious_access",
                    "message": "Multiple failed validation attempts detected",
                    "timestamp": (datetime.utcnow() - datetime.timedelta(hours=6)).isoformat(),
                    "severity": "medium"
                }
            ]
            
            return LinkDashboardDTO(
                overview={
                    "total_active_links": analytics.total_links_generated - analytics.total_links_expired,
                    "links_used_today": analytics.total_links_used,
                    "usage_rate": analytics.usage_rate,
                    "most_popular_action": max(analytics.action_breakdown.keys(), key=lambda k: analytics.action_breakdown[k]) if analytics.action_breakdown else "none"
                },
                recent_activity=recent_activity,
                performance_metrics={
                    "reschedule_rate": reschedule_rate,
                    "cancel_rate": cancel_rate,
                    "link_success_rate": analytics.usage_rate,
                    "average_response_time_hours": analytics.user_engagement_metrics.get("average_time_to_action_minutes", 0) / 60
                },
                security_alerts=security_alerts,
                system_health={
                    "service_status": "healthy",
                    "database_status": "healthy",
                    "link_generation_status": "operational",
                    "last_cleanup": (datetime.utcnow() - datetime.timedelta(hours=12)).isoformat()
                },
                period_start=datetime.utcnow() - datetime.timedelta(days=period_days),
                period_end=datetime.utcnow()
            )
            
        except BusinessLogicError as e:
            logger.warning(f"Business logic error getting dashboard: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting dashboard overview: {e}")
            raise BusinessLogicError("Internal error retrieving dashboard")
    
    async def cleanup_expired_links(self) -> Dict[str, Any]:
        """Clean up expired and old links"""
        try:
            logger.info("Starting link cleanup process")
            
            result = await self._link_use_cases.cleanup_expired_links()
            
            logger.info(f"Link cleanup completed: {result}")
            return result
            
        except BusinessLogicError as e:
            logger.warning(f"Business logic error during cleanup: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during link cleanup: {e}")
            raise BusinessLogicError("Internal error during cleanup")
    
    async def get_link_security_events(
        self,
        link_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get security events for a specific link"""
        try:
            logger.info(f"Getting security events for link {link_id}")
            
            events = await self._link_use_cases._link_repo.get_security_events(link_id, limit)
            
            return {
                "link_id": link_id,
                "total_events": len(events),
                "events": events,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Unexpected error getting security events: {e}")
            raise BusinessLogicError("Internal error retrieving security events")
    
    async def get_user_links_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get summary of links for a specific user"""
        try:
            logger.info(f"Getting link summary for user {user_id}")
            
            # Get user's active links
            active_links = await self._link_use_cases._link_repo.get_links_by_user(
                user_id, 
                status="active",
                limit=100
            )
            
            # Get user's used links from the period
            end_date = datetime.utcnow()
            start_date = end_date - datetime.timedelta(days=days)
            
            used_links = await self._link_use_cases._link_repo.search_links(
                {
                    "user_id": user_id,
                    "status": "used",
                    "date_range": {"start": start_date, "end": end_date}
                },
                limit=100
            )
            
            # Calculate statistics
            reschedule_count = sum(1 for link in used_links["links"] if link.action.value == "reschedule")
            cancel_count = sum(1 for link in used_links["links"] if link.action.value == "cancel")
            
            return {
                "user_id": user_id,
                "period_days": days,
                "active_links": len(active_links),
                "links_used_in_period": used_links["total_count"],
                "reschedules_in_period": reschedule_count,
                "cancellations_in_period": cancel_count,
                "most_recent_activity": used_links["links"][0].used_at if used_links["links"] else None,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Unexpected error getting user links summary: {e}")
            raise BusinessLogicError("Internal error retrieving user summary")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for link management service"""
        try:
            # Test database connectivity by counting active links
            active_count = await self._link_use_cases._link_repo.get_active_links_count()
            
            return {
                "status": "healthy",
                "service": "link_management",
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "active_links": active_count,
                    "database_connected": True
                },
                "features": [
                    "secure_link_generation",
                    "link_validation",
                    "reschedule_via_link",
                    "cancel_via_link",
                    "bulk_operations",
                    "analytics",
                    "security_logging",
                    "automated_cleanup"
                ]
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "link_management",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }