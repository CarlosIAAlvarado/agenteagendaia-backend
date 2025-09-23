"""
Herramienta de IA para cancelamiento de citas
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId
from ..ai_tools.email_notification_tool import EmailNotificationTool
from ...entities.appointment import AppointmentStatus

class AppointmentCancellationTool:
    def __init__(self, appointment_repository, professional_repository, service_repository, user_repository):
        self.appointment_repository = appointment_repository
        self.professional_repository = professional_repository
        self.service_repository = service_repository
        self.user_repository = user_repository
        self.email_tool = EmailNotificationTool(
            user_repository, appointment_repository
        )

    async def start_cancellation_process(self, appointment_id: str, user_id: Optional[str] = None, user_message: str = "") -> Dict[str, Any]:
        """
        Inicia el proceso de cancelación de una cita

        Args:
            appointment_id: ID de la cita a cancelar
            user_id: ID del usuario (opcional)
            user_message: Mensaje del usuario solicitando cancelación

        Returns:
            Dict con información de la cita y opciones de cancelación
        """
        try:
            print(f"🚫 [CANCELLATION_START] Processing cancellation for appointment: {appointment_id}")

            # Validar formato del ID
            if not ObjectId.is_valid(appointment_id):
                return {
                    "success": False,
                    "message": "ID de cita inválido. Por favor verifica el ID e intenta nuevamente.",
                    "display_type": "error"
                }

            # Buscar la cita
            appointment = await self.appointment_repository.get_by_id(appointment_id)
            if not appointment:
                return {
                    "success": False,
                    "message": "No se encontró una cita con ese ID. Por favor verifica el ID e intenta nuevamente.",
                    "display_type": "error"
                }

            # Verificar que la cita no esté ya cancelada
            if appointment.status == AppointmentStatus.CANCELLED:
                return {
                    "success": False,
                    "message": "Esta cita ya fue cancelada anteriormente.",
                    "display_type": "error"
                }

            # Verificar que la cita no sea en el pasado
            appointment_datetime = appointment.appointment_date
            if isinstance(appointment_datetime, str):
                appointment_datetime = datetime.fromisoformat(appointment_datetime.replace('Z', '+00:00'))

            if appointment_datetime and appointment_datetime.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                return {
                    "success": False,
                    "message": "No se pueden cancelar citas que ya pasaron.",
                    "display_type": "error"
                }

            # Obtener información adicional
            service_info = {}
            professional_info = {}

            try:
                if appointment.service_id:
                    service = await self.service_repository.get_by_id(appointment.service_id)
                    if service:
                        service_info = {
                            "name": service.name,
                            "duration": service.duration_minutes,
                            "price": service.price
                        }

                if appointment.professional_id:
                    professional = await self.professional_repository.get_by_id(appointment.professional_id)
                    if professional:
                        professional_info = {
                            "name": professional.name,
                            "specialty": getattr(professional, 'specialty', 'General')
                        }
            except Exception as e:
                print(f"⚠️ [CANCELLATION_INFO] Error getting additional info: {e}")

            # Formatear fecha y hora para mostrar
            if not appointment.appointment_date:
                formatted_date = "Fecha no asignada"
                formatted_time = "Hora no asignada"
            else:
                if isinstance(appointment.appointment_date, str):
                    date_obj = datetime.fromisoformat(appointment.appointment_date.replace('Z', '+00:00'))
                else:
                    date_obj = appointment.appointment_date

                formatted_date = date_obj.strftime("%A, %d de %B de %Y")
                formatted_time = date_obj.strftime("%I:%M %p")

            # Preparar respuesta con información de la cita
            cancellation_data = {
                "appointment_id": appointment_id,
                "date": formatted_date,
                "time": formatted_time,
                "service_name": service_info.get("name", "Servicio no especificado"),
                "professional_name": professional_info.get("name", "Profesional no especificado"),
                "status": appointment.status.value,  # Convert enum to string
                "user_email": appointment.user_email,
                "user_name": appointment.user_name
            }

            response_message = f"""📅 **Información de tu cita**

**Servicio:** {cancellation_data['service_name']}
**Profesional:** {cancellation_data['professional_name']}
**Fecha:** {cancellation_data['date']}
**Hora:** {cancellation_data['time']}

