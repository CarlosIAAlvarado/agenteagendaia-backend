"""
Link Management Routes
API endpoints for appointment link management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..controllers.link_management_controller import LinkManagementController
from ...application.use_cases.link_management_use_cases import LinkManagementUseCases
from ...application.dto.link_management_dto import (
    GenerateLinkDTO, AppointmentLinkResponseDTO, ValidateLinkDTO,
    LinkValidationResponseDTO, RescheduleRequestDTO, CancelRequestDTO,
    LinkActionResponseDTO, BulkLinkGenerationDTO, BulkLinkResponseDTO,
    LinkAnalyticsDTO, LinkDashboardDTO, LinkAction
)
from ...infrastructure.dependencies import (
    get_appointment_link_repository, get_appointment_use_cases, get_user_use_cases
)
from ...infrastructure.exceptions import EntityNotFound, BusinessLogicError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/links", tags=["Appointment Links"])


def get_link_management_use_cases(
    link_repository = Depends(get_appointment_link_repository),
    appointment_use_cases = Depends(get_appointment_use_cases),
    user_use_cases = Depends(get_user_use_cases)
) -> LinkManagementUseCases:
    """Get LinkManagementUseCases instance"""
    return LinkManagementUseCases(
        link_repository,
        appointment_use_cases._appointment_repo,
        user_use_cases._user_repo
    )


def get_link_management_controller(
    link_use_cases: LinkManagementUseCases = Depends(get_link_management_use_cases)
) -> LinkManagementController:
    """Get LinkManagementController instance"""
    return LinkManagementController(link_use_cases)


@router.post("/generate", response_model=AppointmentLinkResponseDTO)
async def generate_appointment_link(
    request: GenerateLinkDTO,
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> AppointmentLinkResponseDTO:
    """
    Generate a secure link for appointment management (reschedule, cancel, confirm)
    """
    try:
        return await controller.generate_link(request)
    except EntityNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating link: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/validate/{token}", response_model=LinkValidationResponseDTO)
async def validate_appointment_link(
    token: str,
    request: Request,
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> LinkValidationResponseDTO:
    """
    Validate a secure appointment link and return appointment details
    """
    try:
        # Extract request metadata
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        
        return await controller.validate_link(token, user_agent, ip_address)
    except Exception as e:
        logger.error(f"Unexpected error validating link: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reschedule", response_model=LinkActionResponseDTO)
async def reschedule_via_link(
    request: RescheduleRequestDTO,
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> LinkActionResponseDTO:
    """
    Reschedule an appointment using a secure link
    """
    try:
        return await controller.reschedule_appointment(request)
    except EntityNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error rescheduling appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cancel", response_model=LinkActionResponseDTO)
async def cancel_via_link(
    request: CancelRequestDTO,
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> LinkActionResponseDTO:
    """
    Cancel an appointment using a secure link
    """
    try:
        return await controller.cancel_appointment(request)
    except EntityNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error cancelling appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bulk-generate", response_model=BulkLinkResponseDTO)
async def bulk_generate_links(
    request: BulkLinkGenerationDTO,
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> BulkLinkResponseDTO:
    """
    Generate multiple appointment links in batch
    """
    try:
        return await controller.bulk_generate_links(request)
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error bulk generating links: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics", response_model=LinkAnalyticsDTO)
async def get_link_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> LinkAnalyticsDTO:
    """
    Get comprehensive link usage analytics
    """
    try:
        return await controller.get_link_analytics(days)
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard", response_model=LinkDashboardDTO)
async def get_dashboard_overview(
    period_days: int = Query(30, ge=1, le=365, description="Period in days for analysis"),
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> LinkDashboardDTO:
    """
    Get link management dashboard overview
    """
    try:
        return await controller.get_dashboard_overview(period_days)
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cleanup")
async def cleanup_expired_links(
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> Dict[str, Any]:
    """
    Clean up expired and old links (admin operation)
    """
    try:
        return await controller.cleanup_expired_links()
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/security/{link_id}")
async def get_link_security_events(
    link_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of events to return"),
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> Dict[str, Any]:
    """
    Get security events for a specific link
    """
    try:
        return await controller.get_link_security_events(link_id, limit)
    except Exception as e:
        logger.error(f"Unexpected error getting security events: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}/summary")
async def get_user_links_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> Dict[str, Any]:
    """
    Get summary of links for a specific user
    """
    try:
        return await controller.get_user_links_summary(user_id, days)
    except Exception as e:
        logger.error(f"Unexpected error getting user summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Public link endpoints (accessed by users via email/SMS links)
@router.get("/appointment-link/{action}/{token}")
async def handle_appointment_link(
    action: str,
    token: str,
    request: Request,
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> HTMLResponse:
    """
    Handle appointment link clicks (reschedule/cancel/confirm)
    This endpoint renders a user-friendly interface for link actions
    """
    try:
        # Validate action
        try:
            link_action = LinkAction(action)
        except ValueError:
            return HTMLResponse(
                content=_generate_error_page("Enlace inválido", "La acción solicitada no es válida."),
                status_code=400
            )
        
        # Validate link
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        
        validation = await controller.validate_link(token, user_agent, ip_address)
        
        if not validation.is_valid:
            return HTMLResponse(
                content=_generate_error_page(
                    "Enlace no válido",
                    validation.error_message or "Este enlace no es válido o ha expirado."
                ),
                status_code=400
            )
        
        # Generate appropriate interface based on action
        if link_action == LinkAction.RESCHEDULE:
            return HTMLResponse(
                content=_generate_reschedule_page(validation, token),
                status_code=200
            )
        elif link_action == LinkAction.CANCEL:
            return HTMLResponse(
                content=_generate_cancel_page(validation, token),
                status_code=200
            )
        else:  # CONFIRM
            return HTMLResponse(
                content=_generate_confirm_page(validation, token),
                status_code=200
            )
        
    except Exception as e:
        logger.error(f"Unexpected error handling appointment link: {e}")
        return HTMLResponse(
            content=_generate_error_page(
                "Error interno",
                "Ha ocurrido un error procesando tu solicitud. Por favor, intenta más tarde."
            ),
            status_code=500
        )


@router.get("/health")
async def link_management_health_check(
    controller: LinkManagementController = Depends(get_link_management_controller)
) -> Dict[str, Any]:
    """Health check for link management service"""
    return await controller.health_check()


# Helper functions for HTML generation
def _generate_error_page(title: str, message: str) -> str:
    """Generate error page HTML"""
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Agenda IA</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .error {{ color: #dc2626; text-align: center; }}
            .back-button {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #3b82f6; color: white; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Agenda IA</h1>
            </div>
            <div class="error">
                <h2>{title}</h2>
                <p>{message}</p>
                <a href="mailto:soporte@agenda-ia.com" class="back-button">Contactar Soporte</a>
            </div>
        </div>
    </body>
    </html>
    """


