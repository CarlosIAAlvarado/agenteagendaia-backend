"""
AI Tool: Consulta de Servicios
Herramienta para que OpenAI muestre los servicios médicos disponibles
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ...repositories.service_repository import IServiceRepository
from ...repositories.professional_repository import IProfessionalRepository

logger = logging.getLogger(__name__)


class ServiceConsultationTool:
    """
    Herramienta AI: Consulta de Servicios
    
    OpenAI usa esta herramienta cuando:
    1. Usuario pregunta "¿qué servicios tienen?"
    2. Después del registro exitoso
    3. Usuario quiere ver especialidades disponibles
    4. Necesita información sobre precios/duración
    """
    
    def __init__(
        self,
        service_repository: IServiceRepository,
        professional_repository: IProfessionalRepository
    ):
        self._service_repo = service_repository
        self._professional_repo = professional_repository
    
    async def get_available_services(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene servicios disponibles opcionalmente filtrados por categoría
        
        Args:
            category: "general", "especialidad", "laboratorio", "emergencia", etc.
        
        Returns:
            {
                "services": [...],
                "categories": [...],
                "total_services": int,
                "display_type": "service_catalog"
            }
        """
        try:
            # Obtener todos los servicios activos
            services = await self._service_repo.get_active_services()
            
            # Filtrar por categoría si se especifica
            if category:
                logger.info(f"[DEBUG] Filtering by category: {category}")
                logger.info(f"[DEBUG] Total services before filter: {len(services)}")
                
                # Mapear categoría de display a service_type real
                # Los service_type reales en BD son: "maintenance", "consultation"
                category_to_type = {
                    "consulta": "medical",
                    "belleza": "beauty", 
                    "especialidad": "consultation",  # "Gastos que existen" tiene consultation ✅
                    "terapia": "maintenance",        # "automatizacionvyrtium" tiene maintenance ✅
                    "otros": "other"
                }
                
                target_type = category_to_type.get(category.lower())
                logger.info(f"[DEBUG] Target type for category '{category}': {target_type}")
                
                if target_type:
                    original_services = services[:]  # Copia para debugging
                    services = [s for s in services if s.service_type.value.lower() == target_type.lower()]
                    logger.info(f"[DEBUG] Services after filtering by target_type '{target_type}': {len(services)}")
                    
                    # Debug: Mostrar los service_type de los servicios originales
                    for i, s in enumerate(original_services):
                        logger.info(f"[DEBUG] Service {i}: name='{s.name}', service_type='{s.service_type.value}'")
                else:
                    # Si no encuentra mapeo, buscar directamente por service_type
                    services = [s for s in services if s.service_type.value.lower() == category.lower()]
                    logger.info(f"[DEBUG] Services after direct category filter: {len(services)}")
                
                logger.info(f"[DEBUG] Final services count after filter: {len(services)}")
            
            # Agrupar servicios por service_type para mejor visualización
            categories = {}
            for service in services:
                # Mapear service_type a categorías amigables
                # Los service_type reales en BD son: "maintenance", "consultation"
                type_to_category = {
                    "medical": "consulta",
                    "beauty": "belleza", 
                    "consultation": "especialidad",  # "Gastos que existen" → "especialidad" ✅
                    "maintenance": "terapia",        # "automatizacionvyrtium" → "terapia" ✅
                    "other": "otros"
                }
                
                cat = type_to_category.get(service.service_type.value, service.service_type.value)
                if cat not in categories:
                    categories[cat] = []
                
                categories[cat].append({
                    "id": service.id,
                    "name": service.name,
                    "description": service.description,
                    "price": service.price or 0,
                    "currency": "COP",  # Pesos colombianos
                    "duration_minutes": service.duration_minutes,
                    "is_emergency": False,  # La entidad Service no tiene este campo
                    "requires_preparation": False,  # La entidad Service no tiene este campo
                    "preparation_instructions": None
                })
            
            # Contar profesionales disponibles por servicio (lógica real)
            service_availability = {}
            for service in services:
                # Obtener profesionales que pueden realizar este servicio
                professionals = await self._professional_repo.get_by_service_id(service.id)
                active_professionals = [p for p in professionals if p.is_active]
                service_availability[service.id] = len(active_professionals)
            
            total_services = len(services)
            
            # Crear respuesta estructurada para el frontend
            response = {
                "tool_used": "service_consultation",
                "action": "show_services",
                "display_type": "service_catalog",  # Le dice al frontend cómo renderizar
                "total_services": total_services,
                "filtered_category": category,
                "service_data": {
                    "categories": categories,
                    "availability": service_availability
                },
                "message": self._generate_service_message(categories, category, total_services),
                "next_step": "service_selection",
                "conversation_flow": "services_displayed",
                "tool_response": {
                    "display_type": "service_catalog",
                    "catalog_config": {
                        "id": "medical_services_catalog",
                        "type": "service_grid",
                        "title": "🏥 Servicios Médicos Disponibles",
                        "subtitle": "Selecciona el servicio que necesitas:",
                        "theme": {
                            "primary_color": "#059669",  # Verde médico
                            "background": "#F0FDF4",     # Verde muy suave
                            "card_background": "#FFFFFF",
                            "border_radius": "16px",
                            "grid_columns": 2  # 2 columnas en desktop, 1 en mobile
                        },
                        "categories": self._format_categories_for_display(categories, service_availability)
                    }
                },
                "ai_continues_after": True  # OpenAI sigue controlando después
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting available services: {e}")
            return {
                "tool_used": "service_consultation",
                "action": "error",
                "error": f"Error obteniendo servicios: {str(e)}",
                "message": "Disculpa, hubo un error obteniendo los servicios. ¿Puedes intentar nuevamente?",
                "next_step": "retry_services"
            }
    
    async def get_service_details(self, service_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles específicos de un servicio
        OpenAI usa esto cuando el usuario pregunta por un servicio específico
        """
        try:
            service = await self._service_repo.get_by_id(service_id)
            if not service:
                return {
                    "success": False,
                    "error": "Servicio no encontrado",
                    "message": "No encontré ese servicio. ¿Puedes verificar el nombre?"
                }
            
            # Obtener profesionales que ofrecen este servicio
            professionals = await self._professional_repo.get_by_specialties([service.specialty])
            
            service_details = {
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "category": service.category,
                "specialty": service.specialty,
                "price": service.price,
                "currency": "COP",
                "duration_minutes": service.duration_minutes,
                "duration_display": f"{service.duration_minutes} minutos",
                "is_emergency": service.is_emergency,
                "requires_preparation": service.requires_preparation,
                "preparation_instructions": service.preparation_instructions,
                "available_professionals": len(professionals),
                "professional_names": [p.name for p in professionals[:3]]  # Mostrar máximo 3
            }
            
            return {
                "tool_used": "service_consultation", 
                "action": "service_details",
                "success": True,
                "service_data": service_details,
                "message": self._generate_service_detail_message(service_details),
                "next_step": "confirm_service_selection",
                "conversation_flow": "service_details_shown"
            }
            
        except Exception as e:
            logger.error(f"Error getting service details: {e}")
            return {
                "success": False,
                "error": f"Error obteniendo detalles: {str(e)}",
                "message": "Disculpa, hubo un error obteniendo los detalles del servicio."
            }
    
    def _generate_service_message(self, categories: Dict, filtered_category: Optional[str], total: int) -> str:
        """Genera mensaje descriptivo sobre los servicios"""
        if filtered_category:
            return f"Aquí tienes los servicios de {filtered_category} que tenemos disponibles ({total} servicios):"
        
        category_names = list(categories.keys())
        if len(category_names) <= 2:
            cat_text = " y ".join(category_names)
        else:
            cat_text = f"{', '.join(category_names[:-1])} y {category_names[-1]}"
        
        return f"Tenemos {total} servicios médicos disponibles en {cat_text}. ¿Cuál te interesa?"
    
    def _generate_service_detail_message(self, service_data: Dict) -> str:
        """Genera mensaje detallado sobre un servicio específico"""
        message = f"📋 **{service_data['name']}**\n\n"
        message += f"📝 {service_data['description']}\n\n"
        message += f"Precio: ${service_data['price']:,} COP\n"
        message += f"Duración: {service_data['duration_display']}\n"
        
        if service_data['requires_preparation']:
            message += f"\n**Preparación requerida:**\n{service_data['preparation_instructions']}\n"
        
        if service_data['available_professionals'] > 0:
            message += f"\n👥 Disponible con {service_data['available_professionals']} profesionales"
            if service_data['professional_names']:
                message += f": {', '.join(service_data['professional_names'])}"
                if service_data['available_professionals'] > 3:
                    message += f" y {service_data['available_professionals'] - 3} más"
        
        message += "\n\n¿Te gustaría agendar una cita para este servicio?"
        return message
    
    def _format_categories_for_display(self, categories: Dict, availability: Dict) -> List[Dict]:
        """Formatea las categorías para el display del frontend"""
        formatted_categories = []
        
        for category_name, services in categories.items():
            formatted_services = []
            for service in services:
                available_professionals = availability.get(service['id'], 0)
                
                formatted_services.append({
                    "id": service['id'],
                    "title": service['name'],
                    "description": service['description'],
                    "price": f"${service['price']:,} COP",
                    "duration": f"{service['duration_minutes']} min",
                    "availability_status": "available" if available_professionals > 0 else "limited",
                    "availability_text": f"{available_professionals} profesionales" if available_professionals > 0 else "Consultar disponibilidad",
                    "is_emergency": service['is_emergency'],
                    "requires_preparation": service['requires_preparation'],
                    "action_button": {
                        "text": "Seleccionar",
                        "action": f"select_service_{service['id']}"
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
            "general": "GENERAL",
            "especialidad": "ESPECIALIDAD",
            "laboratorio": "LABORATORIO",
            "emergencia": "EMERGENCIA",
            "consulta": "CONSULTA",
            "cirugia": "CIRUGIA",
            "terapia": "TERAPIA"
        }
        return icons.get(category.lower(), "SERVICIO")
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información sobre esta herramienta para OpenAI Function Calling"""
        return {
            "name": "service_consultation_tool",
            "description": "Herramienta para mostrar y consultar servicios médicos disponibles",
            "functions": [
                {
                    "name": "get_available_services",
                    "description": "Obtiene lista de servicios médicos disponibles, opcionalmente filtrados por categoría",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string", 
                                "description": "Categoría de servicios a filtrar (opcional): general, especialidad, laboratorio, emergencia",
                                "enum": ["general", "especialidad", "laboratorio", "emergencia", "consulta", "cirugia", "terapia"]
                            }
                        }
                    }
                },
                {
                    "name": "get_service_details",
                    "description": "Obtiene detalles específicos de un servicio médico por su ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_id": {
                                "type": "string",
                                "description": "ID del servicio del cual obtener detalles"
                            }
                        },
                        "required": ["service_id"]
                    }
                }
            ]
        }