"""
AI Tool: Agendamiento de Citas
Herramienta para manejar todo el proceso de agendamiento desde selección de servicio hasta confirmación
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from ...repositories.service_repository import IServiceRepository
from ...repositories.professional_repository import IProfessionalRepository
from ...repositories.user_repository import IUserRepository
from ...repositories.appointment_repository import IAppointmentRepository
from ...entities.appointment import Appointment, AppointmentStatus

logger = logging.getLogger(__name__)


class AppointmentSchedulingTool:
    """
    Herramienta AI: Agendamiento de Citas
    
    OpenAI usa esta herramienta cuando:
    1. Usuario selecciona un servicio específico
    2. Necesita ver horarios disponibles
    3. Quiere confirmar una cita
    4. Maneja todo el flujo de agendamiento
    """
    
    def __init__(
        self,
        service_repository: IServiceRepository,
        professional_repository: IProfessionalRepository,
        user_repository: IUserRepository,
        appointment_repository: IAppointmentRepository
    ):
        self._service_repo = service_repository
        self._professional_repo = professional_repository
        self._user_repo = user_repository
        self._appointment_repo = appointment_repository
    
    async def create_draft_appointment(
        self, 
        user_id: str,
        service_id: str,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Crea un borrador de cita cuando el usuario selecciona un servicio
        Esta cita queda en estado DRAFT hasta que se confirme fecha/hora
        """
        try:
            # Verificar que existe el servicio
            service = await self._service_repo.get_by_id(service_id)
            if not service:
                return {
                    "success": False,
                    "error": "service_not_found",
                    "message": f"No encontré el servicio {service_name}. ¿Puedes elegir otro?"
                }
            
            # Verificar que existe el usuario
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "error": "user_not_found", 
                    "message": "Necesitas estar registrado para agendar una cita. ¿Te ayudo con el registro?"
                }
            
            # Crear cita borrador
            draft_appointment = Appointment(
                id=None,
                user_id=user_id,
                service_id=service_id,
                professional_id=None,  # Se asignará después
                appointment_date=None,  # Se asignará cuando usuario elija
                status=AppointmentStatus.DRAFT,
                notes=f"Cita solicitada para {service_name}",
                created_at=datetime.utcnow()
            )
            
            # Guardar borrador en BD
            saved_appointment = await self._appointment_repo.create(draft_appointment)
            
            logger.info(f"Draft appointment created: {saved_appointment.id} for service {service_name}")
            
            # Generar horarios disponibles
            available_slots = await self._generate_available_time_slots(service)
            
            return {
                "tool_used": "appointment_scheduling",
                "action": "draft_created",
                "success": True,
                "appointment_id": saved_appointment.id,
                "service_data": {
                    "id": service.id,
                    "name": service.name,
                    "duration_minutes": service.duration_minutes,
                    "price": service.price
                },
                "available_slots": available_slots,
                "message": f"¡Perfecto! Has seleccionado {service_name}. Ahora elige cuándo quieres tu cita:",
                "display_type": "time_slot_selector",
                "tool_response": {
                    "display_type": "time_slot_selector",
                    "slot_config": {
                        "id": "appointment_time_selector",
                        "type": "time_grid",
                        "title": f"Horarios Horarios Disponibles para {service_name}",
                        "subtitle": f"Duración: {service.duration_minutes} minutos | Precio: ${service.price:,} COP",
                        "service_info": {
                            "name": service_name,
                            "duration": service.duration_minutes,
                            "price": service.price
                        },
                        "time_slots": available_slots
                    }
                },
                "next_step": "time_selection",
                "conversation_flow": "awaiting_time_selection"
            }
            
        except Exception as e:
            logger.error(f"Error creating draft appointment: {e}")
            return {
                "success": False,
                "error": f"Error creando borrador de cita: {str(e)}",
                "message": "Hubo un error procesando tu selección. ¿Puedes intentar nuevamente?"
            }
    
    async def confirm_appointment(
        self,
        appointment_id: str,
        selected_date: str,
        selected_time: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Confirma una cita asignándole fecha, hora y profesional
        """
        try:
            # Obtener el borrador de cita
            appointment = await self._appointment_repo.get_by_id(appointment_id)
            if not appointment or appointment.status != AppointmentStatus.DRAFT:
                return {
                    "success": False,
                    "error": "appointment_not_found",
                    "message": "No encontré esa cita. ¿Quieres empezar nuevamente?"
                }
            
            # Verificar que la cita pertenece al usuario
            if appointment.user_id != user_id:
                return {
                    "success": False,
                    "error": "unauthorized",
                    "message": "No puedes modificar esta cita."
                }
            
            # Parsear fecha y hora seleccionada
            try:
                appointment_datetime = datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                return {
                    "success": False,
                    "error": "invalid_datetime",
                    "message": "Formato de fecha u hora inválido. Usa el selector de horarios."
                }
            
            # Verificar disponibilidad real
            is_available = await self._check_time_slot_availability(
                appointment.service_id,
                appointment_datetime
            )
            
            if not is_available:
                return {
                    "success": False,
                    "error": "time_not_available",
                    "message": "Ese horario ya no está disponible. ¿Puedes elegir otro?"
                }
            
            # Asignar profesional disponible
            service = await self._service_repo.get_by_id(appointment.service_id)
            professional = await self._assign_available_professional(service, appointment_datetime)
            
            if not professional:
                return {
                    "success": False,
                    "error": "no_professional_available",
                    "message": "No hay profesionales disponibles en ese horario. ¿Puedes elegir otro?"
                }
            
            # Actualizar la cita con TODOS los datos del servicio
            appointment.appointment_date = appointment_datetime
            appointment.professional_id = professional.id
            appointment.duration_minutes = service.duration_minutes  # 🔧 AGREGADO
            appointment.price = service.price                        # 🔧 AGREGADO
            appointment.status = AppointmentStatus.CONFIRMED
            appointment.updated_at = datetime.utcnow()
            
            # Guardar cambios
            updated_appointment = await self._appointment_repo.update(appointment)
            
            # Obtener datos completos para respuesta
            user = await self._user_repo.get_by_id(user_id)
            
            logger.info(f"Appointment confirmed: {updated_appointment.id} for {appointment_datetime}")
            
            return {
                "tool_used": "appointment_scheduling",
                "action": "appointment_confirmed",
                "success": True,
                "appointment_data": {
                    "id": updated_appointment.id,
                    "service_name": service.name,
                    "date": appointment_datetime.strftime("%Y-%m-%d"),
                    "time": appointment_datetime.strftime("%H:%M"),
                    "datetime_display": appointment_datetime.strftime("%A %d de %B, %Y a las %H:%M"),
                    "duration_minutes": service.duration_minutes,
                    "price": service.price,
                    "professional_name": professional.name,
                    "status": "Confirmada"
                },
                "message": f"🎉 ¡Tu cita ha sido confirmada exitosamente!\n\n" +
                          f"📋 Servicio: {service.name}\n" +
                          f"📅 Fecha: {appointment_datetime.strftime('%A %d de %B, %Y')}\n" +
                          f"🕐 Hora: {appointment_datetime.strftime('%H:%M')}\n" +
                          f"👨‍⚕️ Profesional: {professional.name}\n" +
                          f"⏱️ Duración: {service.duration_minutes} minutos\n" +
                          f"💰 Precio: ${service.price:,} COP\n\n" +
                          f"¡Te esperamos {user.name}! Nos vemos pronto. 😊",
                "display_type": "appointment_confirmation",
                "next_step": "appointment_completed",
                "conversation_flow": "appointment_confirmed"
            }
            
        except Exception as e:
            logger.error(f"Error confirming appointment: {e}")
            return {
                "success": False,
                "error": f"Error confirmando cita: {str(e)}",
                "message": "Hubo un error confirmando tu cita. ¿Puedes intentar nuevamente?"
            }
    
    async def _generate_available_time_slots(self, service) -> List[Dict[str, Any]]:
        """Genera horarios disponibles basados en profesionales reales y sus horarios"""
        slots = []
        
        # Obtener profesionales que pueden realizar este servicio
        professionals = await self._professional_repo.get_by_service_id(service.id)
        active_professionals = [p for p in professionals if p.is_active]
        
        if not active_professionals:
            logger.warning(f"No active professionals found for service {service.id}")
            # Fallback: mostrar horarios genéricos si no hay profesionales
            return await self._generate_fallback_slots(service)
        
        logger.info(f"Found {len(active_professionals)} professionals for service {service.name}")
        
        # Mapear días de la semana
        weekday_map = {
            0: "monday", 1: "tuesday", 2: "wednesday",
            3: "thursday", 4: "friday", 5: "saturday", 6: "sunday"
        }
        
        for day_offset in range(7):  # Próximos 7 días
            date = datetime.now() + timedelta(days=day_offset + 1)  # Empezar desde mañana
            weekday = weekday_map[date.weekday()]
            
            day_slots = []
            
            # Para cada profesional, verificar sus horarios de trabajo
            for professional in active_professionals:
                # Buscar horario de trabajo para este día
                working_hours = None
                if hasattr(professional, 'working_hours'):
                    for wh in professional.working_hours:
                        if wh.day.value == weekday and wh.is_available:
                            working_hours = wh
                            break
                
                if not working_hours:
                    # Si no tiene horario específico, usar horario por defecto
                    if weekday != "sunday":  # No trabajar domingos por defecto
                        working_hours = type('obj', (object,), {
                            'start_time': "08:00",
                            'end_time': "18:00",
                            'is_available': True
                        })
                    else:
                        continue
                
                if working_hours and working_hours.is_available:
                    # Parsear horas de inicio y fin (manejar tanto time objects como strings)
                    if isinstance(working_hours.start_time, str):
                        start_hour, start_min = map(int, working_hours.start_time.split(':'))
                        end_hour, end_min = map(int, working_hours.end_time.split(':'))
                    else:
                        # Es un time object de Python
                        start_hour, start_min = working_hours.start_time.hour, working_hours.start_time.minute
                        end_hour, end_min = working_hours.end_time.hour, working_hours.end_time.minute
                    
                    # Generar slots cada 30 minutos dentro del horario de trabajo
                    current_hour = start_hour
                    current_min = start_min
                    
                    while current_hour < end_hour or (current_hour == end_hour and current_min < end_min):
                        slot_time = date.replace(hour=current_hour, minute=current_min, second=0, microsecond=0)
                        
                        # Solo mostrar horarios futuros
                        if slot_time > datetime.now():
                            # Verificar disponibilidad real (no hay citas en ese horario)
                            is_available = await self._check_slot_availability_for_professional(
                                professional.id, slot_time, service.duration_minutes
                            )
                            
                            if is_available:
                                slot_exists = False
                                for existing_slot in day_slots:
                                    if existing_slot['time'] == slot_time.strftime("%H:%M"):
                                        # Agregar profesional a slot existente
                                        existing_slot['professionals'].append({
                                            "id": professional.id,
                                            "name": professional.name
                                        })
                                        slot_exists = True
                                        break
                                
                                if not slot_exists:
                                    day_slots.append({
                                        "time": slot_time.strftime("%H:%M"),
                                        "display": slot_time.strftime("%I:%M %p"),
                                        "available": True,
                                        "datetime": slot_time.isoformat(),
                                        "professionals": [{
                                            "id": professional.id,
                                            "name": professional.name
                                        }]
                                    })
                        
                        # Avanzar 30 minutos
                        current_min += 30
                        if current_min >= 60:
                            current_min = 0
                            current_hour += 1
            
            # Ordenar slots por hora
            day_slots.sort(key=lambda x: x['time'])
            
            if day_slots:  # Solo agregar días con slots disponibles
                slots.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "date_display": date.strftime("%A %d de %B"),
                    "day_name": date.strftime("%A"),
                    "slots": day_slots[:16],  # Máximo 16 slots por día
                    "total_slots": len(day_slots)
                })
        
        return slots[:5]  # Mostrar máximo 5 días
    
    async def _generate_fallback_slots(self, service) -> List[Dict[str, Any]]:
        """Genera horarios de respaldo cuando no hay profesionales disponibles"""
        slots = []
        work_start = 8
        work_end = 18
        
        for day_offset in range(7):
            date = datetime.now() + timedelta(days=day_offset + 1)
            if date.weekday() == 6:  # Saltar domingos
                continue
            
            day_slots = []
            for hour in range(work_start, work_end):
                for minute in [0, 30]:
                    slot_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if slot_time > datetime.now():
                        day_slots.append({
                            "time": slot_time.strftime("%H:%M"),
                            "display": slot_time.strftime("%I:%M %p"),
                            "available": False,  # Marcar como no disponible
                            "datetime": slot_time.isoformat(),
                            "professionals": [],
                            "message": "No hay profesionales disponibles"
                        })
            
            if day_slots:
                slots.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "date_display": date.strftime("%A %d de %B"),
                    "day_name": date.strftime("%A"),
                    "slots": day_slots[:8],  # Menos slots en fallback
                    "warning": "No hay profesionales asignados a este servicio"
                })
        
        return slots[:3]  # Solo 3 días en fallback
    
    async def _check_time_slot_availability(self, service_id: str, appointment_datetime: datetime) -> bool:
        """Verifica si un horario específico está disponible"""
        try:
            # Buscar citas existentes en ese horario
            existing_appointments = await self._appointment_repo.get_by_date_range(
                start_date=appointment_datetime - timedelta(minutes=30),
                end_date=appointment_datetime + timedelta(minutes=30)
            )
            
            # Si hay menos de 3 citas en esa franja, está disponible
            return len(existing_appointments) < 3
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return True  # Default a disponible si hay error
    
    async def _check_slot_availability_for_professional(
        self, 
        professional_id: str, 
        slot_time: datetime, 
        duration_minutes: int
    ) -> bool:
        """Verifica si un profesional específico está disponible en un horario"""
        try:
            # Calcular rango de tiempo considerando duración del servicio
            slot_end = slot_time + timedelta(minutes=duration_minutes)
            
            # Buscar citas existentes del profesional en ese rango
            existing_appointments = await self._appointment_repo.get_by_professional_and_date_range(
                professional_id=professional_id,
                start_date=slot_time - timedelta(minutes=15),  # Buffer de 15 min antes
                end_date=slot_end + timedelta(minutes=15)  # Buffer de 15 min después
            )
            
            # Si no hay citas en ese rango, el slot está disponible
            if not existing_appointments or len(existing_appointments) == 0:
                return True
            
            # Verificar si hay conflictos reales
            for appointment in existing_appointments:
                if appointment.status in [AppointmentStatus.CONFIRMED, AppointmentStatus.SCHEDULED]:
                    # Hay una cita confirmada en ese horario
                    return False
            
            # No hay conflictos con citas confirmadas
            return True
            
        except AttributeError:
            # Si el método no existe en el repositorio, usar verificación simplificada
            try:
                all_appointments = await self._appointment_repo.get_by_date_range(
                    start_date=slot_time,
                    end_date=slot_time + timedelta(minutes=duration_minutes)
                )
                
                # Contar cuántas citas tiene este profesional
                professional_appointments = [
                    apt for apt in all_appointments 
                    if apt.professional_id == professional_id
                    and apt.status in [AppointmentStatus.CONFIRMED, AppointmentStatus.SCHEDULED]
                ]
                
                return len(professional_appointments) == 0
                
            except Exception as inner_e:
                logger.warning(f"Fallback availability check failed: {inner_e}")
                return True  # Asumir disponible si no podemos verificar
            
        except Exception as e:
            logger.error(f"Error checking professional availability: {e}")
            return True  # Default a disponible si hay error
    
    async def _count_professional_appointments(self, professional_id: str) -> int:
        """Cuenta las citas activas/confirmadas de un profesional para balanceamiento"""
        try:
            # Obtener todas las citas del profesional que están activas
            appointments = await self._appointment_repo.find_all()
            
            active_count = 0
            for appointment in appointments:
                if (appointment.professional_id == professional_id and 
                    appointment.status in [AppointmentStatus.CONFIRMED, AppointmentStatus.SCHEDULED]):
                    active_count += 1
            
            logger.debug(f"Professional {professional_id} has {active_count} active appointments")
            return active_count
            
        except Exception as e:
            logger.error(f"Error counting professional appointments: {e}")
            return 0  # Default a 0 si hay error
    
    async def _assign_available_professional(self, service, appointment_datetime):
        """Asigna un profesional disponible con balanceamiento equitativo de carga"""
        try:
            # Obtener profesionales que pueden realizar este servicio
            professionals = await self._professional_repo.get_by_service_id(service.id)
            
            if not professionals:
                # Fallback: buscar por especialidad/nombre del servicio
                professionals = await self._professional_repo.get_by_specialization(service.name)
            
            if not professionals:
                logger.warning(f"No professionals found for service {service.name}")
                return None
            
            # Mapear día de la semana
            weekday_map = {
                0: "monday", 1: "tuesday", 2: "wednesday",
                3: "thursday", 4: "friday", 5: "saturday", 6: "sunday"
            }
            weekday = weekday_map[appointment_datetime.weekday()]
            
            # Lista de profesionales disponibles con su carga de trabajo
            available_professionals = []
            
            # Evaluar cada profesional
            for professional in professionals:
                if not professional.is_active:
                    continue
                
                # Verificar horario de trabajo del profesional
                works_this_day = False
                if hasattr(professional, 'working_hours'):
                    for wh in professional.working_hours:
                        if wh.day.value == weekday and wh.is_available:
                            # Verificar que la hora está dentro del horario (manejar time objects y strings)
                            if isinstance(wh.start_time, str):
                                start_time = datetime.strptime(wh.start_time, "%H:%M").time()
                                end_time = datetime.strptime(wh.end_time, "%H:%M").time()
                            else:
                                # Ya son time objects de Python
                                start_time = wh.start_time
                                end_time = wh.end_time
                            appointment_time_obj = appointment_datetime.time()
                            
                            if start_time <= appointment_time_obj <= end_time:
                                works_this_day = True
                                break
                else:
                    # Si no tiene horarios definidos, asumir disponibilidad estándar
                    if weekday != "sunday" and 8 <= appointment_datetime.hour < 18:
                        works_this_day = True
                
                if not works_this_day:
                    continue
                
                # Verificar que no tenga citas en ese horario
                is_available = await self._check_slot_availability_for_professional(
                    professional.id,
                    appointment_datetime,
                    service.duration_minutes
                )
                
                if is_available:
                    # Contar citas actuales del profesional para balanceamiento
                    workload = await self._count_professional_appointments(professional.id)
                    available_professionals.append((professional, workload))
                    logger.info(f"Professional {professional.name} available with {workload} appointments")
            
            # Si hay profesionales disponibles, seleccionar el que tenga menos carga
            if available_professionals:
                # Ordenar por carga de trabajo (menor a mayor)
                available_professionals.sort(key=lambda x: x[1])
                selected_professional = available_professionals[0][0]
                selected_workload = available_professionals[0][1]
                
                logger.info(f"🎯 BALANCED ASSIGNMENT: Selected {selected_professional.name} (workload: {selected_workload} appointments)")
                return selected_professional
            
            # Si ningún profesional está disponible en el horario exacto,
            # intentar encontrar uno que al menos trabaje ese día (con balanceamiento)
            fallback_professionals = []
            for professional in professionals:
                if professional.is_active:
                    workload = await self._count_professional_appointments(professional.id)
                    fallback_professionals.append((professional, workload))
            
            if fallback_professionals:
                # Seleccionar el que tenga menos carga como fallback
                fallback_professionals.sort(key=lambda x: x[1])
                selected_professional = fallback_professionals[0][0]
                selected_workload = fallback_professionals[0][1]
                
                logger.warning(f"🔄 FALLBACK ASSIGNMENT: {selected_professional.name} (workload: {selected_workload})")
                return selected_professional
            
            logger.error(f"No professional could be assigned for service {service.name} at {appointment_datetime}")
            return None
            
        except Exception as e:
            logger.error(f"Error assigning professional: {e}")
            # Intentar asignación básica como último recurso
            try:
                professionals = await self._professional_repo.get_active_professionals(limit=1)
                if professionals:
                    return professionals[0]
            except:
                pass
            return None
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información sobre esta herramienta para OpenAI Function Calling"""
        return {
            "name": "appointment_scheduling_tool",
            "description": "Herramienta para manejar agendamiento de citas médicas completo",
            "functions": [
                {
                    "name": "create_draft_appointment",
                    "description": "Crea borrador de cita cuando usuario selecciona un servicio específico",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "ID del usuario que agenda la cita"
                            },
                            "service_id": {
                                "type": "string", 
                                "description": "ID del servicio seleccionado"
                            },
                            "service_name": {
                                "type": "string",
                                "description": "Nombre del servicio seleccionado"
                            }
                        },
                        "required": ["user_id", "service_id", "service_name"]
                    }
                },
                {
                    "name": "confirm_appointment",
                    "description": "Confirma una cita asignando fecha, hora y profesional específico",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "string",
                                "description": "ID del borrador de cita a confirmar"
                            },
                            "selected_date": {
                                "type": "string",
                                "description": "Fecha seleccionada en formato YYYY-MM-DD"
                            },
                            "selected_time": {
                                "type": "string",
                                "description": "Hora seleccionada en formato HH:MM"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "ID del usuario que confirma"
                            }
                        },
                        "required": ["appointment_id", "selected_date", "selected_time", "user_id"]
                    }
                }
            ]
        }