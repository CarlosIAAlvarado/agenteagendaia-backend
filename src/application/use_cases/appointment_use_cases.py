from typing import List, Optional
from datetime import datetime, date, timedelta
from ...domain.entities.appointment import Appointment, AppointmentStatus
from ...domain.value_objects.time_slot import TimeSlot
from ...domain.repositories.appointment_repository import IAppointmentRepository
from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.service_repository import IServiceRepository
from ...domain.repositories.professional_repository import IProfessionalRepository
from ...domain.services.availability_service import AvailabilityDomainService
from ..dto.appointment_dto import (
    AppointmentCreateDTO, AppointmentUpdateDTO, AppointmentRescheduleDTO, 
    AppointmentCancelDTO, AppointmentResponseDTO, AppointmentListResponseDTO,
    AppointmentFilterDTO, AvailabilityRequestDTO, AvailabilityResponseDTO,
    AvailableSlotDTO, TimeSlotDTO, TimeSlotResponseDTO
)
import logging

logger = logging.getLogger(__name__)


class AppointmentUseCases:
    """Use cases for Appointment entity operations"""
    
    def __init__(
        self,
        appointment_repository: IAppointmentRepository,
        user_repository: IUserRepository,
        service_repository: IServiceRepository,
        professional_repository: IProfessionalRepository,
        availability_service: AvailabilityDomainService
    ):
        self._appointment_repo = appointment_repository
        self._user_repo = user_repository
        self._service_repo = service_repository
        self._professional_repo = professional_repository
        self._availability_service = availability_service
    
    async def create_appointment(self, appointment_data: AppointmentCreateDTO) -> AppointmentResponseDTO:
        """Create a new appointment"""
        try:
            # Validate entities exist
            user = await self._user_repo.get_by_id(appointment_data.user_id)
            if not user or not user.is_active:
                raise ValueError(f"User with ID {appointment_data.user_id} not found or inactive")
            
            service = await self._service_repo.get_by_id(appointment_data.service_id)
            if not service or not service.is_active:
                raise ValueError(f"Service with ID {appointment_data.service_id} not found or inactive")
            
            professional = await self._professional_repo.get_by_id(appointment_data.professional_id)
            if not professional or not professional.is_active:
                raise ValueError(f"Professional with ID {appointment_data.professional_id} not found or inactive")
            
            # Validate professional provides the service
            if appointment_data.service_id not in professional.service_ids:
                raise ValueError(f"Professional {professional.name} does not provide service {service.name}")
            
            # Create time slot
            end_time = appointment_data.start_time + timedelta(minutes=service.duration_minutes)
            time_slot = TimeSlot(appointment_data.start_time, end_time)
            
            # Check availability with detailed error messaging
            is_available = await self._availability_service.is_slot_available(
                appointment_data.professional_id, time_slot
            )
            
            if not is_available:
                # Check specific reasons for unavailability
                appointment_date = time_slot.start_time.date()
                daily_count = await self._appointment_repo.count_by_professional_and_date(
                    appointment_data.professional_id, appointment_date
                )
                
                # Check if it's due to daily limit
                if daily_count >= 8:
                    raise ValueError(
                        f"No se pueden agendar más citas para {professional.name} en {appointment_date.strftime('%Y-%m-%d')}. "
                        f"Límite diario de 8 citas alcanzado ({daily_count}/8). "
                        f"Por favor seleccione otro día o profesional."
                    )
                
                # Check if there's a time conflict
                if await self._appointment_repo.exists_conflict(appointment_data.professional_id, time_slot):
                    raise ValueError(
                        f"Ya existe una cita programada para {professional.name} en el horario {time_slot.start_time.strftime('%H:%M')} - {time_slot.end_time.strftime('%H:%M')}. "
                        f"Por favor seleccione otro horario."
                    )
                
                # Check if it's outside working hours
                weekday_str = time_slot.start_time.strftime('%A').lower()
                from ...domain.entities.professional import WeekDay
                weekday = WeekDay(weekday_str)
                
                if not professional.is_available_on_day(weekday):
                    raise ValueError(
                        f"{professional.name} no trabaja los {weekday.value}s. "
                        f"Por favor seleccione otro día."
                    )
                
                working_hours = professional.get_working_hours_for_day(weekday)
                if working_hours:
                    slot_start_time = time_slot.start_time.time()
                    slot_end_time = time_slot.end_time.time()
                    
                    if not (working_hours.start_time <= slot_start_time and slot_end_time <= working_hours.end_time):
                        raise ValueError(
                            f"El horario solicitado ({slot_start_time.strftime('%H:%M')} - {slot_end_time.strftime('%H:%M')}) "
                            f"está fuera del horario laboral de {professional.name} "
                            f"({working_hours.start_time.strftime('%H:%M')} - {working_hours.end_time.strftime('%H:%M')}). "
                            f"Por favor seleccione un horario dentro del rango disponible."
                        )
                
                # Generic fallback message
                raise ValueError(f"El horario no está disponible para {professional.name}.")
            
            # Convert DTO enum to domain enum
            mode = AppointmentMode(appointment_data.mode.value)
            
            # Create appointment entity
            appointment = Appointment(
                id=None,
                user_id=appointment_data.user_id,
                service_id=appointment_data.service_id,
                professional_id=appointment_data.professional_id,
                time_slot=time_slot,
                mode=mode,
                notes=appointment_data.notes,
                created_at=datetime.utcnow()
            )
            
            # Save to repository
            created_appointment = await self._appointment_repo.create(appointment)
            
            logger.info(f"Created appointment: {created_appointment.id}")
            
            return self._to_response_dto(created_appointment)
            
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            raise
    
    async def get_appointment_by_id(self, appointment_id: str) -> Optional[AppointmentResponseDTO]:
        """Get appointment by ID"""
        try:
            appointment = await self._appointment_repo.get_by_id(appointment_id)
            
            if not appointment:
                return None
            
            return self._to_response_dto(appointment)
            
        except Exception as e:
            logger.error(f"Error getting appointment by ID {appointment_id}: {e}")
            raise
    
    async def get_appointments(
        self, 
        filter_data: AppointmentFilterDTO, 
        skip: int = 0, 
        limit: int = 100
    ) -> AppointmentListResponseDTO:
        """Get appointments with filters"""
        try:
            # Debug logs temporarily disabled to avoid Unicode issues
            # logger.info(f"[CRITICAL] get_appointments method called! skip={skip}, limit={limit}")
            # logger.info(f"[CRITICAL] filter_data.user_id={filter_data.user_id}, filter_data.upcoming_only={filter_data.upcoming_only}")
            appointments = []
            total = 0
            
            if filter_data.user_id:
                appointments = await self._appointment_repo.get_by_user_id(filter_data.user_id, skip, limit)
                total = await self._appointment_repo.count_by_user(filter_data.user_id)
            elif filter_data.professional_id:
                appointments = await self._appointment_repo.get_by_professional_id(filter_data.professional_id, skip, limit)
                total = await self._appointment_repo.count_by_professional(filter_data.professional_id)
            elif filter_data.service_id:
                appointments = await self._appointment_repo.get_by_service_id(filter_data.service_id, skip, limit)
                # Get total count for service
                total = await self._appointment_repo.count_by_service(filter_data.service_id)
            elif filter_data.status:
                status = AppointmentStatus(filter_data.status.value)
                appointments = await self._appointment_repo.get_by_status(status, skip, limit)
                total = await self._appointment_repo.count_by_status(status)
            elif filter_data.date_from and filter_data.date_to:
                start_datetime = datetime.combine(filter_data.date_from, datetime.min.time())
                end_datetime = datetime.combine(filter_data.date_to, datetime.max.time())
                # logger.info(f"[DEBUG] Use case date range: {start_datetime} to {end_datetime}")
                # Get total count first
                total = await self._appointment_repo.count_by_date_range(start_datetime, end_datetime)
                # Then get paginated results
                appointments = await self._appointment_repo.get_by_date_range_paginated(start_datetime, end_datetime, skip, limit)
                # logger.info(f"[DEBUG] Repository returned {len(appointments)} appointments")
            else:
                appointments = await self._appointment_repo.get_all(skip, limit)
                total = await self._appointment_repo.count_total()
                # logger.info(f"[DEBUG] Retrieved {len(appointments)} appointments from repository")
                # logger.info(f"[DEBUG] Total count from database: {total}")
            
            # Filter upcoming appointments if requested
            if filter_data.upcoming_only:
                now = datetime.utcnow()
                appointments = [apt for apt in appointments if self._is_appointment_upcoming(apt, now)]
                # logger.info(f"[DEBUG] After upcoming filter: {len(appointments)} appointments")
            
            # logger.info(f"[DEBUG] Converting {len(appointments)} appointments to DTOs")
            appointment_dtos = [self._to_response_dto(apt) for apt in appointments]
            # logger.info(f"[DEBUG] Created {len(appointment_dtos)} DTOs")
            
            return AppointmentListResponseDTO(
                appointments=appointment_dtos,
                total=total,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error getting appointments with filters: {e}")
            raise
    
    async def confirm_appointment(self, appointment_id: str) -> AppointmentResponseDTO:
        """Confirm an appointment"""
        try:
            appointment = await self._appointment_repo.get_by_id(appointment_id)
            if not appointment:
                raise ValueError(f"Appointment with ID {appointment_id} not found")
            
            appointment.confirm()
            updated_appointment = await self._appointment_repo.update(appointment)
            
            logger.info(f"Confirmed appointment: {appointment_id}")
            
            return self._to_response_dto(updated_appointment)
            
        except Exception as e:
            logger.error(f"Error confirming appointment {appointment_id}: {e}")
            raise
    
    async def cancel_appointment(self, appointment_id: str, cancel_data: AppointmentCancelDTO) -> AppointmentResponseDTO:
        """Cancel an appointment"""
        try:
            appointment = await self._appointment_repo.get_by_id(appointment_id)
            if not appointment:
                raise ValueError(f"Appointment with ID {appointment_id} not found")
            
            appointment.cancel(cancel_data.reason)
            updated_appointment = await self._appointment_repo.update(appointment)
            
            logger.info(f"Cancelled appointment: {appointment_id}")
            
            return self._to_response_dto(updated_appointment)
            
        except Exception as e:
            logger.error(f"Error cancelling appointment {appointment_id}: {e}")
            raise
    
    async def reschedule_appointment(
        self, 
        appointment_id: str, 
        reschedule_data: AppointmentRescheduleDTO
    ) -> AppointmentResponseDTO:
        """Reschedule an appointment"""
        try:
            appointment = await self._appointment_repo.get_by_id(appointment_id)
            if not appointment:
                raise ValueError(f"Appointment with ID {appointment_id} not found")
            
            # Get service to calculate duration
            service = await self._service_repo.get_by_id(appointment.service_id)
            if not service:
                raise ValueError(f"Service with ID {appointment.service_id} not found")
            
            # Determine professional ID
            new_professional_id = reschedule_data.professional_id or appointment.professional_id
            
            # Validate new professional if changed
            if new_professional_id != appointment.professional_id:
                professional = await self._professional_repo.get_by_id(new_professional_id)
                if not professional or not professional.is_active:
                    raise ValueError(f"Professional with ID {new_professional_id} not found or inactive")
                
                if appointment.service_id not in professional.service_ids:
                    raise ValueError(f"New professional does not provide the required service")
            
            # Create new time slot
            end_time = reschedule_data.start_time + timedelta(minutes=service.duration_minutes)
            new_time_slot = TimeSlot(reschedule_data.start_time, end_time)
            
            # Check availability with detailed error messaging
            is_available = await self._availability_service.is_slot_available(
                new_professional_id, new_time_slot, appointment_id
            )
            
            if not is_available:
                # Get professional for error messages
                professional = await self._professional_repo.get_by_id(new_professional_id)
                if professional:
                    professional_name = professional.name
                else:
                    professional_name = "el profesional"
                
                # Check specific reasons for unavailability
                appointment_date = new_time_slot.start_time.date()
                daily_count = await self._appointment_repo.count_by_professional_and_date(
                    new_professional_id, appointment_date
                )
                
                # For rescheduling, we need to exclude the current appointment when checking limits
                # The availability service already handles this, but for error messages we need to be accurate
                if daily_count >= 8:
                    # Check if current appointment is on same date with same professional
                    current_date = appointment.time_slot.start_time.date()
                    is_same_professional = new_professional_id == appointment.professional_id
                    is_same_date = appointment_date == current_date
                    
                    # If it's the same professional and same date, the current appointment shouldn't count against limit
                    effective_count = daily_count - 1 if (is_same_professional and is_same_date) else daily_count
                    
                    if effective_count >= 8:
                        raise ValueError(
                            f"No se puede reagendar para {professional_name} en {appointment_date.strftime('%Y-%m-%d')}. "
                            f"Límite diario de 8 citas alcanzado ({effective_count}/8). "
                            f"Por favor seleccione otro día o profesional."
                        )
                
                # Check if there's a time conflict
                if await self._appointment_repo.exists_conflict(new_professional_id, new_time_slot, appointment_id):
                    raise ValueError(
                        f"Ya existe una cita programada para {professional_name} en el horario {new_time_slot.start_time.strftime('%H:%M')} - {new_time_slot.end_time.strftime('%H:%M')}. "
                        f"Por favor seleccione otro horario."
                    )
                
                # Check working hours if professional object is available
                if professional:
                    weekday_str = new_time_slot.start_time.strftime('%A').lower()
                    from ...domain.entities.professional import WeekDay
                    weekday = WeekDay(weekday_str)
                    
                    if not professional.is_available_on_day(weekday):
                        raise ValueError(
                            f"{professional.name} no trabaja los {weekday.value}s. "
                            f"Por favor seleccione otro día."
                        )
                    
                    working_hours = professional.get_working_hours_for_day(weekday)
                    if working_hours:
                        slot_start_time = new_time_slot.start_time.time()
                        slot_end_time = new_time_slot.end_time.time()
                        
                        if not (working_hours.start_time <= slot_start_time and slot_end_time <= working_hours.end_time):
                            raise ValueError(
                                f"El horario solicitado ({slot_start_time.strftime('%H:%M')} - {slot_end_time.strftime('%H:%M')}) "
                                f"está fuera del horario laboral de {professional.name} "
                                f"({working_hours.start_time.strftime('%H:%M')} - {working_hours.end_time.strftime('%H:%M')}). "
                                f"Por favor seleccione un horario dentro del rango disponible."
                            )
                
                # Generic fallback message
                raise ValueError(f"El nuevo horario no está disponible para {professional_name}.")
            
            # Reschedule appointment
            appointment.reschedule(new_time_slot, new_professional_id if new_professional_id != appointment.professional_id else None)
            updated_appointment = await self._appointment_repo.update(appointment)
            
            logger.info(f"Rescheduled appointment: {appointment_id}")
            
            return self._to_response_dto(updated_appointment)
            
        except Exception as e:
            logger.error(f"Error rescheduling appointment {appointment_id}: {e}")
            raise
    
    async def complete_appointment(self, appointment_id: str) -> AppointmentResponseDTO:
        """Mark appointment as completed"""
        try:
            appointment = await self._appointment_repo.get_by_id(appointment_id)
            if not appointment:
                raise ValueError(f"Appointment with ID {appointment_id} not found")
            
            appointment.complete()
            updated_appointment = await self._appointment_repo.update(appointment)
            
            logger.info(f"Completed appointment: {appointment_id}")
            
            return self._to_response_dto(updated_appointment)
            
        except Exception as e:
            logger.error(f"Error completing appointment {appointment_id}: {e}")
            raise
    
    async def mark_no_show(self, appointment_id: str) -> AppointmentResponseDTO:
        """Mark appointment as no show"""
        try:
            appointment = await self._appointment_repo.get_by_id(appointment_id)
            if not appointment:
                raise ValueError(f"Appointment with ID {appointment_id} not found")
            
            appointment.mark_no_show()
            updated_appointment = await self._appointment_repo.update(appointment)
            
            logger.info(f"Marked appointment as no show: {appointment_id}")
            
            return self._to_response_dto(updated_appointment)
            
        except Exception as e:
            logger.error(f"Error marking appointment as no show {appointment_id}: {e}")
            raise
    
    async def get_available_slots(self, request: AvailabilityRequestDTO) -> AvailabilityResponseDTO:
        """Get available time slots for a service"""
        try:
            # Validate service exists
            service = await self._service_repo.get_by_id(request.service_id)
            if not service or not service.is_active:
                raise ValueError(f"Service with ID {request.service_id} not found or inactive")
            
            start_date = request.preferred_date or date.today()
            max_days_ahead = request.max_days_ahead or 30
            max_slots = request.max_slots or 10
            
            available_slots = []
            
            if request.preferred_professional_id:
                # Get slots for specific professional
                professional = await self._professional_repo.get_by_id(request.preferred_professional_id)
                if not professional or not professional.is_active:
                    raise ValueError(f"Professional with ID {request.preferred_professional_id} not found or inactive")
                
                if request.service_id not in professional.service_ids:
                    raise ValueError(f"Professional does not provide the requested service")
                
                slots = await self._availability_service.find_next_available_slots(
                    request.preferred_professional_id,
                    service.duration_minutes,
                    start_date,
                    max_days_ahead,
                    max_slots
                )
                
                for slot in slots:
                    available_slots.append(AvailableSlotDTO(
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        professional_id=professional.id,
                        professional_name=professional.name
                    ))
            else:
                # Get slots for all professionals who provide the service
                professionals = await self._professional_repo.get_by_service_id(request.service_id)
                
                for professional in professionals:
                    if not professional.is_active:
                        continue
                    
                    slots = await self._availability_service.find_next_available_slots(
                        professional.id,
                        service.duration_minutes,
                        start_date,
                        max_days_ahead,
                        max_slots // len(professionals) + 1
                    )
                    
                    for slot in slots:
                        available_slots.append(AvailableSlotDTO(
                            start_time=slot.start_time,
                            end_time=slot.end_time,
                            professional_id=professional.id,
                            professional_name=professional.name
                        ))
                
                # Sort by start time and limit results
                available_slots.sort(key=lambda x: x.start_time)
                available_slots = available_slots[:max_slots]
            
            return AvailabilityResponseDTO(
                available_slots=available_slots,
                requested_date=start_date,
                service_id=request.service_id
            )
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            raise
    
    def _to_response_dto(self, appointment: Appointment) -> AppointmentResponseDTO:
        """Convert Appointment entity to response DTO"""
        # DEBUG: Log para verificar datos
        # Debug logs temporarily disabled to avoid Unicode issues
        # print(f"[PRINT DEBUG] Appointment data - ID: {appointment.id}")
        # print(f"[PRINT DEBUG] service_name: {appointment.service_name}")
        # print(f"[PRINT DEBUG] professional_name: {appointment.professional_name}")
        # logger.info(f"[DEBUG] Appointment data - ID: {appointment.id}")
        # logger.info(f"[DEBUG] service_name: {appointment.service_name}")
        # logger.info(f"[DEBUG] professional_name: {appointment.professional_name}")
        
        return AppointmentResponseDTO(
            id=appointment.id,
            user_id=appointment.user_id,
            service_id=appointment.service_id,
            professional_id=appointment.professional_id,
            time_slot=self._get_time_slot_dto(appointment),
            mode=appointment.mode.value if appointment.mode else None,
            status=appointment.status.value,
            notes=appointment.notes,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
            confirmed_at=appointment.confirmed_at,
            cancelled_at=appointment.cancelled_at,
            # Service information (denormalized)
            service_name=appointment.service_name,
            professional_name=appointment.professional_name,
            duration_minutes=appointment.duration_minutes,
            price=appointment.price
        )
    
    def _is_appointment_upcoming(self, appointment: Appointment, now: datetime) -> bool:
        """Check if an appointment is upcoming based on either time_slot or appointment_date"""
        if appointment.time_slot and appointment.time_slot.start_time:
            return appointment.time_slot.start_time > now
        elif appointment.appointment_date:
            return appointment.appointment_date > now
        else:
            # If neither is available, consider it not upcoming
            return False
    
    def _get_time_slot_dto(self, appointment: Appointment) -> TimeSlotResponseDTO:
        """Get TimeSlotResponseDTO from appointment, handling both time_slot and appointment_date formats"""
        if appointment.time_slot and appointment.time_slot.start_time and appointment.time_slot.end_time:
            return TimeSlotResponseDTO(
                start_time=appointment.time_slot.start_time,
                end_time=appointment.time_slot.end_time
            )
        elif appointment.appointment_date and appointment.duration_minutes:
            # Create TimeSlot from appointment_date and duration
            end_time = appointment.appointment_date + timedelta(minutes=appointment.duration_minutes)
            return TimeSlotResponseDTO(
                start_time=appointment.appointment_date,
                end_time=end_time
            )
        elif appointment.appointment_date:
            # If no duration, assume 1 hour default
            end_time = appointment.appointment_date + timedelta(hours=1)
            return TimeSlotResponseDTO(
                start_time=appointment.appointment_date,
                end_time=end_time
            )
        else:
            # Return a placeholder TimeSlot if no valid time data is available
            now = datetime.utcnow()
            return TimeSlotResponseDTO(
                start_time=now,
                end_time=now + timedelta(hours=1)
            )