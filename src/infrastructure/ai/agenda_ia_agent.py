# -*- coding: utf-8 -*-
"""
AGENDA IA - Agente Inteligente Principal
Implementación unificada usando OpenAI GPT-4o-mini con Function Calling
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
import logging
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AgentContext:
    """Contexto y memoria del agente para cada usuario"""
    
    def __init__(self, user_id: Optional[str] = None, conversation_id: Optional[str] = None):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.conversation_history = []
        self.current_step = "greeting"
        self.context_data = {
            "main_intent": None,
            "user_data": {},
            "service_selected": None,
            "appointment_data": {},
            "preferences": {}
        }
    
    def add_message(self, role: str, content: str):
        """Añade mensaje al historial"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def update_context(self, key: str, value: Any):
        """Actualiza datos del contexto"""
        self.context_data[key] = value
    
    def get_context(self, key: str, default=None):
        """Obtiene datos del contexto"""
        return self.context_data.get(key, default)


class AgendaIAAgent:
    """
    Agente IA Principal para AGENDA IA

    Maneja todo el flujo conversacional usando:
    - OpenAI GPT-4o-mini para procesamiento de lenguaje natural
    - Function Calling para herramientas específicas
    - Detección automática de intenciones y datos
    - Gestión inteligente del contexto conversacional
    """
    
    def __init__(self, user_repo=None, conversation_repo=None, service_repo=None, professional_repo=None, appointment_repo=None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no encontrada en variables de entorno")
        
        # Create OpenAI client without proxy configuration to avoid conflicts
        self.client = OpenAI(
            api_key=self.api_key,
            http_client=None  # Let OpenAI create its own http client
        )
        self.model_name = "gpt-4o-mini"
        
        # Inicializar herramientas AI si los repositorios están disponibles
        self.tools_available = False
        if user_repo and conversation_repo:
            from ...domain.services.ai_tools.express_registration_tool import ExpressRegistrationTool
            self.registration_tool = ExpressRegistrationTool(user_repo, conversation_repo)
            
            # Inicializar herramienta de verificación de usuario
            from ...domain.services.ai_tools.user_verification_tool import UserVerificationTool
            self.verification_tool = UserVerificationTool(user_repo)
            logger.info("[SUCCESS] User verification tool initialized")
            
            # Inicializar herramienta de servicios si tenemos los repositorios
            if service_repo and professional_repo:
                from ...domain.services.ai_tools.service_consultation_tool import ServiceConsultationTool  
                self.service_tool = ServiceConsultationTool(service_repo, professional_repo)
                logger.info("[SUCCESS] Service consultation tool initialized")
            else:
                self.service_tool = None
                logger.info("[WARNING] Service tool not initialized - service/professional repos not provided")
            
            # Inicializar herramienta de agendamiento si tenemos todos los repositorios
            if service_repo and professional_repo and appointment_repo:
                from ...domain.services.ai_tools.appointment_scheduling_tool import AppointmentSchedulingTool
                self.appointment_tool = AppointmentSchedulingTool(
                    service_repo, professional_repo, user_repo, appointment_repo
                )
                logger.info("[SUCCESS] Appointment scheduling tool initialized")
            else:
                self.appointment_tool = None
                logger.info("[WARNING] Appointment tool not initialized - missing repositories")
            
            self.tools_available = True
            logger.info("[SUCCESS] AI Tools initialized - Registration, Service and Appointment tools available")
        else:
            self.registration_tool = None
            self.verification_tool = None
            self.service_tool = None
            self.appointment_tool = None
            logger.info("[WARNING] AI Tools not initialized - repositories not provided")
        
        self.instructions = """
Eres un asistente de agendamiento inteligente y conversacional. Tu objetivo principal es ayudar a los usuarios a agendar citas médicas de forma natural y eficiente.

🎯 OBJETIVO PRINCIPAL:
Facilitar el agendamiento de citas médicas manteniendo una conversación natural y amigable.

REGLAS DE CONVERSACIÓN:
1. Mantén un tono amigable y profesional
2. Sé proactivo cuando detectes intención de agendar
3. Guía sutilmente hacia el agendamiento cuando sea apropiado
4. Responde naturalmente a conversaciones casuales
5. NO repitas saludos o información ya compartida
6. Mantén continuidad y coherencia en la conversación

🔧 FLUJO OPTIMIZADO DE AGENDAMIENTO:

1️⃣ DETECCIÓN AUTOMÁTICA:
   - Detecta email/teléfono → Verifica inmediatamente en BD
   - Si existe → Saluda por nombre y ofrece servicios
   - Si no existe → Pre-llena formulario con datos detectados

2️⃣ PALABRAS CLAVE DE AGENDAMIENTO:
   - "cita", "agendar", "reservar", "turno", "consulta"
   - "necesito ver a un doctor", "quiero programar"
   - Al detectarlas → Activa flujo de agendamiento

3️⃣ PROCESO SIMPLIFICADO:
   Usuario menciona agendar → Verificar/Registrar → Mostrar servicios → Seleccionar horario → Confirmar

📋 HERRAMIENTAS Y SU USO:

✅ USA AUTOMÁTICAMENTE:
- verify_user_by_email: Cuando detectes un email
- verify_user_by_phone: Cuando detectes un teléfono
- get_available_services: Cuando usuario pregunte por servicios o quiera agendar
- show_registration_form: Cuando usuario no esté registrado y quiera agendar
- create_draft_appointment: Cuando usuario selecciona un servicio específico para agendar
- confirm_appointment: Cuando usuario selecciona fecha y hora específicas del calendario

⚠️ NO PREGUNTES, ACTÚA:
- NO: "¿Estás registrado?" → SÍ: Verifica automáticamente
- NO: "¿Quieres ver los servicios?" → SÍ: Muestra servicios directamente
- NO: "¿Te gustaría agendar?" → SÍ: Inicia el proceso cuando detectes intención

💬 EJEMPLOS DE RESPUESTAS:

[SALUDO INICIAL]
Usuario: "Hola"
Tú: "¡Hola! Bienvenido al sistema de agendamiento. ¿En qué puedo ayudarte hoy?"

[INTENCIÓN DE AGENDAR]
Usuario: "Necesito una cita"
Tú: "Perfecto, te ayudo con tu cita. [VERIFICAR AUTOMÁTICAMENTE SI DETECTAS DATOS]"

[CON EMAIL DETECTADO]
Usuario: "Quiero agendar, mi email es juan@email.com"
Tú: [VERIFICAR CON verify_user_by_email INMEDIATAMENTE]
Si existe: "¡Hola Juan! Te reconocí. Estos son nuestros servicios disponibles..."
Si no existe: "Veo que es tu primera vez. Te voy a registrar rápidamente..."

[CONVERSACIÓN CASUAL]
Usuario: "¿Cómo estás?"
Tú: "Muy bien, gracias por preguntar. Estoy aquí para ayudarte con cualquier cosa que necesites. ¿Hay algo en particular en lo que pueda asistirte?"

✨ CALENDARIO Y HORARIOS:

Cuando el usuario seleccione un servicio:
1. Genera horarios disponibles para los próximos 7 días
2. Muestra slots de 30 minutos basados en disponibilidad real
3. Considera horarios de profesionales activos
4. Balancea la carga entre profesionales
5. Excluye domingos por defecto

🎯 RECUERDA:
- Tu propósito es AGENDAR CITAS eficientemente
- Mantén conversaciones naturales pero guía hacia el objetivo
- Usa las herramientas de forma inteligente y automática
- Simplifica el proceso lo más posible para el usuario
"""
        
        logger.info("[SUCCESS] AgendaIAAgent initialized successfully")
    
    def detectar_intencion(self, mensaje: str) -> Dict[str, Any]:
        """Detecta la intención principal del mensaje del usuario"""
        mensaje_lower = mensaje.lower()
        
        # Patrones de intención
        intenciones = {
            "AGENDAR": ["agendar", "cita", "reservar", "turno", "appointment", "necesito una cita"],
            "REAGENDAR": ["reagendar", "cambiar cita", "mover cita", "reprogramar"],
            "CANCELAR": ["cancelar", "anular", "eliminar cita"],
            "INFO_SERVICIOS": ["servicios", "qué servicios", "que ofrecen", "tipos de cita", "muestrame", "muestra", "ver servicios", "listar servicios", "catálogo", "opciones", "que tienen"],
            "SALUDO": ["hola", "buenos días", "buenas tardes", "buenas noches", "hey", "como estas", "como vas", "que tal"],
            "CONVERSACION_CASUAL": [
                "que te gusta", "que prefieres", "te gusta", "gustos", "preferencias",
                "interesante", "genial", "cool", "que bien", "amazing", "increible",
                "como estas", "como vas", "que haces", "como te va", "que tal",
                "gracias", "muy bien", "perfecto", "excelente"
            ],
            "CONFIRMACION": ["sí", "si", "ok", "está bien", "confirmo", "de acuerdo"],
            "NEGACION": ["no", "cancelar", "mejor no", "no quiero"]
        }
        
        # Buscar coincidencias
        for intencion, patrones in intenciones.items():
            for patron in patrones:
                if patron in mensaje_lower:
                    return {
                        "intent": intencion,
                        "confidence": 0.8,
                        "original_message": mensaje
                    }
        
        # Default to SALUDO for initial messages
        if not mensaje or len(mensaje.strip()) == 0:
            return {
                "intent": "SALUDO",
                "confidence": 0.9,
                "original_message": mensaje
            }
        
        return {
            "intent": "CONVERSACION_CASUAL",
            "confidence": 0.7,
            "original_message": mensaje
        }
    
    def extraer_datos_usuario(self, mensaje: str) -> Dict[str, Any]:
        """Extrae información del usuario del mensaje"""
        datos = {}
        
        # Regex para email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, mensaje)
        if emails:
            datos["email"] = emails[0]
        
        # Regex para teléfono (formato colombiano y internacional)
        phone_patterns = [
            r'\+57\s?\d{10}',  # +57 3001234567
            r'3[0-9]{2}\s?\d{7}',  # 300 1234567
            r'\d{10}'  # 3001234567
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, mensaje)
            if phones:
                datos["phone"] = phones[0]
                break
        
        # Extraer nombre (simple heurística)
        # Buscar patrones como "soy Juan", "me llamo María", etc.
        name_patterns = [
            r'(?:soy|me llamo|mi nombre es)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)',
            r'([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)*'
        ]
        
        for pattern in name_patterns:
            names = re.findall(pattern, mensaje, re.IGNORECASE)
            if names:
                # Tomar el primer nombre encontrado y limpiarlo
                name = names[0].strip().title()
                if len(name) > 2 and not any(word in name.lower() for word in ['email', 'telefono', 'celular']):
                    datos["name"] = name
                    break
        
        return datos
    
    def identificar_servicio(self, mensaje: str, servicios: List[Dict]) -> Optional[Dict]:
        """Identifica el servicio mencionado en el mensaje"""
        mensaje_lower = mensaje.lower()
        
        for servicio in servicios:
            nombre_servicio = servicio.get("name", "").lower()
            descripcion = servicio.get("description", "").lower()
            
            # Buscar coincidencias exactas o parciales
            if (nombre_servicio in mensaje_lower or 
                any(word in mensaje_lower for word in nombre_servicio.split()) or
                any(word in mensaje_lower for word in descripcion.split())):
                return servicio
        
        return None
    
    def extraer_preferencias_horario(self, mensaje: str) -> Dict[str, Any]:
        """Extrae preferencias temporales del mensaje"""
        preferencias = {}
        mensaje_lower = mensaje.lower()
        
        # Momento del día
        if any(word in mensaje_lower for word in ["mañana", "morning", "am"]):
            preferencias["time_preference"] = "morning"
        elif any(word in mensaje_lower for word in ["tarde", "afternoon", "pm"]):
            preferencias["time_preference"] = "afternoon"
        elif any(word in mensaje_lower for word in ["noche", "evening", "night"]):
            preferencias["time_preference"] = "evening"
        
        # Días específicos
        dias_semana = {
            "lunes": 1, "monday": 1,
            "martes": 2, "tuesday": 2,
            "miércoles": 3, "wednesday": 3,
            "jueves": 4, "thursday": 4,
            "viernes": 5, "friday": 5,
            "sábado": 6, "saturday": 6,
            "domingo": 7, "sunday": 7
        }
        
        for dia, numero in dias_semana.items():
            if dia in mensaje_lower:
                preferencias["preferred_weekday"] = numero
                preferencias["preferred_day_name"] = dia.capitalize()
                break
        
        # Fechas relativas
        if "hoy" in mensaje_lower:
            preferencias["preferred_date"] = "today"
        elif "mañana" in mensaje_lower and "morning" not in mensaje_lower:
            preferencias["preferred_date"] = "tomorrow"
        elif "próximo" in mensaje_lower or "siguiente" in mensaje_lower:
            preferencias["relative_date"] = "next"
        
        return preferencias
    
    async def use_registration_tool(self, action: str, context: AgentContext, **kwargs) -> Dict[str, Any]:
        """
        Usa la herramienta de registro express
        """
        if not self.tools_available or not self.registration_tool:
            return {
                "success": False, 
                "error": "Registration tool not available"
            }
        
        try:
            if action == "check_user":
                return await self.registration_tool.check_user_exists(
                    email=kwargs.get("email"),
                    phone=kwargs.get("phone")
                )
            elif action == "show_form":
                # Obtener datos pre-detectados del contexto
                pre_filled_data = {}
                if context.get_context("detected_name"):
                    pre_filled_data["name"] = context.get_context("detected_name")
                if context.get_context("detected_email"):
                    pre_filled_data["email"] = context.get_context("detected_email")
                if context.get_context("detected_phone"):
                    pre_filled_data["phone"] = context.get_context("detected_phone")
                
                logger.info(f"[OPTIMIZATION] Pre-filled data for form: {pre_filled_data}")
                
                return await self.registration_tool.show_registration_form(
                    conversation_id=context.conversation_id,
                    pre_filled_data=pre_filled_data if pre_filled_data else None
                )
            elif action == "process":
                return await self.registration_tool.process_registration(
                    name=kwargs.get("name"),
                    email=kwargs.get("email"), 
                    phone=kwargs.get("phone"),
                    conversation_id=context.conversation_id,
                    preferred_communication=kwargs.get("preferred_communication", "email")
                )
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error using registration tool: {e}")
            return {"success": False, "error": str(e)}
    
    async def use_service_tool(self, action: str, context: AgentContext, **kwargs) -> Dict[str, Any]:
        """
        Usa la herramienta de consulta de servicios
        """
        if not self.tools_available or not self.service_tool:
            return {
                "success": False, 
                "error": "Service consultation tool not available"
            }
        
        try:
            if action == "get_services":
                return await self.service_tool.get_available_services(
                    category=kwargs.get("category")
                )
            elif action == "get_details":
                return await self.service_tool.get_service_details(
                    service_id=kwargs.get("service_id")
                )
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error using service tool: {e}")
            return {"success": False, "error": str(e)}

    async def process_message(self, message: str, context: AgentContext) -> Tuple[str, AgentContext]:
        """
        Procesa un mensaje del usuario usando el agente IA
        """
        try:
            # DEBUG: Log del mensaje exacto que llega
            logger.info(f"[CRITICAL][CRITICAL] AGENT PROCESS_MESSAGE CALLED: '{message}'")
            logger.info(f"[CRITICAL][CRITICAL] Message type: {type(message)}, length: {len(message)}")
            logger.info(f"[CRITICAL][CRITICAL] Starts with REGISTRO: {message.startswith('REGISTRO:')}")
            logger.info(f"[CRITICAL][CRITICAL] Starts with SERVICIO_SELECCIONADO: {message.startswith('SERVICIO_SELECCIONADO:')}")
            
            # AQUÍ DEBE APARECER ESTE LOG SIEMPRE
            logger.info("[CRITICAL][CRITICAL] PROCESS_MESSAGE METHOD EXECUTING - This should ALWAYS appear")
            
            # PATRÓN DETECTION FIRST: Detectar patrones especiales ANTES de OpenAI
            # NO añadir al contexto si es un comando especial
            # Detectar si el usuario envía datos de registro
            if message.startswith("REGISTRO:") or message.startswith("FORM_SUBMISSION:"):
                logger.info("[DEBUG] REGISTRATION DATA detected - Processing registration BEFORE OpenAI - UPDATED")
                logger.info("[DEBUG] ENTERING REGISTRO BLOCK - This should appear for REGISTRO messages")
                # Extraer datos del formato: REGISTRO:nombre|email|telefono|comunicacion o FORM_SUBMISSION: {"name": "...", ...}
                if message.startswith("REGISTRO:"):
                    data_part = message.replace("REGISTRO:", "").strip()
                elif message.startswith("FORM_SUBMISSION:"):
                    data_part = message.replace("FORM_SUBMISSION:", "").strip()
                
                # Parse data based on format
                if message.startswith("FORM_SUBMISSION:"):
                    # Handle JSON format: {"name": "...", "email": "...", "phone": "...", "preferred_communication": "..."}
                    try:
                        form_data = json.loads(data_part)
                        name = form_data.get("name", "").strip()
                        email = form_data.get("email", "").strip()
                        phone = form_data.get("phone", "").strip()
                        preferred_communication = form_data.get("preferred_communication", "email").strip()
                        logger.info(f"[DEBUG] FORM_SUBMISSION parsed - name: {name}, email: {email}, phone: {phone}, comm: {preferred_communication}")
                    except json.JSONDecodeError as e:
                        logger.error(f"[ERROR] Failed to parse FORM_SUBMISSION JSON: {e}")
                        logger.error(f"[ERROR] Raw data: {data_part}")
                        return "Disculpa, hubo un error procesando tu registro. ¿Puedes intentar nuevamente?", context
                else:
                    # Handle original REGISTRO: format with | or , separators
                    if "|" in data_part:
                        parts = data_part.split("|")
                    else:
                        parts = data_part.split(",")
                    
                    logger.info(f"[DEBUG] REGISTRO parsing - data_part: '{data_part}', parts: {parts}")
                    
                    if len(parts) >= 3:
                        name = parts[0].strip()
                        email = parts[1].strip()
                        phone = parts[2].strip()
                        # Procesamiento más flexible del canal de comunicación
                        if len(parts) > 3:
                            pref_raw = parts[3].strip().lower()
                            # Extraer solo la palabra clave (email, sms, whatsapp)
                            if "email" in pref_raw:
                                preferred_communication = "email"
                            elif "whatsapp" in pref_raw:
                                preferred_communication = "whatsapp"
                            elif "sms" in pref_raw:
                                preferred_communication = "sms"
                            else:
                                preferred_communication = "email"  # default
                        else:
                            preferred_communication = "email"
                        
                        logger.info(f"[DEBUG] REGISTRO parsed - name: {name}, email: {email}, phone: {phone}, comm: {preferred_communication}")
                    else:
                        logger.error(f"[ERROR] Invalid REGISTRO format: {data_part}")
                        return "Disculpa, el formato de registro no es válido. ¿Puedes intentar nuevamente?", context
                
                # Procesar registro con herramienta (applies to both formats)
                tool_response = await self.use_registration_tool(
                        "process",
                        context,
                        name=name,
                        email=email,
                        phone=phone,
                        preferred_communication=preferred_communication
                    )
                
                if tool_response and tool_response.get("success"):
                    # IMPORTANTE: Actualizar user_id en el contexto
                    user_id = tool_response.get("user_id")
                    if user_id:
                        context.user_id = user_id
                        context.update_context("user_id", user_id)
                        context.update_context("user_data", tool_response.get("user_data", {}))
                        logger.info(f"[SUCCESS] User ID saved in context: {user_id}")
                    
                    # Configurar contexto del registro exitoso
                    context.update_context("tool_used", "express_registration_completed")
                    context.update_context("user_registered", True)
                    context.update_context("registration_completed", True)  # Flag adicional
                    context.update_context("skip_registration_detection", True)  # Evitar re-detección
                    context.update_context("tool_response", {})  # Limpiar tool_response para evitar re-renderizado
                    context.update_context("display_type", None)  # No mostrar ningún display
                    context.update_context("form_config", None)  # No mostrar formulario
                    
                    # Respuesta directa sin OpenAI
                    ai_response = tool_response.get("message", f"¡Perfecto {name}! Ya estás registrado como paciente.")
                    context.add_message("assistant", ai_response)
                    
                    logger.info(f"[DEBUG] REGISTRATION SUCCESS - Direct response: {ai_response}")
                    logger.info(f"[DEBUG] Context updated with user_registered=True and user_id={user_id}")
                    # NO agregamos el mensaje REGISTRO: al historial
                    return ai_response, context
                else:
                    # Error en registro
                    ai_response = tool_response.get("message", "Hubo un error procesando tu registro. ¿Puedes intentar nuevamente?")
                    context.add_message("user", message)  # Agregamos el mensaje original
                    context.add_message("assistant", ai_response)
                    return ai_response, context
            
            # Detectar selección de servicio
            logger.info(f"[DEBUG] [FAST] ABOUT TO CHECK SERVICIO_SELECCIONADO - message: '{message[:50]}...'")
            logger.info(f"[DEBUG] [FAST] Starts with SERVICIO_SELECCIONADO: {message.startswith('SERVICIO_SELECCIONADO:')}")
            if message.startswith("SERVICIO_SELECCIONADO:"):
                logger.info("[DEBUG] 🕒 SERVICE SELECTION detected - Processing BEFORE OpenAI - TIMESTAMP")
                logger.info("[DEBUG] 🕒 INSIDE SERVICIO_SELECCIONADO BLOCK - Starting processing - TIMESTAMP")
                # Procesar selección directamente
                parts = message.replace("SERVICIO_SELECCIONADO:", "").strip().split(" - ")
                logger.info(f"[DEBUG] SERVICE SELECTION DEBUG - parsed parts: {parts}")
                logger.info(f"[DEBUG] SERVICE SELECTION DEBUG - parts length: {len(parts)}")
                if len(parts) >= 2:
                    service_id = parts[0].strip()
                    service_name = parts[1].strip()
                    
                    # Verificar que existe user_id en contexto (de verificación o contexto previo)
                    user_id = context.get_context("user_id")
                    if not user_id and context.user_id:
                        user_id = context.user_id
                    
                    # También verificar si el usuario está verificado
                    user_verified = context.get_context("user_verified", False)
                    
                    logger.info(f"[DEBUG] SERVICE SELECTION DEBUG - user_id: {user_id}")
                    logger.info(f"[DEBUG] SERVICE SELECTION DEBUG - has appointment_tool: {bool(self.appointment_tool)}")
                    logger.info(f"[DEBUG] SERVICE SELECTION DEBUG - service_id: {service_id}")
                    logger.info(f"[DEBUG] SERVICE SELECTION DEBUG - service_name: {service_name}")
                    logger.info(f"[DEBUG] SERVICE SELECTION DEBUG - user_verified: {user_verified}")
                    logger.info(f"[DEBUG] SERVICE SELECTION DEBUG - context.user_id: {context.user_id}")
                    logger.info(f"[DEBUG] SERVICE SELECTION DEBUG - Will enter appointment block: {bool(user_id and self.appointment_tool)}")
                        
                    if user_id and self.appointment_tool:
                        logger.info("[DEBUG] 🎯 ENTERING APPOINTMENT TOOL BLOCK - Creating draft appointment")
                        logger.info(f"[DEBUG] 📅 CALLING create_draft_appointment with user_id={user_id}, service_id={service_id}, service_name={service_name}")
                        tool_response = await self.appointment_tool.create_draft_appointment(
                            user_id=user_id,
                            service_id=service_id,
                            service_name=service_name
                        )
                        logger.info(f"[DEBUG] 📅 APPOINTMENT TOOL RESPONSE: {tool_response.get('success') if tool_response else 'No response'}")
                        logger.info(f"[DEBUG] 📅 DISPLAY TYPE: {tool_response.get('display_type') if tool_response else 'None'}")
                        
                        if tool_response and tool_response.get("success"):
                            # CRITICAL: Save appointment_id in context for HORARIO_SELECCIONADO step
                            appointment_id = tool_response.get("appointment_id")
                            if appointment_id:
                                context.update_context("draft_appointment_id", appointment_id)
                                context.update_context("appointment_id", appointment_id)  # fallback
                                logger.info(f"[DEBUG] 🆔 SAVED APPOINTMENT_ID in context: {appointment_id}")
                            else:
                                logger.error(f"[ERROR] 🚨 NO APPOINTMENT_ID in tool_response: {tool_response}")
                                logger.error(f"[ERROR] 🚨 FULL TOOL_RESPONSE: {tool_response}")
                            
                            # Configurar contexto para mostrar selector de horarios
                            context.update_context("tool_used", "appointment_scheduling")
                            context.update_context("tool_response", tool_response.get("tool_response", {}))
                            context.update_context("display_type", "time_slot_selector")
                            
                            ai_response = tool_response.get("message", f"¡Perfecto! Has seleccionado {service_name}.")
                            context.add_message("assistant", ai_response)
                            
                            logger.info(f"[DEBUG] SERVICE SELECTION SUCCESS - Direct response: {ai_response}")
                            return ai_response, context
                    else:
                        # PROBLEMA: No hay user_id - necesita registrarse primero
                        logger.info(f"[DEBUG] SERVICE SELECTION ERROR - No user_id found. user_id: {user_id}")
                        logger.info(f"[DEBUG] SERVICE SELECTION ERROR - Redirecting to registration")
                        
                        # Respuesta directa para solicitar registro
                        ai_response = f"Me encanta que hayas elegido '{service_name}'. Para continuar con el agendamiento, necesito que te registres primero. ¿Podrías proporcionarme tu nombre completo, email y teléfono?"
                        
                        # NO agregar el mensaje SERVICIO_SELECCIONADO al historial para evitar confusión
                        # context.add_message("user", message)  # ELIMINADO - evita que OpenAI lo vea
                        context.add_message("assistant", ai_response)
                        
                        # Limpiar contexto de herramientas anteriores para evitar catálogo duplicado
                        context.update_context("tool_used", None)
                        context.update_context("tool_response", None)
                        context.update_context("display_type", "conversational")
                        
                        # Configurar contexto para forzar herramienta de registro
                        context.update_context("selected_service_id", service_id)
                        context.update_context("selected_service_name", service_name)
                        context.update_context("next_step", "registration_required")
                        
                        return ai_response, context
            
            # Detectar selección de horario
            if message.startswith("HORARIO_SELECCIONADO:"):
                logger.info("[DEBUG] 🕒 TIME SLOT SELECTION detected - Processing BEFORE OpenAI")
                logger.info("[DEBUG] 🕒 INSIDE HORARIO_SELECCIONADO BLOCK - Starting processing")
                
                # Procesar selección directamente
                # Formato: HORARIO_SELECCIONADO: 2025-09-16 09:00 - 2025-09-16T09:00:00
                time_part = message.replace("HORARIO_SELECCIONADO:", "").strip()
                logger.info(f"[DEBUG] TIME SELECTION DEBUG - time_part: {time_part}")
                
                # Extraer fecha y hora del formato "2025-09-16 09:00 - 2025-09-16T09:00:00"
                if " - " in time_part:
                    date_time_display, datetime_iso = time_part.split(" - ")
                    # Separar fecha y hora: "2025-09-16 09:00" → "2025-09-16" y "09:00"
                    if " " in date_time_display:
                        selected_date, selected_time = date_time_display.strip().split(" ")
                    else:
                        selected_date = date_time_display.strip()
                        selected_time = "09:00"  # fallback
                else:
                    # Fallback si no tiene el formato esperado
                    selected_date = "2025-09-16"
                    selected_time = "09:00"
                
                # Verificar que existe user_id en contexto
                user_id = context.get_context("user_id")
                if not user_id and context.user_id:
                    user_id = context.user_id
                
                # Obtener appointment_id del contexto (debe estar del paso anterior)
                appointment_id = context.get_context("draft_appointment_id") or context.get_context("appointment_id")
                
                logger.info(f"[DEBUG] TIME SELECTION DEBUG - user_id: {user_id}")
                logger.info(f"[DEBUG] TIME SELECTION DEBUG - selected_date: {selected_date}")
                logger.info(f"[DEBUG] TIME SELECTION DEBUG - selected_time: {selected_time}")
                logger.info(f"[DEBUG] TIME SELECTION DEBUG - appointment_id: {appointment_id}")
                logger.info(f"[DEBUG] TIME SELECTION DEBUG - has appointment_tool: {bool(self.appointment_tool)}")
                
                # DETAILED CONDITION CHECK
                logger.info(f"[DEBUG] CONDITION CHECK - user_id exists: {bool(user_id)}")
                logger.info(f"[DEBUG] CONDITION CHECK - appointment_id exists: {bool(appointment_id)}")
                logger.info(f"[DEBUG] CONDITION CHECK - appointment_tool exists: {bool(self.appointment_tool)}")
                logger.info(f"[DEBUG] CONDITION CHECK - ALL CONDITIONS: {bool(user_id and appointment_id and self.appointment_tool)}")
                
                if user_id and appointment_id and self.appointment_tool:
                    logger.info("[DEBUG] 🎯 CALLING APPOINTMENT CONFIRMATION")
                    # Aquí llamaríamos a la función de confirmación de cita
                    tool_response = await self.appointment_tool.confirm_appointment(
                        appointment_id=appointment_id,
                        selected_date=selected_date,
                        selected_time=selected_time,
                        user_id=user_id
                    )
                    
                    logger.info(f"[DEBUG] 📅 APPOINTMENT CONFIRMATION RESPONSE: {tool_response.get('success') if tool_response else 'No response'}")
                    
                    if tool_response and tool_response.get("success"):
                        logger.info(f"[DEBUG] 🎉 APPOINTMENT CONFIRMED via Pattern Detection")

                        # 🧹 LIMPIEZA COMPLETA: Eliminar TODOS los datos del calendario
                        context.update_context("tool_response", None)
                        context.update_context("available_slots", None)
                        context.update_context("service_data", None)
                        context.update_context("slot_config", None)
                        context.update_context("time_slots", None)
                        context.update_context("tool_data", None)
                        context.update_context("catalog_config", None)
                        context.update_context("service_catalog", None)

                        # ✅ CONFIGURAR CONTEXTO PARA CONFIRMACIÓN SOLAMENTE
                        context.update_context("tool_used", "appointment_confirmed")
                        context.update_context("display_type", "appointment_confirmation")
                        context.update_context("conversation_flow", "appointment_confirmed")

                        # 🔄 REINICIAR CONTEXTO para nuevas citas
                        user_data = context.context_data.get("user_data", {})
                        user_id = context.context_data.get("user_id")
                        context.context_data = {
                            "user_id": user_id,
                            "user_verified": True,
                            "user_data": user_data,
                            "main_intent": "available_for_new_appointments",
                            "conversation_flow": "appointment_confirmed",
                            "skip_registration_detection": True,
                            "ready_for_new_appointment": True
                        }

                        logger.info("🔄 Context reset - Ready for new appointment cycle")
                        
                        ai_response = tool_response.get("message", f"¡Genial! Tu cita ha sido confirmada para el {selected_date}.")
                        context.add_message("assistant", ai_response)
                        
                        logger.info(f"[DEBUG] TIME SELECTION SUCCESS - Appointment confirmed: {ai_response}")
                        return ai_response, context
                    else:
                        # Error en confirmación
                        ai_response = "Hubo un problema confirmando tu cita. ¿Podrías intentar seleccionar otro horario?"
                        context.add_message("assistant", ai_response)
                        return ai_response, context
                else:
                    # Error: No hay user_id
                    logger.info(f"[DEBUG] TIME SELECTION ERROR - No user_id found. user_id: {user_id}")
                    ai_response = "Hubo un problema procesando tu selección. ¿Podrías intentar nuevamente?"
                    context.add_message("assistant", ai_response)
                    return ai_response, context
            
            # 🔄 OPTIMIZACIÓN: Usuario ya verificado quiere agendar nueva cita
            user_already_verified = context.get_context("user_verified", False) or context.get_context("user_registered", False)
            ready_for_new = context.get_context("ready_for_new_appointment", False)

            # Si el usuario ya está verificado y quiere agendar, mostrar servicios directamente
            if user_already_verified and self.service_tool:
                intent_detected = self.detectar_intencion(message)
                appointment_keywords = ['cita', 'agendar', 'reservar', 'turno', 'consulta', 'nueva cita', 'otra cita']

                if (intent_detected['intent'] in ['AGENDAR', 'INFO_SERVICIOS'] or
                    any(word in message.lower() for word in appointment_keywords)):

                    logger.info("[FAST_TRACK] Verified user wants to schedule - Showing services directly")

                    service_response = await self.use_service_tool("get_services", context)
                    if service_response and service_response.get('success', False):
                        context.update_context("tool_used", service_response.get('tool_used'))
                        context.update_context("tool_response", service_response.get('tool_response', {}))
                        context.update_context("display_type", service_response.get('display_type'))

                        user_name = context.get_context("user_data", {}).get("name", "")
                        ai_response = f"¡Perfecto {user_name}! Aquí tienes nuestros servicios disponibles:"
                        context.add_message("assistant", ai_response)

                        logger.info("[FAST_TRACK] Services displayed for verified user")
                        return ai_response, context

            # *** DETECCIÓN AUTOMÁTICA DE DATOS PARCIALES - PASO 2 OPTIMIZACIÓN ***
            # Verificar automáticamente si el usuario proporciona email/teléfono
            # Solo si no está ya registrado/verificado
            
            if not user_already_verified and self.verification_tool:
                logger.info("[AUTO_DETECT] Checking for partial user data in message...")
                
                # Extraer datos del mensaje usando el método existente
                extracted_data = self.extraer_datos_usuario(message)
                logger.info(f"[AUTO_DETECT] Extracted data: {extracted_data}")
                
                # Si encontramos email, verificar automáticamente
                if 'email' in extracted_data:
                    email = extracted_data['email']
                    logger.info(f"[AUTO_DETECT] Email detected: {email} - Verifying automatically...")
                    
                    verification_result = await self.verification_tool.verify_user_by_email(email)
                    
                    if verification_result.get('exists', False):
                        # Usuario existe - Actualizar contexto y continuar
                        user_id = verification_result.get('user_id')
                        user_name = verification_result.get('user_name')
                        
                        context.user_id = user_id
                        context.update_context("user_id", user_id)
                        context.update_context("user_verified", True)
                        context.update_context("user_data", {
                            "name": user_name,
                            "email": email,
                            "id": user_id
                        })
                        
                        # Respuesta directa optimizada
                        ai_response = f"¡Perfecto {user_name}! Te reconocí por tu email. ¿Te gustaría ver los servicios disponibles para agendar tu cita?"
                        
                        context.add_message("assistant", ai_response)
                        logger.info(f"[AUTO_DETECT] User verified automatically: {user_name} ({email})")
                        
                        # Mostrar servicios inmediatamente si el usuario quiere agendar
                        intent_detected = self.detectar_intencion(message)
                        if intent_detected['intent'] in ['AGENDAR', 'INFO_SERVICIOS'] or any(word in message.lower() for word in ['cita', 'agendar', 'servicio', 'turno']):
                            logger.info("[AUTO_DETECT] Appointment intent detected - Showing services automatically")
                            
                            service_response = await self.use_service_tool("get_services", context)
                            if service_response and service_response.get('success', False):
                                context.update_context("tool_used", service_response.get('tool_used'))
                                context.update_context("tool_response", service_response.get('tool_response', {}))
                                context.update_context("display_type", service_response.get('display_type'))
                                
                                ai_response += " Aquí tienes nuestros servicios disponibles:"
                        
                        return ai_response, context
                    
                    else:
                        # Usuario no existe - Pre-llenar registro con datos detectados
                        logger.info(f"[AUTO_DETECT] User not found with email {email} - Pre-filling registration")
                        
                        # Preparar datos para pre-llenar formulario
                        context.update_context("detected_email", email)
                        if 'phone' in extracted_data:
                            context.update_context("detected_phone", extracted_data['phone'])
                        if 'name' in extracted_data:
                            context.update_context("detected_name", extracted_data['name'])
                        
                        logger.info("[AUTO_DETECT] Pre-filled registration data ready")
                
                # Si encontramos teléfono (y no email), verificar por teléfono
                elif 'phone' in extracted_data:
                    phone = extracted_data['phone']
                    logger.info(f"[AUTO_DETECT] Phone detected: {phone} - Verifying automatically...")
                    
                    verification_result = await self.verification_tool.verify_user_by_phone(phone)
                    
                    if verification_result.get('exists', False):
                        # Usuario existe - Actualizar contexto
                        user_id = verification_result.get('user_id')
                        user_name = verification_result.get('user_name')
                        
                        context.user_id = user_id
                        context.update_context("user_id", user_id)
                        context.update_context("user_verified", True)
                        context.update_context("user_data", {
                            "name": user_name,
                            "phone": phone,
                            "id": user_id
                        })
                        
                        # Respuesta directa optimizada
                        ai_response = f"¡Hola {user_name}! Te reconocí por tu teléfono. ¿Te gustaría ver los servicios disponibles?"
                        
                        context.add_message("assistant", ai_response)
                        logger.info(f"[AUTO_DETECT] User verified by phone: {user_name} ({phone})")
                        
                        return ai_response, context
            
            # Si llegamos aquí, es un mensaje normal, lo agregamos al contexto
            context.add_message("user", message)
            
            # Preparar mensajes para OpenAI
            messages = [
                {"role": "system", "content": self.instructions}
            ]
            
            # Añadir historial reciente (últimos 10 mensajes)
            recent_history = context.conversation_history[-10:] if context.conversation_history else []
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            logger.info(f"[CRITICAL][CRITICAL] Using conversation history: {len(recent_history)} messages")
            
            # NO añadir contexto confuso que fuerce respuestas de citas
            # Solo añadir contexto si realmente hay datos relevantes para conversación natural
            if context.get_context('user_data') and context.get_context('user_data').get('name'):
                user_name = context.get_context('user_data').get('name')
                context_info = f"El usuario se llama {user_name}."
                messages.append({"role": "system", "content": context_info})
            
            # VERIFICAR FLAG SKIP_OPENAI_CALL ANTES DE LLAMAR OPENAI
            skip_openai = context.get_context("skip_openai_call", False)
            if skip_openai:
                logger.info("[DEBUG] SKIP_OPENAI_CALL flag is set - Skipping OpenAI processing")
                # Limpiar flag para próximas interacciones
                context.update_context("skip_openai_call", False)
                # Si ya hay una respuesta definida, devolverla
                if ai_response:
                    return ai_response, context
                else:
                    return "Continuemos con el proceso.", context
            
            # DEBUG: Log COMPLETO de lo que se envía a OpenAI
            logger.info(f"[CRITICAL][CRITICAL] CALLING OPENAI API with {len(messages)} messages")
            logger.info(f"[CRITICAL][CRITICAL] COMPLETE SYSTEM PROMPT: {messages[0]['content']}")
            logger.info(f"[CRITICAL][CRITICAL] ALL MESSAGES TO OPENAI: {messages}")
            logger.info(f"[CRITICAL][CRITICAL] User message: {message}")
            
            # Preparar herramientas disponibles para OpenAI Function Calling
            tools = []
            if self.tools_available:
                if self.registration_tool:
                    tools.extend([
                        {
                            "type": "function",
                            "function": {
                                "name": "show_registration_form",
                                "description": "Muestra formulario de registro cuando el usuario quiere agendar cita pero no está registrado",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "reason": {"type": "string", "description": "Razón por la que se muestra el formulario"}
                                    }
                                }
                            }
                        }
                    ])
                
                if self.verification_tool:
                    tools.extend([
                        {
                            "type": "function",
                            "function": {
                                "name": "verify_user_by_email",
                                "description": "Verifica si un usuario está registrado usando su email cuando el usuario dice estar registrado o proporciona un email",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "description": "Email del usuario a verificar"}
                                    },
                                    "required": ["email"]
                                }
                            }
                        },
                        {
                            "type": "function", 
                            "function": {
                                "name": "verify_user_by_phone",
                                "description": "Verifica si un usuario está registrado usando su teléfono cuando el usuario proporciona un número telefónico",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "phone": {"type": "string", "description": "Teléfono del usuario a verificar"}
                                    },
                                    "required": ["phone"]
                                }
                            }
                        }
                    ])
                
                if self.service_tool:
                    tools.extend([
                        {
                            "type": "function",
                            "function": {
                                "name": "get_available_services",
                                "description": "Obtiene y muestra catálogo de servicios médicos disponibles cuando el usuario pregunta por servicios, opciones, o qué ofrecen",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "category": {
                                            "type": "string",
                                            "description": "Filtrar por categoría específica (opcional)",
                                            "enum": ["consulta", "especialidad", "laboratorio", "emergencia", "terapia", "belleza"]
                                        }
                                    }
                                }
                            }
                        }
                    ])

                # 🔧 AGREGADO: Herramientas de agendamiento para OpenAI Function Calling
                if self.appointment_tool:
                    tools.extend([
                        {
                            "type": "function",
                            "function": {
                                "name": "create_draft_appointment",
                                "description": "Crea borrador de cita cuando usuario selecciona un servicio específico. Usar SOLO cuando el usuario elige un servicio específico para agendar",
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
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "confirm_appointment",
                                "description": "Confirma una cita asignando fecha, hora y profesional específico. Usar SOLO cuando el usuario ya seleccionó fecha y hora específicas",
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
                        }
                    ])
            
            # Llamar a OpenAI con Function Calling si hay herramientas disponibles
            call_params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.8,
                "top_p": 0.95,
                "frequency_penalty": 0.6,
                "presence_penalty": 0.4
            }
            
            if tools:
                call_params["tools"] = tools
                call_params["tool_choice"] = "auto"  # OpenAI decide cuándo usar herramientas
            
            logger.info(f"[DEBUG] OPENAI CALL with {len(tools)} tools available")
            
            response = self.client.chat.completions.create(**call_params)
            
            # Verificar si OpenAI quiere usar herramientas
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            if tool_calls:
                logger.info(f"[DEBUG] OPENAI wants to use {len(tool_calls)} tools")
                
                # Procesar llamadas a herramientas
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"[DEBUG] TOOL CALL: {function_name} with args: {function_args}")
                    
                    if function_name == "get_available_services":
                        logger.info(f"[DEBUG] Processing get_available_services tool call")
                        # Usar herramienta de servicios
                        service_response = await self.use_service_tool("get_services", context, 
                                                                     category=function_args.get("category"))
                        
                        if service_response and service_response.get("tool_response"):
                            # Configurar contexto para mostrar catálogo
                            context.update_context("tool_used", "service_consultation")
                            context.update_context("tool_response", service_response.get("tool_response", {}))
                            context.update_context("display_type", "service_catalog") 
                            context.update_context("tool_data", {
                                "catalog_config": service_response.get("tool_response", {}).get("catalog_config", {})
                            })
                            context.update_context("ai_continues_after", True)
                            
                            # Usar mensaje de la herramienta
                            ai_response = service_response.get("message", "Aquí tienes nuestros servicios médicos disponibles:")
                            
                            # Añadir mensaje del AI al historial
                            context.add_message("assistant", ai_response)
                            
                            return ai_response, context
                    
                    elif function_name == "show_registration_form":
                        # Usar herramienta de registro
                        tool_response = await self.use_registration_tool("show_form", context)
                        
                        if tool_response and tool_response.get("success") != False:
                            context.update_context("tool_used", "express_registration")
                            context.update_context("tool_response", tool_response)
                            
                            ai_response = tool_response.get("message", "Para agendar tu cita, necesito que completes este formulario:")
                            
                            # Añadir mensaje del AI al historial
                            context.add_message("assistant", ai_response)
                            
                            return ai_response, context
                    
                    elif function_name == "verify_user_by_email" and self.verification_tool:
                        # Verificar usuario por email
                        email = function_args.get("email")
                        logger.info(f"[DEBUG] Processing verify_user_by_email tool call with email: {email}")

                        verification_response = await self.verification_tool.verify_user_by_email(email)

                        if verification_response.get("exists"):
                            # Usuario encontrado - guardar información y continuar a servicios
                            context.update_context("user_id", verification_response.get("user_id"))
                            context.update_context("user_name", verification_response.get("user_name"))
                            context.update_context("user_email", verification_response.get("user_email"))
                            context.update_context("user_verified", True)
                            context.update_context("next_step", "proceed_to_appointment")

                            ai_response = verification_response.get("message")
                            context.add_message("assistant", ai_response)

                            return ai_response, context
                        else:
                            # Usuario no encontrado - proceder al registro
                            ai_response = verification_response.get("message")
                            context.add_message("assistant", ai_response)

                            return ai_response, context

                    # 🔧 AGREGADO: Manejo de herramientas de agendamiento en OpenAI Function Calling
                    elif function_name == "create_draft_appointment" and self.appointment_tool:
                        logger.info(f"[DEBUG] 🎯 Processing create_draft_appointment tool call via OpenAI")
                        user_id = function_args.get("user_id")
                        service_id = function_args.get("service_id")
                        service_name = function_args.get("service_name")

                        # Llamar a la herramienta de agendamiento
                        appointment_response = await self.appointment_tool.create_draft_appointment(
                            user_id=user_id,
                            service_id=service_id,
                            service_name=service_name
                        )

                        if appointment_response and appointment_response.get("success"):
                            # Configurar contexto para mostrar selector de horarios
                            appointment_id = appointment_response.get("appointment_id")
                            if appointment_id:
                                context.update_context("draft_appointment_id", appointment_id)
                                context.update_context("appointment_id", appointment_id)

                            context.update_context("tool_used", "appointment_scheduling")
                            context.update_context("tool_response", appointment_response.get("tool_response", {}))
                            context.update_context("display_type", "time_slot_selector")

                            ai_response = appointment_response.get("message", f"¡Perfecto! Has seleccionado {service_name}.")
                            context.add_message("assistant", ai_response)

                            return ai_response, context

                    elif function_name == "confirm_appointment" and self.appointment_tool:
                        logger.info(f"[DEBUG] 🎯 Processing confirm_appointment tool call via OpenAI")
                        appointment_id = function_args.get("appointment_id")
                        selected_date = function_args.get("selected_date")
                        selected_time = function_args.get("selected_time")
                        user_id = function_args.get("user_id")

                        # Llamar a la herramienta de confirmación
                        confirmation_response = await self.appointment_tool.confirm_appointment(
                            appointment_id=appointment_id,
                            selected_date=selected_date,
                            selected_time=selected_time,
                            user_id=user_id
                        )

                        if confirmation_response and confirmation_response.get("success"):
                            logger.info(f"[DEBUG] 🎉 APPOINTMENT CONFIRMED via OpenAI Function Calling")

                            # 🧹 LIMPIEZA COMPLETA: Eliminar TODOS los datos del calendario
                            context.update_context("tool_response", None)
                            context.update_context("available_slots", None)
                            context.update_context("service_data", None)
                            context.update_context("slot_config", None)
                            context.update_context("time_slots", None)
                            context.update_context("tool_data", None)
                            context.update_context("catalog_config", None)
                            context.update_context("service_catalog", None)

                            # Configurar contexto para confirmación SOLAMENTE
                            context.update_context("tool_used", "appointment_confirmed")
                            context.update_context("display_type", "appointment_confirmation")
                            context.update_context("conversation_flow", "appointment_confirmed")

                            # 🔄 REINICIAR CONTEXTO para nuevas citas
                            user_data = context.context_data.get("user_data", {})
                            user_id = context.context_data.get("user_id")
                            context.context_data = {
                                "user_id": user_id,
                                "user_verified": True,
                                "user_data": user_data,
                                "main_intent": "available_for_new_appointments",
                                "conversation_flow": "appointment_confirmed"
                            }

                            ai_response = confirmation_response.get("message", "¡Cita confirmada exitosamente!")
                            context.add_message("assistant", ai_response)

                            return ai_response, context
                    
                    elif function_name == "verify_user_by_phone" and self.verification_tool:
                        # Verificar usuario por teléfono
                        phone = function_args.get("phone")
                        logger.info(f"[DEBUG] Processing verify_user_by_phone tool call with phone: {phone}")
                        
                        verification_response = await self.verification_tool.verify_user_by_phone(phone)
                        
                        if verification_response.get("exists"):
                            # Usuario encontrado - guardar información y continuar a servicios
                            context.update_context("user_id", verification_response.get("user_id"))
                            context.update_context("user_name", verification_response.get("user_name"))
                            context.update_context("user_phone", verification_response.get("user_phone"))
                            context.update_context("user_verified", True)
                            context.update_context("next_step", "proceed_to_appointment")
                            
                            ai_response = verification_response.get("message")
                            context.add_message("assistant", ai_response)
                            
                            return ai_response, context
                        else:
                            # Usuario no encontrado - proceder al registro
                            ai_response = verification_response.get("message")
                            context.add_message("assistant", ai_response)
                            
                            return ai_response, context
                
                # Si llegamos aquí, ninguna herramienta fue procesada correctamente
                ai_response = "Disculpa, hubo un problema procesando tu solicitud. ¿Puedes intentar nuevamente?"
            else:
                # Respuesta normal sin herramientas
                ai_response = response_message.content or "Lo siento, no pude procesar tu solicitud correctamente."
            
            # DEBUG: Log respuesta de OpenAI
            logger.info(f"[CRITICAL][CRITICAL] OPENAI RAW RESPONSE: '{ai_response}'")
            
            # Ensure proper UTF-8 encoding
            if isinstance(ai_response, str):
                ai_response = ai_response.encode('utf-8').decode('utf-8')
            
            # Añadir respuesta al contexto
            context.add_message("assistant", ai_response)
            
            # Analizar intención y decidir si usar herramientas
            intent_data = self.detectar_intencion(message)
            context.update_context("main_intent", intent_data["intent"])
            
            # La lógica de herramientas ahora se ejecuta ANTES de OpenAI
            # Solo llegar aquí si no hay patrones especiales detectados
            return ai_response, context
        
        except Exception as e:
            logger.error(f"Error processing message with AI Agent: {e}")
            logger.error(f"Full error traceback:", exc_info=True)
            
            # Return detailed error information for debugging
            error_response = f"ERROR OPENAI DETALLADO: {type(e).__name__}: {str(e)}"
            context.add_message("assistant", error_response)
            
            return error_response, context
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analiza la intención de un mensaje"""
        return self.detectar_intencion(message)