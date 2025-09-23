"""
AI Tool: Agendamiento Completo de Citas
Herramienta integral para que OpenAI gestione todo el flujo de agendamiento de citas
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from ...repositories.user_repository import IUserRepository
from ...repositories.service_repository import IServiceRepository
from ...repositories.professional_repository import IProfessionalRepository
from ...repositories.appointment_repository import IAppointmentRepository
from ...entities.appointment import Appointment
from ...entities.patient import Patient
from ...entities.appointment import AppointmentStatus
from ...value_objects.time_slot import TimeSlot

logger = logging.getLogger(__name__)


class AppointmentBookingTool:
    """
    Herramienta AI: Agendamiento Completo de Citas

    OpenAI usa esta herramienta cuando:
    1. Usuario dice "Quiero agendar", "Necesito una cita", etc.
    2. Maneja todo el flujo: verificación → servicios → calendario → confirmación
    3. Solo funciona si el usuario está autenticado en la sesión
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        service_repository: IServiceRepository,
        professional_repository: IProfessionalRepository,
        appointment_repository: IAppointmentRepository
    ):
        self._user_repo = user_repository
        self._service_repo = service_repository
        self._professional_repo = professional_repository
        self._appointment_repo = appointment_repository

    async def start_booking_process(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inicia el proceso de agendamiento
        Verifica autenticación y muestra servicios disponibles
        """
        try:
            logger.info("[APPOINTMENT_BOOKING] Starting booking process")

            # Verificar si el usuario está autenticado en la memoria del chat
            user_authenticated = conversation_context.get("user_authenticated", False)
            user_data = conversation_context.get("user_data", {})

            logger.info(f"[APPOINTMENT_BOOKING] User authenticated: {user_authenticated}")
            logger.info(f"[APPOINTMENT_BOOKING] User data: {user_data}")

            if not user_authenticated or not user_data.get("id"):
                logger.info("[APPOINTMENT_BOOKING] User not authenticated - requesting authentication")
                return {
                    "tool_used": "appointment_booking",
                    "action": "authentication_required",
                    "success": False,
                    "message": "Para agendar una cita necesito verificar tu identidad primero. ¿Puedes proporcionarme tu email o número de teléfono?",
                    "next_step": "authentication",
                    "requires_user_input": True,
                    "authentication_status": "required"
                }

            # Usuario autenticado - obtener servicios disponibles
            logger.info("[APPOINTMENT_BOOKING] User authenticated - getting available services")
            services = await self._service_repo.get_active_services()

            if not services:
                return {
                    "tool_used": "appointment_booking",
                    "action": "no_services_available",
                    "success": False,
                    "message": "Lo siento, no hay servicios disponibles en este momento. ¿Puedes intentar más tarde?",
                    "next_step": "retry"
                }

            # Agrupar servicios por categoría
            service_categories = {}
            for service in services:
                # Obtener profesionales disponibles para este servicio
                professionals = await self._professional_repo.get_by_service_id(service.id)
                active_professionals = [p for p in professionals if p.is_active]

                if len(active_professionals) == 0:
                    continue  # Skip servicios sin profesionales disponibles

                # Mapear service_type a categorías amigables
                type_to_category = {
                    "medical": "consulta",
                    "beauty": "belleza",
                    "consultation": "especialidad",
                    "maintenance": "terapia",
                    "other": "otros"
                }

                category = type_to_category.get(service.service_type.value, service.service_type.value)
                if category not in service_categories:
                    service_categories[category] = []

                service_categories[category].append({
                    "id": service.id,
                    "name": service.name,
                    "description": service.description,
                    "price": service.price or 0,
                    "currency": "COP",
                    "duration_minutes": service.duration_minutes,
                    "available_professionals": len(active_professionals)
                })

            logger.info(f"[APPOINTMENT_BOOKING] Found {len(services)} services in {len(service_categories)} categories")

            return {
                "tool_used": "appointment_booking",
                "action": "show_services",
                "success": True,
                "display_type": "service_catalog",
                "message": f"¡Perfecto {user_data.get('name', 'Usuario')}! Aquí están nuestros servicios disponibles. ¿Cuál te interesa?",
                "service_data": {
                    "categories": service_categories,
                    "total_services": len(services)
                },
                "tool_response": {
                    "display_type": "service_catalog",
                    "catalog_config": {
                        "id": "appointment_booking_services",
                        "type": "service_grid",
                        "title": "🏥 Servicios Disponibles para Agendar",
                        "subtitle": f"Hola {user_data.get('name', 'Usuario')}, selecciona el servicio que necesitas:",
                        "theme": {
                            "primary_color": "#059669",
                            "background": "#F0FDF4",
                            "card_background": "#FFFFFF",
                            "border_radius": "16px",
                            "grid_columns": 2
                        },
                        "categories": self._format_categories_for_appointment(service_categories)
                    }
                },
                "context_updates": {
                    "booking_step": "service_selection",
                    "available_services": service_categories,
                    "booking_in_progress": True
                },
                "next_step": "service_selection",
                "requires_user_input": True
            }

        except Exception as e:
            logger.error(f"Error starting booking process: {e}")
            return {
                "tool_used": "appointment_booking",
                "action": "error",
                "success": False,
                "error": str(e),
                "message": "Hubo un error iniciando el proceso de agendamiento. ¿Puedes intentar nuevamente?",
                "next_step": "retry"
            }

    async def select_service(self, service_id: str, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa la selección de servicio y muestra calendario disponible
        """
        try:
            logger.info(f"[APPOINTMENT_BOOKING] Service selected: {service_id}")

            # Verificar que el usuario sigue autenticado
            user_data = conversation_context.get("user_data", {})
            if not user_data.get("id"):
                return await self.start_booking_process(conversation_context)

            # Obtener información del servicio
            service = await self._service_repo.get_by_id(service_id)
            if not service:
                return {
                    "tool_used": "appointment_booking",
                    "action": "service_not_found",
                    "success": False,
                    "message": "No encontré ese servicio. ¿Puedes seleccionar otro?",
                    "next_step": "service_selection"
                }

            # Obtener profesionales que ofrecen este servicio
            professionals = await self._professional_repo.get_by_service_id(service_id)
            active_professionals = [p for p in professionals if p.is_active]

            if not active_professionals:
                return {
                    "tool_used": "appointment_booking",
                    "action": "no_professionals_available",
                    "success": False,
                    "message": f"Lo siento, no hay profesionales disponibles para {service.name} en este momento.",
                    "next_step": "service_selection"
                }

            # Generar slots disponibles para los próximos 30 días
            available_slots = await self._generate_available_slots(
                service_id,
                active_professionals,
                service.duration_minutes
            )

            if not available_slots:
                return {
                    "tool_used": "appointment_booking",
                    "action": "no_slots_available",
                    "success": False,
                    "message": f"No hay horarios disponibles para {service.name} en los próximos días. ¿Te gustaría seleccionar otro servicio?",
                    "next_step": "service_selection"
                }

            logger.info(f"[APPOINTMENT_BOOKING] Generated {len(available_slots)} available slots")

            return {
                "tool_used": "appointment_booking",
                "action": "show_calendar",
                "success": True,
                "display_type": "appointment_calendar",
                "message": f"Excelente elección: {service.name}. Aquí están los horarios disponibles:",
                "service_info": {
                    "id": service.id,
                    "name": service.name,
                    "description": service.description,
                    "duration_minutes": service.duration_minutes,
                    "price": service.price
                },
                "calendar_data": {
                    "available_slots": available_slots,
                    "service_duration": service.duration_minutes
                },
                "tool_response": {
                    "display_type": "appointment_calendar",
                    "calendar_config": {
                        "id": "appointment_booking_calendar",
                        "service_name": service.name,
                        "service_duration": service.duration_minutes,
                        "available_slots": available_slots
                    }
                },
                "context_updates": {
                    "booking_step": "time_selection",
                    "selected_service_id": service_id,
                    "selected_service_name": service.name,
                    "available_slots": available_slots
                },
                "next_step": "time_selection",
                "requires_user_input": True
            }

        except Exception as e:
            logger.error(f"Error selecting service: {e}")
            return {
                "tool_used": "appointment_booking",
                "action": "error",
                "success": False,
                "error": str(e),
                "message": "Hubo un error procesando tu selección. ¿Puedes intentar nuevamente?",
                "next_step": "service_selection"
            }

    async def book_appointment(
        self,
        slot_datetime: str,
        conversation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea la cita con el slot seleccionado
        """
        try:
            logger.info(f"[APPOINTMENT_BOOKING] Booking appointment for slot: {slot_datetime}")

            # Verificar datos necesarios
            user_data = conversation_context.get("user_data", {})
            service_id = conversation_context.get("selected_service_id")

            if not user_data.get("id") or not service_id:
                return {
                    "tool_used": "appointment_booking",
                    "action": "missing_data",
                    "success": False,
                    "message": "Faltan datos para completar la reserva. ¿Puedes intentar nuevamente?",
                    "next_step": "restart_booking"
                }

            # Parsear fecha/hora
            try:
                appointment_datetime = datetime.fromisoformat(slot_datetime.replace('Z', '+00:00'))
            except ValueError:
                return {
                    "tool_used": "appointment_booking",
                    "action": "invalid_datetime",
                    "success": False,
                    "message": "El horario seleccionado no es válido. ¿Puedes seleccionar otro?",
                    "next_step": "time_selection"
                }

            # Obtener información del servicio
            service = await self._service_repo.get_by_id(service_id)
            if not service:
                return {
                    "tool_used": "appointment_booking",
                    "action": "service_not_found",
                    "success": False,
                    "message": "No encontré el servicio seleccionado. ¿Puedes intentar nuevamente?",
                    "next_step": "service_selection"
                }

            # Encontrar profesional disponible para esa fecha/hora
            professionals = await self._professional_repo.get_by_service_id(service_id)
            active_professionals = [p for p in professionals if p.is_active]

            selected_professional = None
            for professional in active_professionals:
                # Verificar disponibilidad del profesional en esa fecha/hora
                is_available = await self._check_professional_availability(
                    professional.id,
                    appointment_datetime,
                    service.duration_minutes
                )
                if is_available:
                    selected_professional = professional
                    break

            if not selected_professional:
                return {
                    "tool_used": "appointment_booking",
                    "action": "slot_no_longer_available",
                    "success": False,
                    "message": "Lo siento, ese horario ya no está disponible. ¿Puedes seleccionar otro?",
                    "next_step": "time_selection"
                }

            # Crear la cita
            end_datetime = appointment_datetime + timedelta(minutes=service.duration_minutes)
            time_slot = TimeSlot(
                start_time=appointment_datetime,
                end_time=end_datetime
            )

            appointment = Appointment(
                id=None,  # Se genera automáticamente
                user_id=user_data["id"],
                service_id=service_id,
                professional_id=selected_professional.id,
                time_slot=time_slot,
                status=AppointmentStatus.CONFIRMED,
                notes=f"Cita agendada via chat IA para {service.name}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Guardar en base de datos
            created_appointment = await self._appointment_repo.create(appointment)

            logger.info(f"[APPOINTMENT_BOOKING] Appointment created successfully with ID: {created_appointment.id}")

            return {
                "tool_used": "appointment_booking",
                "action": "appointment_confirmed",
                "success": True,
                "display_type": "appointment_confirmation",
                "message": f"¡Excelente {user_data.get('name')}! Tu cita ha sido confirmada.",
                "appointment_data": {
                    "id": created_appointment.id,
                    "service_name": service.name,
                    "professional_name": selected_professional.name,
                    "date": appointment_datetime.strftime("%Y-%m-%d"),
                    "time": appointment_datetime.strftime("%H:%M"),
                    "duration": service.duration_minutes,
                    "price": service.price,
                    "status": "confirmed"
                },
                "tool_response": {
                    "display_type": "appointment_confirmation",
                    "confirmation_data": {
                        "appointment_id": created_appointment.id,
                        "service_name": service.name,
                        "professional_name": selected_professional.name,
                        "datetime": appointment_datetime.isoformat(),
                        "duration_minutes": service.duration_minutes,
                        "price": service.price
                    }
                },
                "context_updates": {
                    "booking_step": "completed",
                    "booking_in_progress": False,
                    "last_appointment_id": created_appointment.id
                },
                "next_step": "completed"
            }

        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {
                "tool_used": "appointment_booking",
                "action": "booking_error",
                "success": False,
                "error": str(e),
                "message": "Hubo un error creando tu cita. ¿Puedes intentar nuevamente?",
                "next_step": "time_selection"
            }

    async def _generate_available_slots(
        self,
        service_id: str,
        professionals: List,
        duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Genera slots disponibles utilizando la API real de disponibilidad
        """
        try:
            logger.info(f"[APPOINTMENT_BOOKING] Generating real availability slots for service {service_id}")

            # Usar la API real de disponibilidad del appointment controller
            from ....application.dto.appointment_dto import AvailabilityRequestDTO
            from ....infrastructure.dependencies import get_appointment_controller

            # Crear el request para obtener disponibilidad
            availability_request = AvailabilityRequestDTO(
                service_id=service_id,
                start_date=(datetime.now().date()).isoformat(),
                end_date=(datetime.now().date() + timedelta(days=30)).isoformat(),
                duration_minutes=duration_minutes
            )

            # Obtener el controller y consultar disponibilidad real
            controller = await get_appointment_controller()
            availability_response = await controller.get_available_slots(availability_request)

            if not availability_response.available_slots:
                logger.warning(f"[APPOINTMENT_BOOKING] No available slots found for service {service_id}")
                return []

            # Transformar la respuesta al formato esperado por el frontend
            available_slots = []
            for slot in availability_response.available_slots:
                # Parsear la fecha/hora del slot
                try:
                    slot_datetime = datetime.fromisoformat(slot.start_time.replace('Z', '+00:00'))
                    end_datetime = datetime.fromisoformat(slot.end_time.replace('Z', '+00:00'))

                    # Encontrar el profesional para este slot
                    professional_name = "Profesional disponible"
                    professional_id = slot.professional_id if hasattr(slot, 'professional_id') else None

                    if professional_id:
                        for prof in professionals:
                            if prof.id == professional_id:
                                professional_name = prof.name
                                break
                    else:
                        # Si no hay professional_id específico, usar el primero disponible
                        if professionals:
                            professional_name = professionals[0].name
                            professional_id = professionals[0].id

                    available_slots.append({
                        "start_time": slot.start_time,
                        "end_time": slot.end_time,
                        "professional_id": professional_id,
                        "professional_name": professional_name,
                        "date": slot_datetime.strftime("%Y-%m-%d"),
                        "time": slot_datetime.strftime("%H:%M"),
                        "day_name": slot_datetime.strftime("%A"),
                        "available": True
                    })

                except ValueError as ve:
                    logger.warning(f"[APPOINTMENT_BOOKING] Invalid datetime format in slot: {slot.start_time}")
                    continue

            logger.info(f"[APPOINTMENT_BOOKING] Successfully generated {len(available_slots)} real availability slots")
            return available_slots

        except Exception as e:
            logger.error(f"[APPOINTMENT_BOOKING] Error getting real availability, falling back to basic generation: {e}")

            # Fallback a generación básica si falla la API real
            return await self._generate_basic_slots(service_id, professionals, duration_minutes)

    async def _generate_basic_slots(
        self,
        service_id: str,
        professionals: List,
        duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Fallback: Genera slots básicos cuando la API real no está disponible
        """
        try:
            available_slots = []
            current_date = datetime.now().date()
            current_datetime = datetime.now()

            for day_offset in range(14):  # Reducido a 14 días para fallback
                check_date = current_date + timedelta(days=day_offset)

                # Generar horarios de 8:00 AM a 6:00 PM cada 60 minutos (menos slots para fallback)
                start_hour = 8
                end_hour = 18

                for hour in range(start_hour, end_hour):
                    slot_start = datetime.combine(check_date, datetime.min.time().replace(hour=hour, minute=0))

                    # No mostrar slots en el pasado
                    if slot_start <= current_datetime:
                        continue

                    # Verificar si algún profesional está disponible
                    for professional in professionals:
                        is_available = await self._check_professional_availability(
                            professional.id,
                            slot_start,
                            duration_minutes
                        )

                        if is_available:
                            available_slots.append({
                                "start_time": slot_start.isoformat(),
                                "end_time": (slot_start + timedelta(minutes=duration_minutes)).isoformat(),
                                "professional_id": professional.id,
                                "professional_name": professional.name,
                                "date": slot_start.strftime("%Y-%m-%d"),
                                "time": slot_start.strftime("%H:%M"),
                                "day_name": slot_start.strftime("%A"),
                                "available": True
                            })
                            break  # Solo necesitamos uno disponible por slot

                # Limitar a 20 slots para fallback
                if len(available_slots) >= 20:
                    break

            return available_slots

        except Exception as e:
            logger.error(f"Error generating basic slots: {e}")
            return []

    async def _check_professional_availability(
        self,
        professional_id: str,
        start_time: datetime,
        duration_minutes: int
    ) -> bool:
        """
        Verifica si un profesional está disponible en el horario especificado
        """
        try:
            end_time = start_time + timedelta(minutes=duration_minutes)

            # Buscar citas existentes que se solapen
            existing_appointments = await self._appointment_repo.get_by_professional_and_date_range(
                professional_id,
                start_time.date(),
                start_time.date()
            )

            for appointment in existing_appointments:
                if appointment.status in [AppointmentStatus.CONFIRMED, AppointmentStatus.SCHEDULED]:
                    # Verificar solapamiento
                    apt_start = appointment.time_slot.start_time
                    apt_end = appointment.time_slot.end_time

                    if (start_time < apt_end and end_time > apt_start):
                        return False  # Hay solapamiento

            return True

        except Exception as e:
            logger.error(f"Error checking professional availability: {e}")
            return False

    def _format_categories_for_appointment(self, categories: Dict) -> List[Dict]:
        """
        Formatea las categorías para el display del frontend en modo agendamiento
        """
        formatted_categories = []

        for category_name, services in categories.items():
            formatted_services = []
            for service in services:
                formatted_services.append({
                    "id": service["id"],
                    "title": service["name"],
                    "description": service["description"],
                    "price": f"${service['price']:,} COP",
                    "duration": f"{service['duration_minutes']} min",
                    "availability_status": "available",
                    "availability_text": f"{service['available_professionals']} profesionales disponibles",
                    "action_button": {
                        "text": "Agendar",
                        "action": f"book_service_{service['id']}"
                    }
                })

            formatted_categories.append({
                "category_name": category_name,
                "category_display": category_name.title(),
                "icon": self._get_category_icon(category_name),
                "service_count": len(services),
                "services": formatted_services
            })

        return formatted_categories

    def _get_category_icon(self, category: str) -> str:
        """Devuelve el icono apropiado para cada categoría"""
        icons = {
            "consulta": "CONSULTA",
            "especialidad": "ESPECIALIDAD",
            "terapia": "TERAPIA",
            "belleza": "BELLEZA",
            "otros": "OTROS"
        }
        return icons.get(category.lower(), "SERVICIO")

    def get_tool_info(self) -> Dict[str, Any]:
        """Información sobre esta herramienta para OpenAI Function Calling"""
        return {
            "name": "appointment_booking_tool",
            "description": "Herramienta integral para agendar citas - maneja todo el flujo desde verificación hasta confirmación",
            "functions": [
                {
                    "name": "start_booking_process",
                    "description": "USAR AUTOMÁTICAMENTE cuando el usuario quiera agendar una cita. Inicia el proceso completo de agendamiento verificando autenticación y mostrando servicios.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversation_context": {
                                "type": "object",
                                "description": "Contexto actual de la conversación con datos del usuario"
                            }
                        },
                        "required": ["conversation_context"]
                    }
                },
                {
                    "name": "select_service",
                    "description": "Procesa la selección de servicio y muestra calendario disponible",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_id": {
                                "type": "string",
                                "description": "ID del servicio seleccionado por el usuario"
                            },
                            "conversation_context": {
                                "type": "object",
                                "description": "Contexto actual de la conversación"
                            }
                        },
                        "required": ["service_id", "conversation_context"]
                    }
                },
                {
                    "name": "book_appointment",
                    "description": "Confirma y crea la cita con el horario seleccionado",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "slot_datetime": {
                                "type": "string",
                                "description": "Fecha y hora del slot seleccionado en formato ISO"
                            },
                            "conversation_context": {
                                "type": "object",
                                "description": "Contexto actual de la conversación"
                            }
                        },
                        "required": ["slot_datetime", "conversation_context"]
                    }
                }
            ]
        }