¿Estás seguro de que deseas cancelar esta cita?"""

            return {
                "success": True,
                "message": response_message,
                "display_type": "cancellation_confirmation",
                "cancellation_data": cancellation_data
            }

        except Exception as e:
            print(f"❌ [CANCELLATION_ERROR] Error in start_cancellation_process: {e}")
            return {
                "success": False,
                "message": "Ocurrió un error al procesar la solicitud de cancelación. Por favor intenta nuevamente.",
                "display_type": "error"
            }

    async def confirm_cancellation(self, appointment_id: str, cancellation_reason: str = "", user_confirmation: str = "yes") -> Dict[str, Any]:
        """
        Confirma y ejecuta la cancelación de la cita

        Args:
            appointment_id: ID de la cita a cancelar
            cancellation_reason: Razón de la cancelación (opcional)
            user_confirmation: Confirmación del usuario

        Returns:
            Dict con resultado de la cancelación
        """
        try:
            print(f"🚫 [CANCELLATION_CONFIRM] Confirming cancellation for appointment: {appointment_id}")

            if user_confirmation.lower() not in ["yes", "sí", "si", "confirmar", "cancelar"]:
                return {
                    "success": False,
                    "message": "Cancelación cancelada. Tu cita se mantiene programada.",
                    "display_type": "cancellation_cancelled"
                }

            # Buscar la cita nuevamente
            appointment = await self.appointment_repository.get_by_id(appointment_id)
            if not appointment:
                return {
                    "success": False,
                    "message": "No se encontró la cita para cancelar.",
                    "display_type": "error"
                }

            # Verificar que la cita no esté ya cancelada
            if appointment.status == AppointmentStatus.CANCELLED:
                return {
                    "success": False,
                    "message": "Esta cita ya fue cancelada anteriormente.",
                    "display_type": "error"
                }

            # Obtener información antes de cancelar (para el email)
            service_info = {"name": "Servicio no especificado", "duration": 30, "price": 0}
            professional_info = {"name": "Profesional no especificado"}

            try:
                if appointment.service_id:
                    service = await self.service_repository.get_by_id(appointment.service_id)
                    if service:
                        service_info = {
                            "name": service.name,
                            "duration": service.duration_minutes,
                            "price": service.price
                        }

                if appointment.professional_id:
                    professional = await self.professional_repository.get_by_id(appointment.professional_id)
                    if professional:
                        professional_info = {
                            "name": professional.name,
                            "specialty": getattr(professional, 'specialty', 'General')
                        }
            except Exception as e:
                print(f"⚠️ [CANCELLATION_INFO] Error getting info for email: {e}")

            # Actualizar el status de la cita a cancelada usando el método del entity
            appointment.cancel()
            appointment.cancellation_reason = cancellation_reason
            appointment.cancelled_at = datetime.now(timezone.utc)

            # Guardar los cambios
            updated_appointment = await self.appointment_repository.update(appointment)

            if not updated_appointment:
                return {
                    "success": False,
                    "message": "Error al cancelar la cita. Por favor intenta nuevamente.",
                    "display_type": "error"
                }

            # Formatear fecha para el mensaje
            if not appointment.appointment_date:
                formatted_date = "Fecha no asignada"
                formatted_time = "Hora no asignada"
            else:
                if isinstance(appointment.appointment_date, str):
                    date_obj = datetime.fromisoformat(appointment.appointment_date.replace('Z', '+00:00'))
                else:
                    date_obj = appointment.appointment_date

                formatted_date = date_obj.strftime("%A, %d de %B de %Y")
                formatted_time = date_obj.strftime("%I:%M %p")

            # Enviar email de confirmación de cancelación
            try:
                print(f"📧 [CANCELLATION_EMAIL] Preparing email data for {appointment.user_email}")

                # Ensure email is not None
                user_email = appointment.user_email
                if not user_email:
                    print(f"❌ [CANCELLATION_EMAIL] No email found in appointment. user_email is None")
                    # Try to get email from user record if possible
                    try:
                        if hasattr(appointment, 'user_id') and appointment.user_id:
                            user = await self.user_repository.get_by_id(appointment.user_id)
                            if user and hasattr(user, 'email'):
                                user_email = user.email
                                print(f"📧 [CANCELLATION_EMAIL] Found email from user record: {user_email}")
                    except Exception as email_lookup_error:
                        print(f"❌ [CANCELLATION_EMAIL] Error looking up user email: {email_lookup_error}")

                if user_email:
                    email_data = {
                        "user_email": user_email,
                        "user_name": appointment.user_name or "Usuario",
                        "service_name": service_info["name"],
                        "professional_name": professional_info["name"],
                        "date": formatted_date,
                        "time": formatted_time,
                        "cancellation_reason": cancellation_reason or "No especificada"
                    }

                    print(f"📧 [CANCELLATION_EMAIL] Sending email to: {user_email}")
                    await self.email_tool.send_cancellation_email(email_data)
                    print(f"📧 [CANCELLATION_EMAIL] Cancellation email sent successfully")
                else:
                    print(f"❌ [CANCELLATION_EMAIL] No valid email found for user")

            except Exception as e:
                print(f"❌ [CANCELLATION_EMAIL] Error sending cancellation email: {e}")
                # Continuar aunque falle el email

            # Preparar mensaje de éxito con estado del email
            email_status = ""
            if user_email:
                email_status = f"\nSe ha enviado un email de confirmación a **{user_email}**."
            else:
                email_status = f"\nNo se pudo enviar email de confirmación (no hay email registrado)."

            success_message = f"""✅ **Cita cancelada exitosamente**

Tu cita del **{formatted_date}** a las **{formatted_time}** ha sido cancelada.{email_status}

¿Hay algo más en lo que pueda ayudarte?"""

            return {
                "success": True,
                "message": success_message,
                "display_type": "cancellation_success",
                "cancelled_appointment": {
                    "appointment_id": appointment_id,
                    "date": formatted_date,
                    "time": formatted_time,
                    "service_name": service_info["name"],
                    "professional_name": professional_info["name"],
                    "cancellation_reason": cancellation_reason
                }
            }

        except Exception as e:
            print(f"❌ [CANCELLATION_CONFIRM_ERROR] Error in confirm_cancellation: {e}")
            return {
                "success": False,
                "message": "Ocurrió un error al cancelar la cita. Por favor intenta nuevamente.",
                "display_type": "error"
            }