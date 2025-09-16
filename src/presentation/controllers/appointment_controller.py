from fastapi import HTTPException, status
from typing import Optional
from ...application.use_cases.appointment_use_cases import AppointmentUseCases
from ...application.dto.appointment_dto import (
    AppointmentCreateDTO, AppointmentUpdateDTO, AppointmentRescheduleDTO,
    AppointmentCancelDTO, AppointmentResponseDTO, AppointmentListResponseDTO,
    AppointmentFilterDTO, AvailabilityRequestDTO, AvailabilityResponseDTO
)
import logging

logger = logging.getLogger(__name__)


class AppointmentController:
    """Controller for Appointment-related endpoints"""
    
    def __init__(self, appointment_use_cases: AppointmentUseCases):
        self.appointment_use_cases = appointment_use_cases
    
    async def create_appointment(self, appointment_data: AppointmentCreateDTO) -> AppointmentResponseDTO:
        """Create a new appointment"""
        try:
            return await self.appointment_use_cases.create_appointment(appointment_data)
        except ValueError as e:
            logger.warning(f"Appointment creation validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error creating appointment: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_appointment_by_id(self, appointment_id: str) -> AppointmentResponseDTO:
        """Get appointment by ID"""
        try:
            appointment = await self.appointment_use_cases.get_appointment_by_id(appointment_id)
            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Appointment with ID {appointment_id} not found"
                )
            return appointment
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting appointment {appointment_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_appointments(
        self,
        user_id: Optional[str] = None,
        professional_id: Optional[str] = None,
        service_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        mode: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        upcoming_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> AppointmentListResponseDTO:
        """Get appointments with filters"""
        try:
            if skip < 0 or limit <= 0 or limit > 500:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination parameters"
                )
            
            # Parse date strings to date objects if provided
            from datetime import datetime
            parsed_date_from = None
            parsed_date_to = None
            
            if date_from:
                try:
                    parsed_date_from = datetime.fromisoformat(date_from).date()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid date_from format: {date_from}"
                    )
            
            if date_to:
                try:
                    parsed_date_to = datetime.fromisoformat(date_to).date()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid date_to format: {date_to}"
                    )
            
            # Create filter DTO
            filter_data = AppointmentFilterDTO(
                user_id=user_id,
                professional_id=professional_id,
                service_id=service_id,
                status=status_filter,
                mode=mode,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                upcoming_only=upcoming_only
            )
            
            # logger.info(f"[DEBUG] Controller filters: date_from={parsed_date_from}, date_to={parsed_date_to}, upcoming_only={upcoming_only}")
            
            return await self.appointment_use_cases.get_appointments(filter_data, skip, limit)
        except HTTPException:
            raise
        except ValueError as e:
            logger.warning(f"Appointment filter validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error getting appointments: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def confirm_appointment(self, appointment_id: str) -> AppointmentResponseDTO:
        """Confirm an appointment"""
        try:
            return await self.appointment_use_cases.confirm_appointment(appointment_id)
        except ValueError as e:
            logger.warning(f"Appointment confirmation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error confirming appointment {appointment_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def cancel_appointment(
        self, 
        appointment_id: str, 
        cancel_data: AppointmentCancelDTO
    ) -> AppointmentResponseDTO:
        """Cancel an appointment"""
        try:
            return await self.appointment_use_cases.cancel_appointment(appointment_id, cancel_data)
        except ValueError as e:
            logger.warning(f"Appointment cancellation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error cancelling appointment {appointment_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def reschedule_appointment(
        self, 
        appointment_id: str, 
        reschedule_data: AppointmentRescheduleDTO
    ) -> AppointmentResponseDTO:
        """Reschedule an appointment"""
        try:
            return await self.appointment_use_cases.reschedule_appointment(appointment_id, reschedule_data)
        except ValueError as e:
            logger.warning(f"Appointment reschedule error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error rescheduling appointment {appointment_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def complete_appointment(self, appointment_id: str) -> AppointmentResponseDTO:
        """Mark appointment as completed"""
        try:
            return await self.appointment_use_cases.complete_appointment(appointment_id)
        except ValueError as e:
            logger.warning(f"Appointment completion error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error completing appointment {appointment_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def mark_no_show(self, appointment_id: str) -> AppointmentResponseDTO:
        """Mark appointment as no show"""
        try:
            return await self.appointment_use_cases.mark_no_show(appointment_id)
        except ValueError as e:
            logger.warning(f"Appointment no show error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error marking appointment as no show {appointment_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_available_slots(self, request: AvailabilityRequestDTO) -> AvailabilityResponseDTO:
        """Get available time slots for a service"""
        try:
            return await self.appointment_use_cases.get_available_slots(request)
        except ValueError as e:
            logger.warning(f"Availability request error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error getting available slots: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_user_appointments(
        self, 
        user_id: str, 
        upcoming_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> AppointmentListResponseDTO:
        """Get appointments for a specific user"""
        try:
            if skip < 0 or limit <= 0 or limit > 500:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination parameters"
                )
            
            filter_data = AppointmentFilterDTO(
                user_id=user_id,
                upcoming_only=upcoming_only
            )
            
            return await self.appointment_use_cases.get_appointments(filter_data, skip, limit)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting user appointments {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_professional_appointments(
        self, 
        professional_id: str, 
        upcoming_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> AppointmentListResponseDTO:
        """Get appointments for a specific professional"""
        try:
            if skip < 0 or limit <= 0 or limit > 500:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination parameters"
                )
            
            filter_data = AppointmentFilterDTO(
                professional_id=professional_id,
                upcoming_only=upcoming_only
            )
            
            return await self.appointment_use_cases.get_appointments(filter_data, skip, limit)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting professional appointments {professional_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )