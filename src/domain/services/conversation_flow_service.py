"""
AGENDA IA - Conversation Flow Service v2.0 with AI Agent Integration
Clean and simplified version following the PDF workflow + AI Intelligence
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from ..entities.conversation import Conversation, Message, MessageRole, IntentType, ConversationStatus
from ..entities.patient import Patient
from ..entities.appointment import Appointment, AppointmentStatus
from ..value_objects.time_slot import TimeSlot
from ..repositories.user_repository import IUserRepository
from ..repositories.service_repository import IServiceRepository
from ..repositories.professional_repository import IProfessionalRepository
from ..repositories.appointment_repository import IAppointmentRepository
from .availability_service import AvailabilityDomainService
import logging

logger = logging.getLogger(__name__)


class ConversationFlowServiceV2:
    """
    Clean conversation flow service implementing the 6-step process from PDF:
    A) Greeting + Intent Detection
    B) User Identification 
    C) Service Selection
    D) Schedule Search & Proposal
    E) Confirmation
    F) Reminder Preferences
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        service_repository: IServiceRepository,
        professional_repository: IProfessionalRepository,
        availability_service: AvailabilityDomainService,
        appointment_repository: IAppointmentRepository = None,
        shared_ai_agent = None
    ):
        self._user_repo = user_repository
        self._service_repo = service_repository
        self._professional_repo = professional_repository
        self._availability_service = availability_service
        self._appointment_repo = appointment_repository
        
        # Use shared AI Agent or initialize if not provided
        if shared_ai_agent:
            self._ai_agent = shared_ai_agent
            logger.info("✅ AI Agent integrated successfully (shared instance)")
        else:
            # Fallback: Initialize AI Agent
            self._ai_agent = None
            try:
                from ...infrastructure.ai.agenda_ia_agent import AgendaIAAgent
                self._ai_agent = AgendaIAAgent()
                logger.info("✅ AI Agent integrado correctamente")
            except Exception as e:
                logger.warning(f"⚠️ AI Agent not available: {e}")
                logger.info("📋 Falling back to manual intent detection")
    
    async def process_conversation_step(
        self, 
        conversation: Conversation, 
        user_message: str,
        detected_intent: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Main processor following PDF workflow steps A-F with AI enhancement
        """
        try:
            # Check if this is a form registration message FIRST
            if user_message.startswith("FORM_REGISTRATION:"):
                logger.info(f"🔥 FORM DETECTED IN MAIN PROCESSOR: {user_message}")
                return await self._handle_form_registration(conversation, user_message)
            
            current_step = conversation.current_step
            
            # Enhance intent detection with AI Agent if available
            if self._ai_agent and user_message.strip():
                try:
                    ai_analysis = await self._ai_agent.analyze_intent(user_message)
                    # Merge AI analysis with existing detection, prioritizing AI
                    detected_intent = {
                        **detected_intent,
                        **ai_analysis,
                        'ai_enhanced': True
                    }
                    logger.info(f"🤖 AI Enhanced Intent: {ai_analysis['intent']} (confidence: {ai_analysis['confidence']})")
                except Exception as ai_error:
                    logger.warning(f"⚠️ AI analysis failed: {ai_error}")
            
            intent = detected_intent.get('intent', 'OTRO')
            entities = detected_intent.get('entities', {})
            
            logger.info(f"Processing Step: {current_step} | Intent: {intent} | Message: {user_message[:50]}...")
            
            # Route to step handlers with enhanced data
            if current_step == "greeting":
                return await self._step_a_greeting(conversation, user_message, intent, entities)
            elif current_step == "user_identification":
                return await self._step_b_user_identification(conversation, user_message, entities)
            elif current_step == "service_selection":
                return await self._step_c_service_selection(conversation, user_message, entities)
            elif current_step == "appointment_scheduling":
                return await self._step_d_scheduling(conversation, user_message, entities)
            elif current_step == "confirmation":
                return await self._step_e_confirmation(conversation, user_message)
            elif current_step == "reminder_validation":
                return await self._step_f_reminder_validation(conversation, user_message)
            elif current_step == "appointment_management":
                return await self._handle_appointment_management(conversation, intent)
            elif current_step == "cancel_selection":
                return await self._handle_cancel_selection(conversation, user_message)
            elif current_step == "reschedule_selection":
                return await self._handle_reschedule_selection(conversation, user_message)
            elif current_step == "reschedule_appointment_selection":
                return await self._handle_reschedule_appointment_selection(conversation, user_message)
            else:
                return await self._handle_unknown_step(conversation, user_message, intent)
                
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return f"Disculpa, hubo un problema: {str(e)}. ¿Podrías intentar de nuevo?", {}
    
    # STEP A: Greeting + Intent Detection
    async def _step_a_greeting(
        self, 
        conversation: Conversation, 
        user_message: str, 
        intent: str, 
        entities: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """PDF Step A: First contact - Greeting + intent detection"""
        
        # Detect clear intent
        if intent in ['AGENDAR', 'REAGENDAR', 'CANCELAR']:
            conversation.update_step("user_identification")
            conversation.update_context("main_intent", intent)
            
            intent_messages = {
                'AGENDAR': "¡Perfecto! Te ayudo a agendar una cita.",
                'REAGENDAR': "Entendido, te ayudo a reagendar tu cita.",
                'CANCELAR': "Por supuesto, te ayudo a cancelar tu cita."
            }
            
            message = intent_messages.get(intent, "")
            
            # Try to identify user from entities
            user_info = await self._try_identify_user(entities)
            
            if user_info:
                conversation.update_context("user_id", user_info.id)
                conversation.update_context("user_name", user_info.name)
                
                if intent in ['REAGENDAR', 'CANCELAR']:
                    conversation.update_step("appointment_management")
                    return await self._handle_appointment_management(conversation, intent)
                else:
                    conversation.update_step("service_selection")
                    return f"{message} ¡Hola {user_info.name}! ¿Qué servicio necesitas?", {
                        "user_identified": True,
                        "main_intent": intent,
                        "request_services": True
                    }
            else:
                return f"{message} Necesito algunos datos para continuar.", {
                    "main_intent": intent,
                    "needs_registration": True
                }
        
        # Handle casual conversation or greetings
        if intent in ['SALUDO', 'CONVERSACION_CASUAL', 'OTRO']:
            # Generate natural response using AI if available
            if self._ai_agent and entities.get('ai_enhanced'):
                try:
                    # Let AI generate a natural response
                    natural_response = await self._generate_natural_response(user_message, conversation)
                    if natural_response:
                        return natural_response, {
                            "conversation_type": "natural",
                            "ai_enhanced": True
                        }
                except Exception as e:
                    logger.warning(f"AI natural response failed: {e}")
            
            # Fallback natural responses
            casual_responses = self._get_casual_response(user_message)
            if casual_responses:
                return casual_responses, {
                    "conversation_type": "natural"
                }
        
        # NO usar saludos hardcodeados - OpenAI GPT-4o-mini genera TODO
        # Este código NO debería ejecutarse porque OpenAI maneja el saludo inicial
        conversation.update_step("user_identification")
        # Si llegamos aquí, hay un error en la arquitectura
        raise Exception("ERROR: No se debería usar saludo hardcodeado - OpenAI debe manejar TODO")
    
    # STEP B: User Identification
    async def _step_b_user_identification(
        self, 
        conversation: Conversation, 
        user_message: str, 
        entities: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """PDF Step B: User registration or identification"""
        
        # Handle intent if provided
        intent = entities.get('intent', 'OTRO') if isinstance(entities.get('intent'), str) else 'OTRO'
        
        # Handle casual conversation in user identification step too
        if intent in ['SALUDO', 'CONVERSACION_CASUAL', 'OTRO']:
            casual_response = self._get_casual_response(user_message)
            if casual_response:
                return casual_response, {
                    "conversation_type": "natural"
                }
        
        if intent in ['AGENDAR', 'REAGENDAR', 'CANCELAR']:
            conversation.update_context("main_intent", intent)
        
        # Check if this is a form registration message first
        if user_message.startswith("FORM_REGISTRATION:"):
            return await self._handle_form_registration(conversation, user_message)
        
        # Try to identify existing user
        user_info = await self._try_identify_user(entities)
        
        if user_info:
            conversation.update_context("user_id", user_info.id)
            conversation.update_context("user_name", user_info.name)
            conversation.update_step("service_selection")
            
            return f"¡Hola {user_info.name}! Te reconozco. ¿Qué servicio necesitas?", {
                "user_identified": True,
                "request_services": True
            }
        
        # Check for registration data
        registration_data = self._extract_registration_data(user_message, entities)
        
        if self._is_complete_registration(registration_data):
            # Create new user
            try:
                from ...domain.value_objects.email import Email
                from ...domain.value_objects.phone import Phone
                
                new_user = User(
                    id=None,
                    name=registration_data['name'],
                    email=Email(registration_data['email']),
                    phone=Phone(registration_data['phone']),
                    created_at=datetime.utcnow()
                )
                
                created_user = await self._user_repo.create(new_user)
                conversation.update_context("user_id", created_user.id)
                conversation.update_context("user_name", created_user.name)
                conversation.update_step("service_selection")
                
                return (f"¡Registrado exitosamente {created_user.name}!\n\n"
                        f"📧 {created_user.email.value}\n"
                        f"📱 {created_user.phone.value}\n\n"
                        f"¿Qué servicio necesitas?"), {
                    "user_created": True,
                    "user_id": created_user.id,
                    "request_services": True
                }
                
            except ValueError as ve:
                if "already exists" in str(ve):
                    try:
                        from ...domain.value_objects.email import Email
                        existing_user = await self._user_repo.find_by_email(Email(registration_data['email']))
                        if existing_user:
                            conversation.update_context("user_id", existing_user.id)
                            conversation.update_context("user_name", existing_user.name)
                            conversation.update_step("service_selection")
                            
                            return f"¡Hola de nuevo {existing_user.name}! ¿Qué servicio necesitas?", {
                                "user_found": True,
                                "user_id": existing_user.id,
                                "request_services": True
                            }
                    except Exception:
                        pass
                return "El email ya está registrado. ¿Podrías usar uno diferente?", {}
            except Exception as e:
                logger.error(f"Error creating user: {e}")
                return "Hubo un problema al registrarte. Verifica tus datos.", {}
        
        # Request missing information
        missing_fields = []
        if not registration_data.get('name'):
            missing_fields.append("👤 Nombre completo")
        if not registration_data.get('email'):
            missing_fields.append("📧 Correo electrónico")  
        if not registration_data.get('phone'):
            missing_fields.append("📱 Número de celular")
        
        if len(missing_fields) == 3:
            main_intent = conversation.get_context_value('main_intent', 'AGENDAR')
            return f"Para {main_intent.lower()} necesito tu registro rápido:", {
                "show_registration_form": True,
                "form_type": "express_registration"
            }
        elif missing_fields:
            return f"Necesito:\n{chr(10).join(missing_fields)}", {}
        
        return "Proporciona tu nombre, email y celular para continuar.", {}
    
    # STEP C: Service Selection
    async def _step_c_service_selection(
        self, 
        conversation: Conversation, 
        user_message: str, 
        entities: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """PDF Step C: Service selection"""
        
        try:
            services = await self._service_repo.get_active_services()
            
            if not services:
                return "No hay servicios disponibles.", {}
            
            # Check if user is requesting service list
            if self._is_requesting_service_list(user_message):
                services_data = []
                for service in services[:10]:
                    services_data.append({
                        "id": service.id,
                        "name": service.name,
                        "description": service.description,
                        "duration": f"{service.duration_minutes}min",
                        "price": f"${service.price}",
                        "service_type": service.service_type.value,
                        "service_mode": service.service_mode.value
                    })
                
                service_list = "\n".join([
                    f"• **{s.name}** - {s.duration_minutes}min - ${s.price}"
                    for s in services[:5]
                ])
                
                return f"Servicios disponibles:\n\n{service_list}\n\n¿Cuál te interesa?", {
                    "show_interactive_services": True,
                    "services_data": services_data
                }
            
            # Try to match selected service
            selected_service = self._match_service(user_message, services)
            
            if selected_service:
                conversation.update_context("service_id", selected_service.id)
                conversation.update_context("service_name", selected_service.name)
                conversation.update_context("service_duration", selected_service.duration_minutes)
                conversation.update_step("appointment_scheduling")
                
                # Generate availability slots immediately
                available_slots = self._create_availability_slots()
                
                if not available_slots:
                    return "No hay disponibilidad para este servicio.", {}
                
                # Create calendar slots for frontend
                calendar_slots = []
                for slot in available_slots[:20]:
                    calendar_slots.append({
                        "start_time": slot.start_time.isoformat(),
                        "end_time": slot.end_time.isoformat(),
                        "date": slot.start_time.strftime("%Y-%m-%d"),
                        "time": slot.start_time.strftime("%H:%M"),
                        "available": True
                    })
                
                conversation.update_context("available_slots", calendar_slots)
                
                return (f"✅ **Servicio:** {selected_service.name}\n"
                        f"⏱️ **Duración:** {selected_service.duration_minutes}min\n\n"
                        f"📅 **¿Cuándo te conviene?**"), {
                    "service_selected": True,
                    "service_id": selected_service.id,
                    "service_name": selected_service.name,
                    "show_calendar": True,
                    "available_slots": calendar_slots
                }
            
            return "No identifiqué ese servicio. ¿Podrías elegir de la lista?", {
                "request_services": True
            }
            
        except Exception as e:
            logger.error(f"Error in service selection: {e}")
            return "Hubo un problema consultando servicios.", {}
    
    # STEP D: Scheduling
    async def _step_d_scheduling(
        self, 
        conversation: Conversation, 
        user_message: str, 
        entities: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """PDF Step D: Schedule search and slot proposal"""
        
        try:
            service_id = conversation.get_context_value("service_id")
            if not service_id:
                conversation.update_step("service_selection")
                return "Primero selecciona un servicio.", {"request_services": True}
            
            # Check for calendar slot selection
            if user_message.startswith("slot:"):
                slot_time = user_message.replace("slot:", "")
                conversation.update_step("confirmation")
                conversation.update_context("selected_slot", slot_time)
                
                slot_datetime = datetime.fromisoformat(slot_time)
                date_str = slot_datetime.strftime("%A %d de %B a las %H:%M")
                
                return f"📅 **Horario seleccionado:**\n{date_str}\n\n¿Confirmas?", {
                    "slot_selected": True,
                    "selected_slot": slot_time,
                    "show_confirmation": True
                }
            
            # Generate availability slots
            available_slots = self._create_availability_slots()
            
            if not available_slots:
                return "No hay disponibilidad. ¿Prefieres otros horarios?", {}
            
            # Show options
            options_text = "🗓️ **Horarios disponibles:**\n\n"
            
            for i, slot in enumerate(available_slots[:5], 1):
                date_str = slot.start_time.strftime("%A %d de %B")
                time_str = slot.start_time.strftime("%H:%M")
                options_text += f"**[{i}]** {date_str} a las {time_str}\n"
            
            options_text += f"\n**[{len(available_slots[:5]) + 1}]** 🔄 Ninguna me sirve\n"
            options_text += f"**[{len(available_slots[:5]) + 2}]** ↩️ Volver al menú\n\n"
            options_text += "Escribe el número o usa el calendario:"
            
            # Store slots and show calendar
            calendar_slots = []
            for slot in available_slots[:20]:
                calendar_slots.append({
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "date": slot.start_time.strftime("%Y-%m-%d"),
                    "time": slot.start_time.strftime("%H:%M"),
                    "available": True
                })
            
            conversation.update_context("available_slots", calendar_slots)
            conversation.update_step("confirmation")
            
            return options_text, {
                "slots_presented": True,
                "show_calendar": True,
                "available_slots": calendar_slots
            }
            
        except Exception as e:
            logger.error(f"Error in scheduling: {e}")
            return "Problema buscando horarios.", {}
    
    # STEP E: Confirmation
    async def _step_e_confirmation(
        self, 
        conversation: Conversation, 
        user_message: str
    ) -> Tuple[str, Dict[str, Any]]:
        """PDF Step E: Appointment confirmation"""
        
        user_choice = user_message.strip()
        available_slots = conversation.get_context_value("available_slots", [])
        max_options = len(available_slots)
        
        # Handle "None works"
        none_works_option = str(max_options + 1)
        if user_choice == none_works_option or "ninguna" in user_message.lower():
            conversation.update_step("appointment_scheduling")
            return "¿Qué prefieres?\n• Próxima semana\n• Próximo mes\n• Mañana\n• Tarde", {}
        
        # Handle "Back to menu" 
        menu_option = str(max_options + 2)
        if user_choice == menu_option or "menú" in user_message.lower():
            conversation.update_step("greeting")
            return "¿En qué más puedo ayudarte?", {}
        
        # Handle slot selection
        try:
            choice_num = int(user_choice)
            if 1 <= choice_num <= max_options:
                selected_slot = available_slots[choice_num - 1]
                
                # Create appointment immediately
                appointment_data = {
                    "user_id": conversation.get_context_value("user_id"),
                    "service_id": conversation.get_context_value("service_id"),
                    "start_time": selected_slot["start_time"],
                    "duration_minutes": conversation.get_context_value("service_duration", 30),
                    "service_name": conversation.get_context_value("service_name"),
                    "service_mode": "presential"
                }
                
                success = await self._create_appointment(appointment_data)
                
                if success:
                    conversation.complete_conversation(success=True)
                    start_time = datetime.fromisoformat(selected_slot["start_time"])
                    date_str = start_time.strftime("%A %d de %B a las %H:%M")
                    
                    return (f"🎉 **¡Cita confirmada!**\n\n"
                            f"📅 {date_str}\n"
                            f"🏥 {conversation.get_context_value('service_name')}\n"
                            f"👤 {conversation.get_context_value('user_name')}\n\n"
                            f"Te enviaremos recordatorios.\n\n"
                            f"¿Algo más en lo que pueda ayudarte?"), {
                        "appointment_confirmed": True,
                        "appointment_data": appointment_data
                    }
                else:
                    return "❌ Error confirmando cita. Intenta de nuevo.", {}
        
        except ValueError:
            pass
        
        return f"Elige un número del 1 al {max_options + 2}.", {}
    
    # STEP F: Reminder Validation (simplified)
    async def _step_f_reminder_validation(
        self, 
        conversation: Conversation, 
        user_message: str
    ) -> Tuple[str, Dict[str, Any]]:
        """PDF Step F: Reminder preferences (currently simplified)"""
        
        # This step is now handled in Step E for simplicity
        return "Proceso completado.", {}
    
    # Helper Methods
    async def _try_identify_user(self, entities: Dict[str, Any]) -> Optional[User]:
        """Try to identify user from entities"""
        try:
            if entities.get('email'):
                from ...domain.value_objects.email import Email
                user = await self._user_repo.get_by_email(Email(entities['email']))
                if user:
                    return user
            
            if entities.get('phone'):
                from ...domain.value_objects.phone import Phone
                user = await self._user_repo.get_by_phone(Phone(entities['phone']))
                if user:
                    return user
            
            return None
        except Exception as e:
            logger.error(f"Error identifying user: {e}")
            return None
    
    def _extract_registration_data(self, message: str, entities: Dict[str, Any]) -> Dict[str, str]:
        """Extract registration data from message"""
        import re
        
        data = {}
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
        if email_match:
            data['email'] = email_match.group()
        
        # Extract phone
        phone_patterns = [
            r'\+[0-9]{1,3}[0-9]{7,12}',
            r'(\+?57\s?)?[3][0-9]{9}',
            r'\b[0-9]{10,13}\b'
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, message.replace(' ', '').replace('-', ''))
            if phone_match:
                raw_phone = phone_match.group()
                if raw_phone.startswith('+'):
                    data['phone'] = raw_phone
                else:
                    clean_digits = re.sub(r'[^\d]', '', raw_phone)
                    if len(clean_digits) == 10 and clean_digits.startswith('3'):
                        data['phone'] = f"+57{clean_digits}"
                    elif len(clean_digits) == 12 and clean_digits.startswith('57'):
                        data['phone'] = f"+{clean_digits}"
                    else:
                        data['phone'] = f"+57{clean_digits}"
                break
        
        # Extract name
        if email_match or 'phone' in data:
            clean_message = message
            if email_match:
                clean_message = clean_message.replace(email_match.group(), '')
            if 'phone' in data:
                clean_message = clean_message.replace(phone_match.group() if phone_match else '', '')
            
            # Remove common phrases
            phrases_to_remove = ['mi nombre es', 'me llamo', 'soy', 'mi correo es', 'mi email es', 'mi teléfono es']
            for phrase in phrases_to_remove:
                clean_message = clean_message.replace(phrase, ' ')
            
            clean_message = re.sub(r'\s+', ' ', clean_message).strip()
            words = clean_message.split()
            
            exclude_words = ['quiero', 'agendar', 'cita', 'necesito', 'correo', 'email', 'celular', 'telefono']
            potential_names = [
                w.strip(',') for w in words 
                if w.strip(',').isalpha() and len(w.strip(',')) > 1 and w.strip(',').lower() not in exclude_words
            ]
            
            if potential_names:
                data['name'] = ' '.join(potential_names[:3])
        
        return data
    
    def _is_complete_registration(self, data: Dict[str, str]) -> bool:
        """Check if registration data is complete"""
        return all(key in data and data[key] for key in ['name', 'email', 'phone'])
    
    def _is_requesting_service_list(self, message: str) -> bool:
        """Check if user is requesting service list"""
        phrases = ['que servicios', 'qué servicios', 'servicios disponibles', 'que tienes', 'opciones']
        return any(phrase in message.lower() for phrase in phrases)
    
    def _match_service(self, message: str, services: List[Any]) -> Optional[Any]:
        """Match user input with services"""
        message_lower = message.lower().strip()
        
        # Exact match
        for service in services:
            if service.name.lower() == message_lower:
                return service
        
        # Partial match
        for service in services:
            if message_lower in service.name.lower() or service.name.lower() in message_lower:
                return service
        
        # Keyword match
        keywords = {
            'psicolog': 'psicolog',
            'odont': 'odont', 
            'medic': 'medic',
            'masaje': 'masaje',
            'belleza': 'belleza',
            'cabello': 'cabello'
        }
        
        for keyword, service_keyword in keywords.items():
            if keyword in message_lower:
                for service in services:
                    if service_keyword in service.name.lower():
                        return service
        
        return None
    
    def _create_availability_slots(self):
        """Create availability slots (mock for now)"""
        from datetime import timedelta
        
        slots = []
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = base_date + timedelta(days=1)
        
        # Generate 5 slots
        slot_times = [(9, 0), (10, 0), (11, 0), (14, 0), (15, 0)]
        
        for hour, minute in slot_times:
            slot_start = tomorrow.replace(hour=hour, minute=minute)
            slot_end = slot_start + timedelta(minutes=30)
            time_slot = TimeSlot(slot_start, slot_end)
            slots.append(time_slot)
        
        return slots
    
    async def _create_appointment(self, appointment_data: Dict[str, Any]) -> bool:
        """Create appointment in database"""
        try:
            import secrets
            
            start_time = datetime.fromisoformat(appointment_data["start_time"])
            duration_minutes = appointment_data.get("duration_minutes", 30)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            time_slot = TimeSlot(start_time=start_time, end_time=end_time)
            
            mode = AppointmentMode.VIRTUAL if appointment_data.get("service_mode") == "virtual" else AppointmentMode.PRESENTIAL
            
            appointment = Appointment(
                id=None,
                appointment_id=f"APT-{secrets.token_urlsafe(8)}",
                user_id=appointment_data["user_id"],
                service_id=appointment_data["service_id"],
                time_slot=time_slot,
                mode=mode,
                status=AppointmentStatus.SCHEDULED,
                service_name=appointment_data.get("service_name"),
                duration_minutes=duration_minutes,
                reminder_enabled=True,
                source="web_chat",
                created_at=datetime.utcnow()
            )
            
            created_appointment = await self._appointment_repo.create(appointment)
            
            if created_appointment and created_appointment.id:
                logger.info(f"✅ Appointment created: {created_appointment.id}")
                return True
            else:
                logger.error("❌ Failed to create appointment")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating appointment: {e}")
            return False
    
    async def _handle_appointment_management(self, conversation: Conversation, intent: str) -> Tuple[str, Dict[str, Any]]:
        """Handle REAGENDAR and CANCELAR"""
        try:
            user_id = conversation.get_context_value("user_id")
            if not user_id:
                return "Necesito identificarte primero. ¿Cuál es tu email o teléfono?", {
                    "needs_identification": True
                }
            
            # Get user's appointments
            user_appointments = await self._appointment_repo.get_by_user_id(user_id)
            active_appointments = [
                apt for apt in user_appointments 
                if apt.status.value in ["scheduled", "confirmed"]
            ]
            
            if not active_appointments:
                return ("No tienes citas programadas para gestionar.\n\n"
                       "¿Te gustaría agendar una nueva cita?"), {
                    "no_appointments": True,
                    "suggest_booking": True
                }
            
            if intent == "CANCELAR":
                return await self._handle_cancel_appointments(conversation, active_appointments)
            elif intent == "REAGENDAR":
                return await self._handle_reschedule_appointments(conversation, active_appointments)
            else:
                return await self._show_appointment_options(conversation, active_appointments, intent)
                
        except Exception as e:
            logger.error(f"❌ Error in appointment management: {e}")
            return "Hubo un error al gestionar tu cita. Intenta de nuevo.", {}
    
    async def _handle_cancel_appointments(self, conversation: Conversation, appointments: List[Appointment]) -> Tuple[str, Dict[str, Any]]:
        """Handle appointment cancellation"""
        try:
            if len(appointments) == 1:
                # Single appointment - confirm cancellation
                apt = appointments[0]
                conversation.update_context("appointment_to_cancel", apt.id)
                
                start_time = apt.time_slot.start_time.strftime("%A %d de %B a las %H:%M")
                
                return (f"¿Confirmas que deseas cancelar esta cita?\n\n"
                        f"📅 {start_time}\n"
                        f"🏥 {apt.service_name or 'Servicio'}\n\n"
                        f"Responde 'SÍ' para cancelar o 'NO' para mantenerla."), {
                    "confirm_cancellation": True,
                    "appointment_id": apt.id
                }
            
            # Multiple appointments - show list
            appointments_text = "Tienes las siguientes citas programadas:\n\n"
            for i, apt in enumerate(appointments[:5], 1):
                start_time = apt.time_slot.start_time.strftime("%d/%m a las %H:%M")
                appointments_text += f"**[{i}]** {start_time} - {apt.service_name or 'Servicio'}\n"
            
            appointments_text += f"\n**[{len(appointments[:5]) + 1}]** ↩️ Cancelar operación\n"
            appointments_text += "\n¿Cuál deseas cancelar? (Escribe el número)"
            
            # Store appointments in context
            conversation.update_context("appointments_list", [apt.id for apt in appointments[:5]])
            conversation.update_step("cancel_selection")
            
            return appointments_text, {
                "show_appointment_list": True,
                "appointments_data": [
                    {
                        "id": apt.id,
                        "date": apt.time_slot.start_time.strftime("%Y-%m-%d"),
                        "time": apt.time_slot.start_time.strftime("%H:%M"),
                        "service": apt.service_name or "Servicio"
                    }
                    for apt in appointments[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling cancel appointments: {e}")
            return "Hubo un error al cargar tus citas. Intenta de nuevo.", {}
    
    async def _handle_reschedule_appointments(self, conversation: Conversation, appointments: List[Appointment]) -> Tuple[str, Dict[str, Any]]:
        """Handle appointment rescheduling"""
        try:
            if len(appointments) == 1:
                # Single appointment - show new slots
                apt = appointments[0]
                conversation.update_context("appointment_to_reschedule", apt.id)
                conversation.update_context("service_id", apt.service_id)
                conversation.update_context("service_duration", apt.duration_minutes)
                
                # Generate new available slots
                available_slots = self._create_availability_slots()
                
                if not available_slots:
                    return "No hay horarios disponibles para reagendar.", {}
                
                # Show current appointment and new options
                current_time = apt.time_slot.start_time.strftime("%A %d de %B a las %H:%M")
                
                options_text = f"📅 **Cita actual:** {current_time}\n\n"
                options_text += "🔄 **Nuevos horarios disponibles:**\n\n"
                
                for i, slot in enumerate(available_slots[:5], 1):
                    date_str = slot.start_time.strftime("%A %d de %B")
                    time_str = slot.start_time.strftime("%H:%M")
                    options_text += f"**[{i}]** {date_str} a las {time_str}\n"
                
                options_text += f"\n**[{len(available_slots[:5]) + 1}]** ↩️ Cancelar reagendamiento\n"
                options_text += "\n¿A cuál horario deseas cambiar? (Escribe el número)"
                
                # Create calendar slots for frontend
                calendar_slots = []
                for slot in available_slots[:20]:
                    calendar_slots.append({
                        "start_time": slot.start_time.isoformat(),
                        "end_time": slot.end_time.isoformat(),
                        "date": slot.start_time.strftime("%Y-%m-%d"),
                        "time": slot.start_time.strftime("%H:%M"),
                        "available": True
                    })
                
                conversation.update_context("available_slots", calendar_slots)
                conversation.update_step("reschedule_selection")
                
                return options_text, {
                    "show_reschedule_options": True,
                    "show_calendar": True,
                    "available_slots": calendar_slots,
                    "current_appointment": {
                        "id": apt.id,
                        "date": apt.time_slot.start_time.strftime("%Y-%m-%d"),
                        "time": apt.time_slot.start_time.strftime("%H:%M"),
                        "service": apt.service_name or "Servicio"
                    }
                }
            
            # Multiple appointments - show list first
            appointments_text = "Tienes las siguientes citas programadas:\n\n"
            for i, apt in enumerate(appointments[:5], 1):
                start_time = apt.time_slot.start_time.strftime("%d/%m a las %H:%M")
                appointments_text += f"**[{i}]** {start_time} - {apt.service_name or 'Servicio'}\n"
            
            appointments_text += f"\n**[{len(appointments[:5]) + 1}]** ↩️ Cancelar operación\n"
            appointments_text += "\n¿Cuál deseas reagendar? (Escribe el número)"
            
            conversation.update_context("appointments_list", [apt.id for apt in appointments[:5]])
            conversation.update_step("reschedule_appointment_selection")
            
            return appointments_text, {
                "show_appointment_list": True,
                "appointments_data": [
                    {
                        "id": apt.id,
                        "date": apt.time_slot.start_time.strftime("%Y-%m-%d"),
                        "time": apt.time_slot.start_time.strftime("%H:%M"),
                        "service": apt.service_name or "Servicio"
                    }
                    for apt in appointments[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling reschedule appointments: {e}")
            return "Hubo un error al cargar tus citas. Intenta de nuevo.", {}
    
    async def _show_appointment_options(self, conversation: Conversation, appointments: List[Appointment], intent: str) -> Tuple[str, Dict[str, Any]]:
        """Show appointment management options when intent is unclear"""
        try:
            appointments_text = "Tienes las siguientes citas programadas:\n\n"
            for i, apt in enumerate(appointments[:5], 1):
                start_time = apt.time_slot.start_time.strftime("%d/%m a las %H:%M")
                status_emoji = "✅" if apt.status == AppointmentStatus.CONFIRMED else "📅"
                appointments_text += f"{status_emoji} **[{i}]** {start_time} - {apt.service_name or 'Servicio'}\n"
            
            appointments_text += "\n¿Qué deseas hacer?\n"
            appointments_text += "• **CANCELAR** una cita\n"
            appointments_text += "• **REAGENDAR** una cita\n"
            appointments_text += "• **VER DETALLES** de una cita\n"
            appointments_text += "• **VOLVER** al menú principal"
            
            return appointments_text, {
                "show_appointment_management": True,
                "appointments_data": [
                    {
                        "id": apt.id,
                        "date": apt.time_slot.start_time.strftime("%Y-%m-%d"),
                        "time": apt.time_slot.start_time.strftime("%H:%M"),
                        "service": apt.service_name or "Servicio",
                        "status": apt.status.value
                    }
                    for apt in appointments[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error showing appointment options: {e}")
            return "Hubo un error al cargar tus citas. Intenta de nuevo.", {}
    
    async def _handle_cancel_selection(self, conversation: Conversation, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle cancellation selection step"""
        try:
            user_choice = user_message.strip()
            appointments_list = conversation.get_context_value("appointments_list", [])
            
            # Handle cancellation
            cancel_option = str(len(appointments_list) + 1)
            if user_choice == cancel_option or "cancelar" in user_message.lower():
                conversation.update_step("greeting")
                return "Operación cancelada. ¿En qué más puedo ayudarte?", {}
            
            # Handle appointment selection
            try:
                choice_num = int(user_choice)
                if 1 <= choice_num <= len(appointments_list):
                    appointment_id = appointments_list[choice_num - 1]
                    
                    # Update appointment status to cancelled
                    appointment = await self._appointment_repo.get_by_id(appointment_id)
                    if appointment:
                        appointment.status = AppointmentStatus.CANCELLED
                        await self._appointment_repo.update(appointment)
                        
                        conversation.update_step("greeting")
                        start_time = appointment.time_slot.start_time.strftime("%A %d de %B a las %H:%M")
                        
                        return (f"✅ **Cita cancelada exitosamente**\n\n"
                                f"📅 {start_time}\n"
                                f"🏥 {appointment.service_name or 'Servicio'}\n\n"
                                f"¿Algo más en lo que pueda ayudarte?"), {
                            "appointment_cancelled": True,
                            "cancelled_appointment": appointment_id
                        }
                    else:
                        return "No se pudo encontrar la cita. Intenta de nuevo.", {}
                        
            except ValueError:
                pass
            
            return f"Por favor, elige un número del 1 al {len(appointments_list) + 1}.", {}
            
        except Exception as e:
            logger.error(f"❌ Error handling cancel selection: {e}")
            return "Hubo un error al cancelar la cita. Intenta de nuevo.", {}
    
    async def _handle_reschedule_selection(self, conversation: Conversation, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle rescheduling selection step"""
        try:
            user_choice = user_message.strip()
            available_slots = conversation.get_context_value("available_slots", [])
            appointment_to_reschedule = conversation.get_context_value("appointment_to_reschedule")
            
            # Handle cancellation
            cancel_option = str(len(available_slots[:5]) + 1)
            if user_choice == cancel_option or "cancelar" in user_message.lower():
                conversation.update_step("greeting")
                return "Reagendamiento cancelado. ¿En qué más puedo ayudarte?", {}
            
            # Handle slot selection from calendar
            if user_message.startswith("slot:"):
                slot_time = user_message.replace("slot:", "")
                selected_slot_time = slot_time
            else:
                # Handle numeric selection
                try:
                    choice_num = int(user_choice)
                    if 1 <= choice_num <= len(available_slots[:5]):
                        selected_slot_time = available_slots[choice_num - 1]["start_time"]
                    else:
                        return f"Por favor, elige un número del 1 al {len(available_slots[:5]) + 1}.", {}
                except ValueError:
                    return f"Por favor, elige un número del 1 al {len(available_slots[:5]) + 1}.", {}
            
            # Update appointment with new time slot
            appointment = await self._appointment_repo.get_by_id(appointment_to_reschedule)
            if appointment:
                new_start_time = datetime.fromisoformat(selected_slot_time)
                new_end_time = new_start_time + timedelta(minutes=appointment.duration_minutes)
                appointment.time_slot = TimeSlot(new_start_time, new_end_time)
                
                updated_appointment = await self._appointment_repo.update(appointment)
                
                if updated_appointment:
                    conversation.update_step("greeting")
                    date_str = new_start_time.strftime("%A %d de %B a las %H:%M")
                    
                    return (f"✅ **Cita reagendada exitosamente**\n\n"
                            f"📅 Nuevo horario: {date_str}\n"
                            f"🏥 {appointment.service_name or 'Servicio'}\n\n"
                            f"Te enviaremos recordatorios con el nuevo horario.\n\n"
                            f"¿Algo más en lo que pueda ayudarte?"), {
                        "appointment_rescheduled": True,
                        "rescheduled_appointment": appointment_to_reschedule,
                        "new_time": selected_slot_time
                    }
                else:
                    return "Error al reagendar la cita. Intenta de nuevo.", {}
            else:
                return "No se pudo encontrar la cita. Intenta de nuevo.", {}
            
        except Exception as e:
            logger.error(f"❌ Error handling reschedule selection: {e}")
            return "Hubo un error al reagendar la cita. Intenta de nuevo.", {}
    
    async def _handle_reschedule_appointment_selection(self, conversation: Conversation, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle appointment selection for rescheduling when multiple appointments exist"""
        try:
            user_choice = user_message.strip()
            appointments_list = conversation.get_context_value("appointments_list", [])
            
            # Handle cancellation
            cancel_option = str(len(appointments_list) + 1)
            if user_choice == cancel_option or "cancelar" in user_message.lower():
                conversation.update_step("greeting")
                return "Operación cancelada. ¿En qué más puedo ayudarte?", {}
            
            # Handle appointment selection
            try:
                choice_num = int(user_choice)
                if 1 <= choice_num <= len(appointments_list):
                    appointment_id = appointments_list[choice_num - 1]
                    appointment = await self._appointment_repo.get_by_id(appointment_id)
                    
                    if appointment:
                        # Set up rescheduling for selected appointment
                        conversation.update_context("appointment_to_reschedule", appointment.id)
                        conversation.update_context("service_id", appointment.service_id)
                        conversation.update_context("service_duration", appointment.duration_minutes)
                        
                        # Generate new available slots
                        available_slots = self._create_availability_slots()
                        
                        if not available_slots:
                            return "No hay horarios disponibles para reagendar.", {}
                        
                        # Show current appointment and new options
                        current_time = appointment.time_slot.start_time.strftime("%A %d de %B a las %H:%M")
                        
                        options_text = f"📅 **Cita a reagendar:** {current_time}\n\n"
                        options_text += "🔄 **Nuevos horarios disponibles:**\n\n"
                        
                        for i, slot in enumerate(available_slots[:5], 1):
                            date_str = slot.start_time.strftime("%A %d de %B")
                            time_str = slot.start_time.strftime("%H:%M")
                            options_text += f"**[{i}]** {date_str} a las {time_str}\n"
                        
                        options_text += f"\n**[{len(available_slots[:5]) + 1}]** ↩️ Cancelar reagendamiento\n"
                        options_text += "\n¿A cuál horario deseas cambiar? (Escribe el número)"
                        
                        # Create calendar slots for frontend
                        calendar_slots = []
                        for slot in available_slots[:20]:
                            calendar_slots.append({
                                "start_time": slot.start_time.isoformat(),
                                "end_time": slot.end_time.isoformat(),
                                "date": slot.start_time.strftime("%Y-%m-%d"),
                                "time": slot.start_time.strftime("%H:%M"),
                                "available": True
                            })
                        
                        conversation.update_context("available_slots", calendar_slots)
                        conversation.update_step("reschedule_selection")
                        
                        return options_text, {
                            "show_reschedule_options": True,
                            "show_calendar": True,
                            "available_slots": calendar_slots,
                            "current_appointment": {
                                "id": appointment.id,
                                "date": appointment.time_slot.start_time.strftime("%Y-%m-%d"),
                                "time": appointment.time_slot.start_time.strftime("%H:%M"),
                                "service": appointment.service_name or "Servicio"
                            }
                        }
                    else:
                        return "No se pudo encontrar la cita. Intenta de nuevo.", {}
                        
            except ValueError:
                pass
            
            return f"Por favor, elige un número del 1 al {len(appointments_list) + 1}.", {}
            
        except Exception as e:
            logger.error(f"❌ Error handling reschedule appointment selection: {e}")
            return "Hubo un error al procesar la selección. Intenta de nuevo.", {}

    async def _handle_unknown_step(self, conversation: Conversation, user_message: str, intent: str) -> Tuple[str, Dict[str, Any]]:
        """Handle unknown steps"""
        conversation.update_step("greeting")
        return "No estoy seguro de cómo ayudarte. ¿Deseas agendar una cita?", {}
    
    async def _handle_form_registration(self, conversation: Conversation, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle structured form registration data"""
        try:
            logger.info(f"🔥 FORM REGISTRATION DETECTED: {user_message}")
            
            # Extract data after the prefix
            form_part = user_message[len("FORM_REGISTRATION:"):]
            parts = form_part.split("|")
            
            if len(parts) != 3:
                return "Error en los datos del formulario. Intenta de nuevo.", {}
            
            name, email, phone = [part.strip() for part in parts]
            
            if not all([name, email, phone]):
                return "Faltan datos en el formulario. Intenta de nuevo.", {}
            
            logger.info(f"🔥 PROCESSING FORM DATA: name={name}, email={email}, phone={phone}")
            
            # Create user directly
            from ...domain.value_objects.email import Email
            from ...domain.value_objects.phone import Phone
            
            new_user = User(
                id=None,
                name=name,
                email=Email(email),
                phone=Phone(phone),
                created_at=datetime.utcnow()
            )
            
            try:
                created_user = await self._user_repo.create(new_user)
                
                # Update conversation context
                conversation.update_context("user_id", created_user.id)
                conversation.update_context("user_name", created_user.name)
                conversation.update_context("user_email", created_user.email.value)
                conversation.update_context("user_phone", created_user.phone.value)
                conversation.update_context("user_created", True)
                conversation.update_context("registration_method", "structured_form")
                conversation.update_step("service_selection")
                
                logger.info(f"✅ FORM USER CREATED: {created_user.id}")
                
                success_message = f"✅ ¡Registro exitoso {created_user.name}!\n\n📧 {created_user.email.value}\n📱 {created_user.phone.value}\n\n¿Qué servicio necesitas?"
                
                return success_message, {
                    "user_created": True,
                    "user_id": created_user.id,
                    "request_services": True,
                    "show_interactive_services": True,  # Trigger service display
                    "registration_method": "structured_form"
                }
                
            except ValueError as ve:
                if "already exists" in str(ve).lower():
                    # Handle existing user
                    existing_user = await self._user_repo.find_by_email(Email(email))
                    if existing_user:
                        conversation.update_context("user_id", existing_user.id)
                        conversation.update_context("user_name", existing_user.name)
                        conversation.update_context("user_email", existing_user.email.value)
                        conversation.update_context("user_phone", existing_user.phone.value)
                        conversation.update_context("user_found", True)
                        conversation.update_context("registration_method", "structured_form")
                        conversation.update_step("service_selection")
                        
                        success_message = f"¡Hola de nuevo {existing_user.name}! 😊\n\n¿Qué servicio necesitas?"
                        
                        return success_message, {
                            "user_found": True,
                            "user_id": existing_user.id,
                            "request_services": True,
                            "show_interactive_services": True,
                            "registration_method": "structured_form"
                        }
                    else:
                        return "El correo ya está registrado pero no se pudo encontrar el usuario.", {}
                else:
                    logger.error(f"❌ User creation error: {ve}")
                    return f"Error en el registro: {str(ve)}", {}
                    
        except Exception as e:
            logger.error(f"❌ FORM REGISTRATION ERROR: {e}")
            return "Hubo un problema con el registro. Por favor, verifica tus datos e intenta de nuevo.", {}
    
    async def _generate_natural_response(self, user_message: str, conversation: Conversation) -> Optional[str]:
        """Generate natural response using AI agent"""
        try:
            if not self._ai_agent:
                return None
            
            # Create context for natural conversation
            context_messages = [
                {
                    "role": "user", 
                    "content": user_message
                }
            ]
            
            # Get AI response using the agent's method
            if hasattr(self._ai_agent, 'generate_natural_response'):
                response = await self._ai_agent.generate_natural_response(context_messages)
                return response
            elif hasattr(self._ai_agent, 'chat'):
                response = await self._ai_agent.chat(context_messages)
                return response.get('content') or response.get('message')
            
        except Exception as e:
            logger.warning(f"Error generating natural response: {e}")
            return None
        
        return None
    
    def _get_casual_response(self, user_message: str) -> Optional[str]:
        """ELIMINADO - OpenAI GPT-4o-mini es el ÚNICO cerebro que debe responder"""
        # NUNCA usar respuestas hardcodeadas - SOLO OpenAI GPT-4o-mini controla TODO
        return None