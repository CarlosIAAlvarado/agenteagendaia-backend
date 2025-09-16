"""
Link Management Use Cases
Business logic for appointment link management system
"""

import logging
import secrets
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from ...domain.entities.appointment_link import AppointmentLink, LinkAction, LinkStatus
from ...domain.repositories.appointment_link_repository import AppointmentLinkRepository
from ...domain.repositories.appointment_repository import IAppointmentRepository as AppointmentRepository
from ...domain.repositories.user_repository import IUserRepository as UserRepository
from ..dto.link_management_dto import (
    GenerateLinkDTO, AppointmentLinkResponseDTO, ValidateLinkDTO,
    LinkValidationResponseDTO, RescheduleRequestDTO, CancelRequestDTO,
    LinkActionResponseDTO, BulkLinkGenerationDTO, BulkLinkResponseDTO,
    LinkAnalyticsDTO, LinkSecurityLogDTO
)
from ...infrastructure.exceptions import EntityNotFound, BusinessLogicError
from ...infrastructure.config.link_config import link_config

logger = logging.getLogger(__name__)


class LinkManagementUseCases:
    """Use cases for appointment link management"""
    
    def __init__(
        self,
        link_repository: AppointmentLinkRepository,
        appointment_repository: AppointmentRepository,
        user_repository: UserRepository
    ):
        self._link_repo = link_repository
        self._appointment_repo = appointment_repository
        self._user_repo = user_repository
        self._base_url = link_config.BASE_URL
    
    async def generate_appointment_link(
        self,
        request: GenerateLinkDTO
    ) -> AppointmentLinkResponseDTO:
        """Generate a secure link for appointment management"""
        try:
            # Verify appointment exists
            appointment = await self._appointment_repo.get_appointment_by_id(request.appointment_id)
            if not appointment:
                raise EntityNotFound(f"Appointment {request.appointment_id} not found")
            
            # Verify user owns the appointment
            if appointment.user_id != request.user_id:
                raise BusinessLogicError("User does not have permission for this appointment")
            
            # Check if appointment is in a valid state for this action
            if not self._can_perform_action(appointment, request.action):
                raise BusinessLogicError(f"Cannot {request.action.value} appointment in current state")
            
            # Check for existing active links of the same type
            existing_links = await self._link_repo.get_links_by_appointment(
                request.appointment_id,
                action=request.action,
                status=LinkStatus.ACTIVE
            )
            
            # Revoke existing active links of the same type
            for existing_link in existing_links:
                existing_link.revoke()
                await self._link_repo.update_link(existing_link)
            
            # Create new link
            if request.action == LinkAction.RESCHEDULE:
                link = AppointmentLink.create_reschedule_link(
                    request.appointment_id,
                    request.user_id,
                    request.expires_in_hours,
                    request.custom_message
                )
            elif request.action == LinkAction.CANCEL:
                link = AppointmentLink.create_cancel_link(
                    request.appointment_id,
                    request.user_id,
                    request.expires_in_hours,
                    request.custom_message
                )
            else:  # CONFIRM
                link = AppointmentLink.create_confirm_link(
                    request.appointment_id,
                    request.user_id,
                    request.expires_in_hours,
                    request.custom_message
                )
            
            # Add metadata
            link.add_metadata("appointment_date", appointment.appointment_date.isoformat())
            link.add_metadata("service_name", appointment.service_name)
            link.add_metadata("professional_name", appointment.professional_name)
            
            # Save to repository
            created_link = await self._link_repo.create_link(link)
            
            # Log security event
            await self._link_repo.log_security_event(
                link.link_id,
                "created",
                {
                    "action": request.action.value,
                    "appointment_id": request.appointment_id,
                    "user_id": request.user_id
                }
            )
            
            # Return response DTO
            return AppointmentLinkResponseDTO(
                link_id=created_link.link_id,
                appointment_id=created_link.appointment_id,
                action=created_link.action,
                secure_url=created_link.get_full_url(self._base_url),
                expires_at=created_link.expires_at,
                status=created_link.status,
                created_at=created_link.created_at
            )
            
        except (EntityNotFound, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Error generating appointment link: {e}")
            raise BusinessLogicError(f"Failed to generate appointment link: {e}")
    
    async def validate_link(
        self,
        request: ValidateLinkDTO
    ) -> LinkValidationResponseDTO:
        """Validate a secure link and return appointment details"""
        try:
            # Get link by token
            link = await self._link_repo.get_link_by_token(request.link_token)
            
            if not link:
                return LinkValidationResponseDTO(
                    is_valid=False,
                    status=LinkStatus.INVALID,
                    error_message="Link not found or invalid token"
                )
            
            # Log access attempt
            await self._link_repo.log_security_event(
                link.link_id,
                "accessed",
                {
                    "user_agent": request.user_agent,
                    "ip_address": request.ip_address,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Check if link is valid
            if not link.is_valid():
                status = LinkStatus.EXPIRED if link.is_expired() else LinkStatus.USED
                return LinkValidationResponseDTO(
                    is_valid=False,
                    link_id=link.link_id,
                    appointment_id=link.appointment_id,
                    action=link.action,
                    status=status,
                    expires_at=link.expires_at,
                    error_message=f"Link is {status.value}"
                )
            
            # Get appointment details
            appointment = await self._appointment_repo.get_appointment_by_id(link.appointment_id)
            if not appointment:
                return LinkValidationResponseDTO(
                    is_valid=False,
                    status=LinkStatus.INVALID,
                    error_message="Associated appointment not found"
                )
            
            # Get user details
            user = await self._user_repo.get_user_by_id(link.user_id)
            user_details = {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone
            } if user else None
            
            # Return successful validation
            return LinkValidationResponseDTO(
                is_valid=True,
                link_id=link.link_id,
                appointment_id=link.appointment_id,
                action=link.action,
                status=link.status,
                appointment_details={
                    "appointment_id": appointment.appointment_id,
                    "service_name": appointment.service_name,
                    "appointment_date": appointment.appointment_date.isoformat(),
                    "time_slot": appointment.time_slot,
                    "professional_name": appointment.professional_name,
                    "status": appointment.status.value,
                    "duration_minutes": appointment.duration_minutes
                },
                user_details=user_details,
                expires_at=link.expires_at
            )
            
        except Exception as e:
            logger.error(f"Error validating link: {e}")
            return LinkValidationResponseDTO(
                is_valid=False,
                status=LinkStatus.INVALID,
                error_message="Internal error validating link"
            )
    
    async def reschedule_via_link(
        self,
        request: RescheduleRequestDTO
    ) -> LinkActionResponseDTO:
        """Reschedule appointment via secure link"""
        try:
            # Validate link first
            validation = await self.validate_link(ValidateLinkDTO(link_token=request.link_token))
            
            if not validation.is_valid or validation.action != LinkAction.RESCHEDULE:
                raise BusinessLogicError("Invalid or unauthorized link for rescheduling")
            
            # Get the link and mark it as used
            link = await self._link_repo.get_link_by_token(request.link_token)
            if not link or not link.use_link():
                raise BusinessLogicError("Link cannot be used")
            
            # Get original appointment
            original_appointment = await self._appointment_repo.get_appointment_by_id(link.appointment_id)
            if not original_appointment:
                raise EntityNotFound("Original appointment not found")
            
            # Check if requested time slot is available
            if request.preferred_professional_id:
                # Check with specific professional
                is_available = await self._appointment_repo.check_availability(
                    request.preferred_professional_id,
                    request.new_date,
                    request.new_time_slot
                )
            else:
                # Use same professional as original appointment
                is_available = await self._appointment_repo.check_availability(
                    original_appointment.professional_id,
                    request.new_date,
                    request.new_time_slot
                )
            
            if not is_available:
                raise BusinessLogicError("Requested time slot is not available")
            
            # Create new appointment
            new_appointment_data = {
                "user_id": original_appointment.user_id,
                "service_name": original_appointment.service_name,
                "appointment_date": request.new_date,
                "time_slot": request.new_time_slot,
                "professional_id": request.preferred_professional_id or original_appointment.professional_id,
                "duration_minutes": original_appointment.duration_minutes,
                "notes": f"Rescheduled from {original_appointment.appointment_date.date()}. Reason: {request.reason or 'User requested'}"
            }
            
            new_appointment = await self._appointment_repo.create_appointment(new_appointment_data)
            
            # Cancel original appointment
            await self._appointment_repo.cancel_appointment(
                original_appointment.appointment_id,
                f"Rescheduled to {request.new_date.date()}"
            )
            
            # Update link
            link.add_metadata("new_appointment_id", new_appointment.appointment_id)
            link.add_metadata("reschedule_reason", request.reason)
            link.add_metadata("reschedule_date", request.new_date.isoformat())
            await self._link_repo.update_link(link)
            
            # Log security event
            await self._link_repo.log_security_event(
                link.link_id,
                "used",
                {
                    "action": "reschedule",
                    "original_appointment_id": original_appointment.appointment_id,
                    "new_appointment_id": new_appointment.appointment_id,
                    "reason": request.reason
                }
            )
            
            return LinkActionResponseDTO(
                success=True,
                message="Cita reagendada exitosamente",
                appointment_id=original_appointment.appointment_id,
                action=LinkAction.RESCHEDULE,
                new_appointment_id=new_appointment.appointment_id,
                new_appointment_details={
                    "appointment_date": new_appointment.appointment_date.isoformat(),
                    "time_slot": new_appointment.time_slot,
                    "professional_name": new_appointment.professional_name,
                    "service_name": new_appointment.service_name
                },
                confirmation_code=new_appointment.confirmation_code,
                follow_up_required=True,
                next_steps=[
                    "Recibirás un email de confirmación",
                    "El profesional será notificado del cambio",
                    "Puedes cancelar o reagendar nuevamente si es necesario"
                ]
            )
            
        except (EntityNotFound, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Error rescheduling via link: {e}")
            raise BusinessLogicError(f"Failed to reschedule appointment: {e}")
    
    async def cancel_via_link(
        self,
        request: CancelRequestDTO
    ) -> LinkActionResponseDTO:
        """Cancel appointment via secure link"""
        try:
            # Validate link first
            validation = await self.validate_link(ValidateLinkDTO(link_token=request.link_token))
            
            if not validation.is_valid or validation.action != LinkAction.CANCEL:
                raise BusinessLogicError("Invalid or unauthorized link for cancellation")
            
            # Get the link and mark it as used
            link = await self._link_repo.get_link_by_token(request.link_token)
            if not link or not link.use_link():
                raise BusinessLogicError("Link cannot be used")
            
            # Get appointment
            appointment = await self._appointment_repo.get_appointment_by_id(link.appointment_id)
            if not appointment:
                raise EntityNotFound("Appointment not found")
            
            # Cancel appointment
            cancellation_reason = request.reason or "Cancelled by user via link"
            await self._appointment_repo.cancel_appointment(
                appointment.appointment_id,
                cancellation_reason
            )
            
            # Update link with feedback
            if request.feedback_rating or request.feedback_comment:
                link.add_metadata("feedback_rating", request.feedback_rating)
                link.add_metadata("feedback_comment", request.feedback_comment)
            
            link.add_metadata("cancellation_reason", request.reason)
            link.add_metadata("cancelled_at", datetime.utcnow().isoformat())
            await self._link_repo.update_link(link)
            
            # Log security event
            await self._link_repo.log_security_event(
                link.link_id,
                "used",
                {
                    "action": "cancel",
                    "appointment_id": appointment.appointment_id,
                    "reason": request.reason,
                    "feedback_rating": request.feedback_rating
                }
            )
            
            return LinkActionResponseDTO(
                success=True,
                message="Cita cancelada exitosamente",
                appointment_id=appointment.appointment_id,
                action=LinkAction.CANCEL,
                follow_up_required=request.feedback_rating is not None and request.feedback_rating <= 3,
                next_steps=[
                    "Recibirás un email de confirmación de cancelación",
                    "El profesional será notificado",
                    "Puedes agendar una nueva cita cuando gustes"
                ]
            )
            
        except (EntityNotFound, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Error cancelling via link: {e}")
            raise BusinessLogicError(f"Failed to cancel appointment: {e}")
    
    async def bulk_generate_links(
        self,
        request: BulkLinkGenerationDTO
    ) -> BulkLinkResponseDTO:
        """Generate multiple appointment links in batch"""
        try:
            start_time = datetime.utcnow()
            
            links_to_create = []
            errors = []
            
            for appointment_id in request.appointment_ids:
                try:
                    # Verify appointment exists
                    appointment = await self._appointment_repo.get_appointment_by_id(appointment_id)
                    if not appointment:
                        errors.append({
                            "appointment_id": appointment_id,
                            "error": "Appointment not found"
                        })
                        continue
                    
                    # Create links for each requested action
                    for action in request.actions:
                        if not self._can_perform_action(appointment, action):
                            errors.append({
                                "appointment_id": appointment_id,
                                "action": action.value,
                                "error": f"Cannot {action.value} appointment in current state"
                            })
                            continue
                        
                        # Create link
                        if action == LinkAction.RESCHEDULE:
                            link = AppointmentLink.create_reschedule_link(
                                appointment_id,
                                appointment.user_id,
                                request.expires_in_hours
                            )
                        elif action == LinkAction.CANCEL:
                            link = AppointmentLink.create_cancel_link(
                                appointment_id,
                                appointment.user_id,
                                request.expires_in_hours
                            )
                        else:  # CONFIRM
                            link = AppointmentLink.create_confirm_link(
                                appointment_id,
                                appointment.user_id,
                                request.expires_in_hours
                            )
                        
                        links_to_create.append(link)
                        
                except Exception as e:
                    errors.append({
                        "appointment_id": appointment_id,
                        "error": str(e)
                    })
            
            # Bulk create valid links
            created_links = []
            if links_to_create:
                created_links = await self._link_repo.bulk_create_links(links_to_create)
            
            # Convert to response DTOs
            response_links = []
            for link in created_links:
                response_links.append(AppointmentLinkResponseDTO(
                    link_id=link.link_id,
                    appointment_id=link.appointment_id,
                    action=link.action,
                    secure_url=link.get_full_url(self._base_url),
                    expires_at=link.expires_at,
                    status=link.status,
                    created_at=link.created_at
                ))
            
            end_time = datetime.utcnow()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            return BulkLinkResponseDTO(
                total_processed=len(request.appointment_ids),
                successful_links=len(created_links),
                failed_links=len(errors),
                links=response_links,
                errors=errors,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error bulk generating links: {e}")
            raise BusinessLogicError(f"Failed to bulk generate links: {e}")
    
    async def get_link_analytics(self, days: int = 30) -> LinkAnalyticsDTO:
        """Get comprehensive link analytics"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get usage statistics
            usage_stats = await self._link_repo.get_usage_statistics(days)
            
            # Get analytics by date range
            analytics = await self._link_repo.get_link_analytics(start_date, end_date)
            
            # Mock some additional data (in real implementation, get from database)
            popular_time_slots = [
                {"time_slot": "10:00", "reschedule_count": 25},
                {"time_slot": "14:00", "reschedule_count": 22},
                {"time_slot": "16:00", "reschedule_count": 18}
            ]
            
            cancellation_reasons = {
                "Personal emergency": 15,
                "Schedule conflict": 12,
                "Feeling unwell": 8,
                "No longer needed": 5,
                "Other": 10
            }
            
            reschedule_patterns = {
                "Same week": 35,
                "Next week": 25,
                "Same month": 20,
                "Next month": 15,
                "Further out": 5
            }
            
            user_engagement_metrics = {
                "average_time_to_action_minutes": 24,
                "most_active_hour": 14,
                "mobile_vs_desktop": {"mobile": 65, "desktop": 35},
                "repeat_users": 25
            }
            
            return LinkAnalyticsDTO(
                total_links_generated=usage_stats["total_links_created"],
                total_links_used=usage_stats["total_links_used"],
                total_links_expired=usage_stats["total_links_expired"],
                usage_rate=usage_stats["usage_rate"],
                action_breakdown=analytics["by_action"],
                popular_time_slots=popular_time_slots,
                cancellation_reasons=cancellation_reasons,
                reschedule_patterns=reschedule_patterns,
                user_engagement_metrics=user_engagement_metrics,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting link analytics: {e}")
            raise BusinessLogicError(f"Failed to get link analytics: {e}")
    
    async def cleanup_expired_links(self) -> Dict[str, Any]:
        """Clean up expired links and return summary"""
        try:
            # Mark expired links
            expired_count = await self._link_repo.expire_old_links()
            
            # Get expired links for deletion (keep for 30 days after expiration)
            cleanup_date = datetime.utcnow() - timedelta(days=30)
            expired_links = await self._link_repo.get_expired_links(limit=1000)
            
            # Delete very old expired links
            old_links_deleted = 0
            for link in expired_links:
                if link.expires_at < cleanup_date:
                    await self._link_repo.delete_link(link.link_id)
                    old_links_deleted += 1
            
            return {
                "expired_links_marked": expired_count,
                "old_links_deleted": old_links_deleted,
                "cleanup_date": cleanup_date.isoformat(),
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up expired links: {e}")
            raise BusinessLogicError(f"Failed to cleanup expired links: {e}")
    
    def _can_perform_action(self, appointment, action: LinkAction) -> bool:
        """Check if an action can be performed on an appointment"""
        from ...domain.entities.appointment import AppointmentStatus
        
        # Cannot reschedule or cancel completed, cancelled, or no-show appointments
        if appointment.status in [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW
        ]:
            return False
        
        # Cannot reschedule or cancel appointments that are too close
        if action in [LinkAction.RESCHEDULE, LinkAction.CANCEL]:
            time_until_appointment = appointment.appointment_date - datetime.utcnow()
            min_hours = link_config.MIN_HOURS_BEFORE_APPOINTMENT
            if time_until_appointment.total_seconds() < (min_hours * 3600):
                return False
        
        return True