def _generate_reschedule_page(validation: LinkValidationResponseDTO, token: str) -> str:
    """Generate reschedule page HTML"""
    appointment = validation.appointment_details
    user = validation.user_details
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reagendar Cita - Agenda IA</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .appointment-info {{ background: #f8fafc; padding: 20px; border-radius: 6px; margin-bottom: 20px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input, textarea, select {{ width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 4px; box-sizing: border-box; }}
            .submit-button {{ width: 100%; padding: 12px; background: #10b981; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }}
            .submit-button:hover {{ background: #059669; }}
            .cancel-link {{ display: inline-block; margin-top: 10px; color: #6b7280; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Reagendar Cita</h1>
                <p>Hola {user['name']}, puedes reagendar tu cita aquí</p>
            </div>
            
            <div class="appointment-info">
                <h3>Cita Actual</h3>
                <p><strong>Servicio:</strong> {appointment['service_name']}</p>
                <p><strong>Fecha:</strong> {appointment['appointment_date'][:10]}</p>
                <p><strong>Hora:</strong> {appointment['time_slot']}</p>
                <p><strong>Profesional:</strong> {appointment['professional_name']}</p>
            </div>
            
            <form id="rescheduleForm">
                <div class="form-group">
                    <label for="new_date">Nueva Fecha:</label>
                    <input type="date" id="new_date" name="new_date" required min="{(datetime.utcnow()).strftime('%Y-%m-%d')}">
                </div>
                
                <div class="form-group">
                    <label for="new_time">Nueva Hora:</label>
                    <select id="new_time" name="new_time" required>
                        <option value="">Selecciona una hora</option>
                        <option value="09:00">9:00 AM</option>
                        <option value="10:00">10:00 AM</option>
                        <option value="11:00">11:00 AM</option>
                        <option value="14:00">2:00 PM</option>
                        <option value="15:00">3:00 PM</option>
                        <option value="16:00">4:00 PM</option>
                        <option value="17:00">5:00 PM</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="reason">Motivo del cambio (opcional):</label>
                    <textarea id="reason" name="reason" rows="3" placeholder="Ej: Conflicto de horario"></textarea>
                </div>
                
                <button type="submit" class="submit-button">Reagendar Cita</button>
            </form>
            
            <a href="#" class="cancel-link">Cancelar (mantener cita actual)</a>
        </div>
        
        <script>
            document.getElementById('rescheduleForm').addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = {{
                    link_token: '{token}',
                    new_date: formData.get('new_date') + 'T' + formData.get('new_time') + ':00',
                    new_time_slot: formData.get('new_time'),
                    reason: formData.get('reason')
                }};
                
                try {{
                    const response = await fetch('/api/v1/links/reschedule', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    
                    if (response.ok) {{
                        const result = await response.json();
                        alert('¡Cita reagendada exitosamente! ' + result.message);
                        window.close();
                    }} else {{
                        const error = await response.json();
                        alert('Error: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('Error de conexión. Por favor, intenta nuevamente.');
                }}
            }});
        </script>
    </body>
    </html>
    """


def _generate_cancel_page(validation: LinkValidationResponseDTO, token: str) -> str:
    """Generate cancel page HTML"""
    appointment = validation.appointment_details
    user = validation.user_details
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cancelar Cita - Agenda IA</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .appointment-info {{ background: #f8fafc; padding: 20px; border-radius: 6px; margin-bottom: 20px; }}
            .warning {{ background: #fef3cd; border: 1px solid #facc15; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            select, textarea {{ width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 4px; box-sizing: border-box; }}
            .cancel-button {{ width: 100%; padding: 12px; background: #dc2626; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }}
            .cancel-button:hover {{ background: #b91c1c; }}
            .keep-link {{ display: inline-block; margin-top: 10px; color: #6b7280; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Cancelar Cita</h1>
                <p>Hola {user['name']}, ¿estás seguro que deseas cancelar tu cita?</p>
            </div>
            
            <div class="appointment-info">
                <h3>Información de la Cita</h3>
                <p><strong>Servicio:</strong> {appointment['service_name']}</p>
                <p><strong>Fecha:</strong> {appointment['appointment_date'][:10]}</p>
                <p><strong>Hora:</strong> {appointment['time_slot']}</p>
                <p><strong>Profesional:</strong> {appointment['professional_name']}</p>
            </div>
            
            <div class="warning">
                <strong>Importante:</strong> La cancelación de tu cita liberará el espacio para otros usuarios. Si cambias de opinión, necesitarás agendar una nueva cita.
            </div>
            
            <form id="cancelForm">
                <div class="form-group">
                    <label for="reason">Motivo de cancelación:</label>
                    <select id="reason" name="reason" required>
                        <option value="">Selecciona un motivo</option>
                        <option value="Personal emergency">Emergencia personal</option>
                        <option value="Schedule conflict">Conflicto de horario</option>
                        <option value="Feeling unwell">No me siento bien</option>
                        <option value="No longer needed">Ya no necesito el servicio</option>
                        <option value="Other">Otro motivo</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="feedback">Comentarios adicionales (opcional):</label>
                    <textarea id="feedback" name="feedback" rows="3" placeholder="Cuéntanos más sobre tu cancelación..."></textarea>
                </div>
                
                <div class="form-group">
                    <label for="rating">¿Cómo calificarías tu experiencia hasta ahora? (opcional):</label>
                    <select id="rating" name="rating">
                        <option value="">No calificar</option>
                        <option value="5">Excelente (5)</option>
                        <option value="4">Buena (4)</option>
                        <option value="3">Regular (3)</option>
                        <option value="2">Mala (2)</option>
                        <option value="1">Muy mala (1)</option>
                    </select>
                </div>
                
                <button type="submit" class="cancel-button">Cancelar Cita</button>
            </form>
            
            <a href="#" class="keep-link">Mantener cita (no cancelar)</a>
        </div>
        
        <script>
            document.getElementById('cancelForm').addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                if (!confirm('¿Estás seguro que deseas cancelar esta cita?')) {{
                    return;
                }}
                
                const formData = new FormData(e.target);
                const data = {{
                    link_token: '{token}',
                    reason: formData.get('reason'),
                    feedback_comment: formData.get('feedback'),
                    feedback_rating: formData.get('rating') ? parseInt(formData.get('rating')) : null
                }};
                
                try {{
                    const response = await fetch('/api/v1/links/cancel', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    
                    if (response.ok) {{
                        const result = await response.json();
                        alert('Cita cancelada exitosamente. ' + result.message);
                        window.close();
                    }} else {{
                        const error = await response.json();
                        alert('Error: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('Error de conexión. Por favor, intenta nuevamente.');
                }}
            }});
        </script>
    </body>
    </html>
    """


def _generate_confirm_page(validation: LinkValidationResponseDTO, token: str) -> str:
    """Generate confirm page HTML"""
    appointment = validation.appointment_details
    user = validation.user_details
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Confirmar Cita - Agenda IA</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .appointment-info {{ background: #f0f9ff; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #3b82f6; }}
            .confirm-button {{ width: 100%; padding: 12px; background: #10b981; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; margin-bottom: 10px; }}
            .confirm-button:hover {{ background: #059669; }}
            .reschedule-button {{ width: 100%; padding: 12px; background: #3b82f6; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }}
            .reschedule-button:hover {{ background: #2563eb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Confirmar Cita</h1>
                <p>Hola {user['name']}, por favor confirma tu cita</p>
            </div>
            
            <div class="appointment-info">
                <h3>Detalles de tu Cita</h3>
                <p><strong>Servicio:</strong> {appointment['service_name']}</p>
                <p><strong>Fecha:</strong> {appointment['appointment_date'][:10]}</p>
                <p><strong>Hora:</strong> {appointment['time_slot']}</p>
                <p><strong>Profesional:</strong> {appointment['professional_name']}</p>
                <p><strong>Duración:</strong> {appointment['duration_minutes']} minutos</p>
            </div>
            
            <button onclick="confirmAppointment()" class="confirm-button">✓ Confirmar Cita</button>
            <button onclick="rescheduleInstead()" class="reschedule-button">📅 Reagendar en su lugar</button>
        </div>
        
        <script>
            function confirmAppointment() {{
                if (confirm('¿Confirmas que asistirás a esta cita?')) {{
                    // In a real implementation, this would make an API call
                    alert('¡Cita confirmada exitosamente! Te esperamos.');
                    window.close();
                }}
            }}
            
            function rescheduleInstead() {{
                if (confirm('¿Deseas reagendar esta cita en su lugar?')) {{
                    // Redirect to reschedule flow
                    window.location.href = window.location.href.replace('/confirm/', '/reschedule/');
                }}
            }}
        </script>
    </body>
    </html>
    """