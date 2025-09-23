import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
import re

from ...entities.appointment import Appointment, AppointmentStatus
from ...repositories.appointment_repository import IAppointmentRepository
from ...repositories.professional_repository import IProfessionalRepository
from ...repositories.service_repository import IServiceRepository

logger = logging.getLogger(__name__)


class AppointmentRescheduleTool:
    """AI Tool for rescheduling appointments interactively"""

    def __init__(
        self,
        appointment_repository: IAppointmentRepository,
        professional_repository: IProfessionalRepository,
        service_repository: IServiceRepository,
        email_tool=None
    ):
        self.appointment_repo = appointment_repository
        self.professional_repo = professional_repository
        self.service_repo = service_repository
        self.email_tool = email_tool

    async def start_reschedule_process(
        self,
        appointment_id: str,
        user_id: str = None,
        user_message: str = ""
    ) -> Dict[str, Any]:
        """
        Inicia el proceso de reagendamiento interactivo
        Muestra la cita actual y opciones disponibles
        """
        try:
            logger.info(f"🔄 [RESCHEDULE] Starting reschedule process for appointment {appointment_id}")

            # Buscar la cita
            appointment = await self.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                logger.error(f"❌ [RESCHEDULE] Appointment {appointment_id} not found")
                return {
                    "success": False,
                    "error": "appointment_not_found",
                    "message": "No se encontró la cita especificada",
                    "user_notification": f"No pude encontrar la cita con ID {appointment_id}. Verifica que el ID sea correcto."
                }

            # Validar que la cita pertenece al usuario (si se proporciona user_id)
            if user_id and appointment.user_id != user_id:
                logger.error(f"❌ [RESCHEDULE] Appointment {appointment_id} does not belong to user {user_id}")
                return {
                    "success": False,
                    "error": "unauthorized_access",
                    "message": "La cita no pertenece al usuario",
                    "user_notification": "No tienes permisos para reagendar esta cita."
                }

            # Validar que la cita se puede reagendar
            if appointment.status in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]:
                logger.error(f"❌ [RESCHEDULE] Cannot reschedule appointment with status {appointment.status}")
                return {
                    "success": False,
                    "error": "invalid_status",
                    "message": f"No se puede reagendar una cita {appointment.status.value}",
                    "user_notification": f"No puedes reagendar una cita que está {appointment.status.value}."
                }

            # Validar que la cita no es en el pasado
            if appointment.appointment_date and appointment.appointment_date < datetime.utcnow():
                logger.error(f"❌ [RESCHEDULE] Cannot reschedule past appointment")
                return {
                    "success": False,
                    "error": "past_appointment",
                    "message": "No se puede reagendar una cita del pasado",
                    "user_notification": "No puedes reagendar una cita que ya pasó."
                }

            # Obtener datos completos del servicio y profesional
            service_name = appointment.service_name
            professional_name = appointment.professional_name

            if not service_name and appointment.service_id:
                service = await self.service_repo.get_by_id(appointment.service_id)
                service_name = service.name if service else "Servicio no especificado"

            if not professional_name and appointment.professional_id:
                professional = await self.professional_repo.get_by_id(appointment.professional_id)
                professional_name = professional.name if professional else "Profesional no asignado"

            # Formatear fecha actual
            current_date_str = "Fecha no especificada"
            current_time_str = "Hora no especificada"
            if appointment.appointment_date:
                current_date_str = appointment.appointment_date.strftime("%A %d de %B, %Y")
                current_time_str = appointment.appointment_date.strftime("%H:%M")

            logger.info(f"✅ [RESCHEDULE] Appointment found and validated")

            return {
                "success": True,
                "tool_used": "reschedule_start",
                "display_type": "reschedule_current_info",
                "appointment_id": appointment_id,
                "current_appointment": {
                    "id": appointment.id,
                    "service_name": service_name,
                    "professional_name": professional_name,
                    "date": current_date_str,
                    "time": current_time_str,
                    "duration_minutes": appointment.duration_minutes or 30,
                    "price": appointment.price or 0
                },
                "message": f"Encontré tu cita actual. Te mostraré las opciones disponibles para reagendar con el mismo profesional.",
                "user_notification": f"📅 Tu cita actual:\n🏥 {service_name}\n👨‍⚕️ {professional_name}\n📅 {current_date_str} - {current_time_str}\n\nTe muestro las fechas disponibles para reagendar:",
                "next_action": "show_reschedule_calendar"
            }

        except Exception as e:
            logger.error(f"❌ [RESCHEDULE] Error starting reschedule process: {e}")
            return {
                "success": False,
                "error": f"reschedule_start_error: {str(e)}",
                "message": "Error iniciando el proceso de reagendamiento",
                "user_notification": "Hubo un problema iniciando el reagendamiento. Por favor, inténtalo de nuevo."
            }

    async def show_reschedule_calendar(
        self,
        appointment_id: str,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Muestra calendario interactivo con slots disponibles del mismo profesional
        """
        try:
            logger.info(f"📅 [RESCHEDULE_CALENDAR] Generating calendar for appointment {appointment_id}")

            # Obtener la cita para conocer el profesional
            appointment = await self.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                return {
                    "success": False,
                    "error": "appointment_not_found",
                    "message": "Cita no encontrada"
                }

            professional_id = appointment.professional_id
            if not professional_id:
                return {
                    "success": False,
                    "error": "no_professional_assigned",
                    "message": "La cita no tiene un profesional asignado",
                    "user_notification": "Esta cita no tiene un profesional asignado, no se puede reagendar automáticamente."
                }

            # Obtener el profesional
            professional = await self.professional_repo.get_by_id(professional_id)
            if not professional:
                return {
                    "success": False,
                    "error": "professional_not_found",
                    "message": "Profesional no encontrado"
                }

            # Generar slots disponibles para los próximos días
            available_slots = await self._generate_available_slots(
                professional_id=professional_id,
                exclude_appointment_id=appointment_id,
                days_ahead=days_ahead,
                duration_minutes=appointment.duration_minutes or 30
            )

            if not available_slots:
                logger.warning(f"⚠️ [RESCHEDULE_CALENDAR] No available slots found")
                return {
                    "success": False,
                    "error": "no_slots_available",
                    "message": "No hay horarios disponibles",
                    "user_notification": f"Lo siento, {professional.name} no tiene horarios disponibles en los próximos {days_ahead} días. Prueba contactando directamente para más opciones."
                }

            logger.info(f"✅ [RESCHEDULE_CALENDAR] Generated {len(available_slots)} available slots")

            return {
                "success": True,
                "tool_used": "reschedule_calendar",
                "display_type": "reschedule_calendar",
                "appointment_id": appointment_id,
                "professional_name": professional.name,
                "available_slots": available_slots,
                "message": f"Horarios disponibles con {professional.name}",
                "user_notification": f"📅 Horarios disponibles con {professional.name}:\n\nSelecciona tu nueva fecha y hora:",
                "calendar_data": {
                    "slots": available_slots,
                    "professional_id": professional_id,
                    "appointment_id": appointment_id
                }
            }

        except Exception as e:
            logger.error(f"❌ [RESCHEDULE_CALENDAR] Error generating calendar: {e}")
            return {
                "success": False,
                "error": f"calendar_error: {str(e)}",
                "message": "Error generando calendario",
                "user_notification": "Hubo un problema generando los horarios disponibles. Inténtalo de nuevo."
            }

    async def confirm_reschedule(
        self,
        appointment_id: str,
        new_date: str,
        new_time: str,
        user_confirmation: str = "yes"
    ) -> Dict[str, Any]:
        """
        Confirma el reagendamiento y actualiza la cita
        """
        try:
            logger.info(f"✅ [RESCHEDULE_CONFIRM] Confirming reschedule for {appointment_id} to {new_date} {new_time}")

            # Obtener la cita actual
            appointment = await self.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                return {
                    "success": False,
                    "error": "appointment_not_found",
                    "message": "Cita no encontrada"
                }

            # Parsear nueva fecha y hora
            try:
                new_datetime = self._parse_datetime(new_date, new_time)
            except ValueError as e:
                logger.error(f"❌ [RESCHEDULE_CONFIRM] Invalid datetime format: {e}")
                return {
                    "success": False,
                    "error": "invalid_datetime",
                    "message": "Formato de fecha/hora inválido",
                    "user_notification": "La fecha u hora seleccionada no es válida. Por favor, intenta de nuevo."
                }

            # Validar que no hay conflictos
            conflicts = await self.appointment_repo.get_overlapping_appointments(
                professional_id=appointment.professional_id,
                time_slot=self._create_time_slot(new_datetime, appointment.duration_minutes or 30)
            )

            # Filtrar conflictos excluyendo la cita actual
            active_conflicts = [
                conflict for conflict in conflicts
                if conflict.id != appointment_id and conflict.status not in [
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.COMPLETED
                ]
            ]

            if active_conflicts:
                logger.error(f"❌ [RESCHEDULE_CONFIRM] Time slot conflict detected")
                return {
                    "success": False,
                    "error": "time_slot_conflict",
                    "message": "El horario seleccionado ya no está disponible",
                    "user_notification": "Lo siento, ese horario ya no está disponible. Por favor, selecciona otro horario."
                }

            # Guardar datos antiguos para el email
            old_date_str = appointment.appointment_date.strftime("%A %d de %B, %Y") if appointment.appointment_date else "Fecha anterior"
            old_time_str = appointment.appointment_date.strftime("%H:%M") if appointment.appointment_date else "Hora anterior"

            # Actualizar la cita
            appointment.appointment_date = new_datetime
            appointment.updated_at = datetime.utcnow()

            # Opcional: marcar como reagendada
            if appointment.status == AppointmentStatus.SCHEDULED:
                appointment.status = AppointmentStatus.CONFIRMED

            # Guardar en BD
            updated_appointment = await self.appointment_repo.update(appointment)

            # Formatear nueva fecha para respuesta
            new_date_str = new_datetime.strftime("%A %d de %B, %Y")
            new_time_str = new_datetime.strftime("%H:%M")

            logger.info(f"✅ [RESCHEDULE_CONFIRM] Appointment successfully rescheduled")

            # Enviar email de confirmación del reagendamiento
            email_sent = False
            email_error = None
            if self.email_tool:
                try:
                    # Crear datos especiales para email de reagendamiento
                    reschedule_data = {
                        "old_date": old_date_str,
                        "old_time": old_time_str,
                        "new_date": new_date_str,
                        "new_time": new_time_str
                    }

                    # Usar el email tool con tipo "reschedule"
                    email_result = await self.email_tool.send_appointment_confirmation_email(
                        user_id=appointment.user_id,
                        appointment_id=appointment_id,
                        email_type="reschedule",
                        reschedule_data=reschedule_data
                    )

                    if email_result.get("success"):
                        email_sent = True
                        logger.info(f"📧 [RESCHEDULE_EMAIL] Reschedule confirmation email sent")
                    else:
                        email_error = email_result.get("error", "Unknown error")
                        logger.warning(f"⚠️ [RESCHEDULE_EMAIL] Failed to send email: {email_error}")

                except Exception as e:
                    email_error = str(e)
                    logger.error(f"❌ [RESCHEDULE_EMAIL] Email error: {e}")

            # Preparar respuesta
            user_notification = f"🔄 ¡Cita reagendada exitosamente!\n\n"
            user_notification += f"📋 Cambio realizado:\n"
            user_notification += f"❌ De: {old_date_str} - {old_time_str}\n"
            user_notification += f"✅ A: {new_date_str} - {new_time_str}\n\n"

            # Agregar datos que se mantienen
            service_name = appointment.service_name or "Servicio"
            professional_name = appointment.professional_name or "Profesional"
            user_notification += f"🏥 Servicio: {service_name}\n"
            user_notification += f"👨‍⚕️ Profesional: {professional_name}\n"
            user_notification += f"⏱️ Duración: {appointment.duration_minutes or 30} minutos"

            if email_sent:
                user_notification += f"\n\n📧 Te envié los detalles del cambio por email."
            elif email_error:
                user_notification += f"\n\n⚠️ No pude enviar el email de confirmación, pero tu cita está reagendada."

            return {
                "success": True,
                "tool_used": "reschedule_confirmed",
                "display_type": "reschedule_success",
                "appointment_id": appointment_id,
                "old_datetime": {
                    "date": old_date_str,
                    "time": old_time_str
                },
                "new_datetime": {
                    "date": new_date_str,
                    "time": new_time_str
                },
                "appointment_details": {
                    "service_name": service_name,
                    "professional_name": professional_name,
                    "duration_minutes": appointment.duration_minutes or 30,
                    "price": appointment.price or 0
                },
                "email_sent": email_sent,
                "message": "Cita reagendada exitosamente",
                "user_notification": user_notification
            }

        except Exception as e:
            logger.error(f"❌ [RESCHEDULE_CONFIRM] Error confirming reschedule: {e}")
            return {
                "success": False,
                "error": f"reschedule_confirm_error: {str(e)}",
                "message": "Error confirmando el reagendamiento",
                "user_notification": "Hubo un problema confirmando el reagendamiento. Por favor, inténtalo de nuevo."
            }

    async def _generate_available_slots(
        self,
        professional_id: str,
        exclude_appointment_id: str,
        days_ahead: int = 7,
        duration_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Genera slots disponibles para el profesional"""
        available_slots = []

        # Horarios de trabajo (esto podría venir del profesional en el futuro)
        work_hours = {
            "start": 8,  # 8:00 AM
            "end": 18,   # 6:00 PM
            "interval": 30  # 30 minutos por slot
        }

        # Generar slots para los próximos días
        for day_offset in range(1, days_ahead + 1):
            date = datetime.now(timezone.utc).date() + timedelta(days=day_offset)

            # Saltar domingos
            if date.weekday() == 6:
                continue

            # Generar slots para ese día
            for hour in range(work_hours["start"], work_hours["end"]):
                for minute in [0, 30]:
                    slot_datetime = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
                    # Hacer el datetime timezone-aware (UTC)
                    slot_datetime = slot_datetime.replace(tzinfo=timezone.utc)

                    # Verificar si hay conflictos
                    time_slot = self._create_time_slot(slot_datetime, duration_minutes)
                    conflicts = await self.appointment_repo.get_overlapping_appointments(
                        professional_id=professional_id,
                        time_slot=time_slot
                    )

                    # Filtrar conflictos activos (excluyendo la cita actual)
                    active_conflicts = [
                        conflict for conflict in conflicts
                        if conflict.id != exclude_appointment_id and conflict.status not in [
                            AppointmentStatus.CANCELLED,
                            AppointmentStatus.COMPLETED
                        ]
                    ]

                    if not active_conflicts:
                        available_slots.append({
                            "date": date.strftime("%Y-%m-%d"),
                            "time": slot_datetime.strftime("%H:%M"),
                            "datetime": slot_datetime.isoformat(),
                            "display_date": date.strftime("%A %d de %B"),
                            "display_time": slot_datetime.strftime("%H:%M"),
                            "available": True
                        })

                        # Limitar a 20 slots para no sobrecargar la UI
                        if len(available_slots) >= 20:
                            return available_slots

        return available_slots

    def _create_time_slot(self, start_datetime: datetime, duration_minutes: int):
        """Crea un TimeSlot para validación de conflictos"""
        from ...value_objects.time_slot import TimeSlot
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        return TimeSlot(start_time=start_datetime, end_time=end_datetime)

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
        """Parsea strings de fecha y hora a datetime"""
        try:
            # Formato esperado: "2025-09-25" y "15:00"
            date_part = datetime.strptime(date_str, "%Y-%m-%d").date()
            time_part = datetime.strptime(time_str, "%H:%M").time()
            result = datetime.combine(date_part, time_part)
            # Hacer timezone-aware (UTC)
            return result.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"Invalid date/time format: {date_str} {time_str}")