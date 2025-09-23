import aiosmtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Template

from ...entities.email_config import EmailConfig
from ...entities.company_config import CompanyConfig
from ...repositories.user_repository import IUserRepository
from ...repositories.appointment_repository import IAppointmentRepository

logger = logging.getLogger(__name__)


class EmailNotificationTool:
    """AI Tool for sending email notifications about appointments"""

    def __init__(
        self,
        user_repository: IUserRepository,
        appointment_repository: IAppointmentRepository,
        email_config: Optional[EmailConfig] = None,
        company_config: Optional[CompanyConfig] = None
    ):
        self.user_repo = user_repository
        self.appointment_repo = appointment_repository
        self.email_config = email_config
        self.company_config = company_config

    async def _load_configurations(self):
        """Load email and company configurations dynamically"""
        try:
            # Import here to avoid circular imports
            from ....infrastructure.database.repositories.email_config_repository_impl import EmailConfigRepositoryImpl
            from ....infrastructure.database.repositories.company_config_repository_impl import CompanyConfigRepositoryImpl

            if not self.email_config:
                email_repo = EmailConfigRepositoryImpl()
                self.email_config = await email_repo.get_current_config()

            if not self.company_config:
                company_repo = CompanyConfigRepositoryImpl()
                self.company_config = await company_repo.get_current_config()

        except Exception as e:
            logger.error(f"Error loading email/company configurations: {e}")

    async def send_appointment_confirmation_email(
        self,
        user_id: str,
        appointment_id: str,
        email_type: str = "confirmation",
        reschedule_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send appointment confirmation email to user
        This is the main function called by the AI agent
        """
        try:
            logger.info(f"🏁 [EMAIL_TOOL] Starting email notification for appointment {appointment_id}")

            # Load configurations if not available
            await self._load_configurations()

            # Check if configurations are available
            if not self.email_config:
                logger.warning("📧 [EMAIL_TOOL] Email configuration not found")
                return {
                    "success": False,
                    "error": "email_config_not_found",
                    "message": "Configuración de email no encontrada",
                    "user_notification": None
                }

            if not self.company_config:
                logger.warning("📧 [EMAIL_TOOL] Company configuration not found, using defaults")
                # Create a default company config
                from ...entities.company_config import CompanyConfig
                from datetime import datetime
                self.company_config = CompanyConfig(
                    id="default",
                    company_name="Agenda IA",
                    created_at=datetime.utcnow()
                )

            # Check if email is enabled
            if not self.email_config.email_enabled:
                logger.info("📧 [EMAIL_TOOL] Email notifications are disabled")
                return {
                    "success": False,
                    "error": "email_disabled",
                    "message": "Las notificaciones por email están deshabilitadas",
                    "user_notification": None
                }

            # Get user data
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                logger.error(f"❌ [EMAIL_TOOL] User {user_id} not found")
                return {
                    "success": False,
                    "error": "user_not_found",
                    "message": "Usuario no encontrado",
                    "user_notification": None
                }

            # Get appointment data
            appointment = await self.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                logger.error(f"❌ [EMAIL_TOOL] Appointment {appointment_id} not found")
                return {
                    "success": False,
                    "error": "appointment_not_found",
                    "message": "Cita no encontrada",
                    "user_notification": None
                }

            # Extract user email
            user_email = None
            if hasattr(user, 'email'):
                if hasattr(user.email, 'value'):
                    user_email = user.email.value
                else:
                    user_email = str(user.email)

            if not user_email:
                logger.error(f"❌ [EMAIL_TOOL] No email found for user {user_id}")
                return {
                    "success": False,
                    "error": "no_email",
                    "message": "El usuario no tiene email registrado",
                    "user_notification": "No pude enviar el email porque no tienes un email registrado."
                }

            # Get service and professional details if not populated
            service_name = getattr(appointment, 'service_name', None)
            professional_name = getattr(appointment, 'professional_name', None)

            # If service_name is None or empty, try to get from service repository
            if not service_name and hasattr(appointment, 'service_id') and appointment.service_id:
                try:
                    from ....infrastructure.database.repositories.service_repository_impl import ServiceRepositoryImpl
                    service_repo = ServiceRepositoryImpl()
                    service = await service_repo.get_by_id(appointment.service_id)
                    if service:
                        service_name = service.name
                except Exception as e:
                    logger.warning(f"Could not fetch service name: {e}")

            # If professional_name is None or empty, try to get from professional repository
            if not professional_name and hasattr(appointment, 'professional_id') and appointment.professional_id:
                try:
                    from ....infrastructure.database.repositories.professional_repository_impl import ProfessionalRepositoryImpl
                    professional_repo = ProfessionalRepositoryImpl()
                    professional = await professional_repo.get_by_id(appointment.professional_id)
                    if professional:
                        professional_name = professional.name
                except Exception as e:
                    logger.warning(f"Could not fetch professional name: {e}")

            # Prepare appointment data for template
            appointment_data = {
                "id": appointment.id,
                "service_name": service_name or 'Servicio no especificado',
                "date": appointment.appointment_date.strftime("%A %d de %B, %Y") if appointment.appointment_date else "Fecha no especificada",
                "time": appointment.appointment_date.strftime("%H:%M") if appointment.appointment_date else "Hora no especificada",
                "professional_name": professional_name or 'Por asignar',
                "duration_minutes": getattr(appointment, 'duration_minutes', 30),
                "price": getattr(appointment, 'price', 0),
                "status": "Confirmada"
            }

            # Add reschedule data if provided (for reschedule emails)
            if reschedule_data and email_type == "reschedule":
                appointment_data.update({
                    "old_date": reschedule_data.get("old_date", "N/A"),
                    "old_time": reschedule_data.get("old_time", "N/A"),
                    "new_date": reschedule_data.get("new_date", appointment_data["date"]),
                    "new_time": reschedule_data.get("new_time", appointment_data["time"])
                })

            logger.info(f"📧 [EMAIL_TOOL] Sending {email_type} email to {user_email}")

            # Generate email template
            email_template = self._generate_email_template(
                user_name=user.name,
                appointment_data=appointment_data,
                email_type=email_type
            )

            # Send email
            email_result = await self._send_email(
                to_email=user_email,
                subject=email_template["subject"],
                html_body=email_template["html_body"],
                text_body=email_template["text_body"]
            )

            if email_result["success"]:
                logger.info(f"✅ [EMAIL_TOOL] Email sent successfully to {user_email}")
                return {
                    "success": True,
                    "email_sent": True,
                    "recipient_email": user_email,
                    "email_type": email_type,
                    "message": f"Email de confirmación enviado exitosamente a {user_email}",
                    "user_notification": f"📧 Te envié los detalles de tu cita por email a: {user_email}",
                    "tool_used": "email_notification",
                    "display_type": "email_confirmation"
                }
            else:
                logger.error(f"❌ [EMAIL_TOOL] Failed to send email: {email_result.get('error')}")
                return {
                    "success": False,
                    "error": "email_send_failed",
                    "message": f"Error enviando email: {email_result.get('error', 'Error desconocido')}",
                    "user_notification": "No pude enviar el email de confirmación, pero tu cita está confirmada."
                }

        except Exception as e:
            logger.error(f"❌ [EMAIL_TOOL] Unexpected error: {e}")
            return {
                "success": False,
                "error": f"email_tool_error: {str(e)}",
                "message": "Error interno enviando email",
                "user_notification": "Hubo un problema enviando el email, pero tu cita está confirmada."
            }

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str
    ) -> Dict[str, Any]:
        """Send email using SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.email_config.email_from_name} <{self.email_config.email_from_address.value}>"
            message["To"] = to_email

            # Add text and HTML parts
            text_part = MIMEText(text_body, "plain", "utf-8")
            html_part = MIMEText(html_body, "html", "utf-8")

            message.attach(text_part)
            message.attach(html_part)

            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.email_config.smtp_server,
                port=self.email_config.smtp_port,
                start_tls=self.email_config.use_tls,
                timeout=30
            ) as smtp:
                await smtp.login(
                    self.email_config.smtp_username,
                    self.email_config.smtp_password
                )
                await smtp.send_message(message)

            logger.info(f"📧 Email sent successfully to {to_email}")
            return {
                "success": True,
                "message": "Email sent successfully"
            }

        except Exception as e:
            logger.error(f"❌ SMTP Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_email_template(
        self,
        user_name: str,
        appointment_data: Dict[str, Any],
        email_type: str = "confirmation"
    ) -> Dict[str, str]:
        """Generate email template for appointment confirmation"""

        if email_type == "confirmation":
            return self._get_confirmation_template(user_name, appointment_data)
        elif email_type == "reminder":
            return self._get_reminder_template(user_name, appointment_data)
        elif email_type == "cancellation":
            return self._get_cancellation_template(user_name, appointment_data)
        elif email_type == "reschedule":
            return self._get_reschedule_template(user_name, appointment_data)
        else:
            return self._get_confirmation_template(user_name, appointment_data)

    def _get_confirmation_template(
        self,
        user_name: str,
        appointment_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate appointment confirmation email template"""

        subject = f"✅ Cita Confirmada - {appointment_data.get('service_name', 'Servicio')}"

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #059669; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }
        .content { background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
        .appointment-details { background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .detail-label { font-weight: bold; color: #059669; }
        .footer { text-align: center; margin-top: 30px; font-size: 14px; color: #666; }
        .success-icon { font-size: 48px; text-align: center; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 ¡Cita Confirmada!</h1>
            <p>Tu cita ha sido programada exitosamente</p>
        </div>

        <div class="content">
            <div class="success-icon">✅</div>

            <p>Hola <strong>{{ user_name }}</strong>,</p>

            <p>Tu cita ha sido <strong>confirmada exitosamente</strong>. Aquí están los detalles:</p>

            <div class="appointment-details">
                <h3 style="color: #059669; margin-top: 0;">📋 Detalles de la Cita</h3>

                <div class="detail-row">
                    <span class="detail-label">🏥 Servicio:</span>
                    <span>{{ service_name }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">📅 Fecha:</span>
                    <span>{{ date }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">🕐 Hora:</span>
                    <span>{{ time }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">👨‍⚕️ Profesional:</span>
                    <span>{{ professional_name }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">⏱️ Duración:</span>
                    <span>{{ duration_minutes }} minutos</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">💰 Precio:</span>
                    <span>${{ "{:,}".format(price) }} COP</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">🆔 ID de Cita:</span>
                    <span>{{ appointment_id }}</span>
                </div>
            </div>

            <div style="background-color: #e0f2fe; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #0277bd;">📱 Recordatorios</h4>
                <p style="margin-bottom: 0;">Te enviaremos recordatorios por email antes de tu cita.</p>
            </div>

            <div style="background-color: #fff3cd; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #856404;">ℹ️ Información Importante</h4>
                <ul style="margin-bottom: 0;">
                    <li>Llega 10 minutos antes de tu cita</li>
                    <li>Trae tu documento de identidad</li>
                    <li>Si necesitas cancelar, hazlo con al menos 24 horas de anticipación</li>
                </ul>
            </div>
        </div>

        <div class="footer">
            <p>🏥 <strong>{{ company_name }}</strong></p>
            <p>Este email fue enviado automáticamente. No respondas a este mensaje.</p>
            <p style="font-size: 12px;">Generado el {{ current_datetime }}</p>
        </div>
    </div>
</body>
</html>
        """

        text_template = """
🎉 ¡CITA CONFIRMADA!

Hola {{ user_name }},

Tu cita ha sido confirmada exitosamente. Aquí están los detalles:

📋 DETALLES DE LA CITA:
🏥 Servicio: {{ service_name }}
📅 Fecha: {{ date }}
🕐 Hora: {{ time }}
👨‍⚕️ Profesional: {{ professional_name }}
⏱️ Duración: {{ duration_minutes }} minutos
💰 Precio: ${{ "{:,}".format(price) }} COP
🆔 ID de Cita: {{ appointment_id }}

📱 RECORDATORIOS:
Te enviaremos recordatorios por email antes de tu cita.

ℹ️ INFORMACIÓN IMPORTANTE:
- Llega 10 minutos antes de tu cita
- Trae tu documento de identidad
- Si necesitas cancelar, hazlo con al menos 24 horas de anticipación

¡Te esperamos!

🏥 {{ company_name }}
Este email fue enviado automáticamente.
Generado el {{ current_datetime }}
        """

        # Prepare template data
        template_data = {
            "user_name": user_name,
            "service_name": appointment_data.get('service_name', 'N/A'),
            "date": appointment_data.get('date', 'N/A'),
            "time": appointment_data.get('time', 'N/A'),
            "professional_name": appointment_data.get('professional_name', 'Por asignar'),
            "duration_minutes": appointment_data.get('duration_minutes', 30),
            "price": appointment_data.get('price', 0),
            "appointment_id": appointment_data.get('id', 'N/A'),
            "company_name": self.company_config.company_name,
            "current_datetime": datetime.now().strftime("%d/%m/%Y a las %H:%M")
        }

        # Render templates
        html_body = Template(html_template).render(**template_data)
        text_body = Template(text_template).render(**template_data)

        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body
        }

    async def send_cancellation_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía email de confirmación de cancelación de cita

        Args:
            email_data: Datos del email con información de la cita cancelada

        Returns:
            Dict con resultado del envío
        """
        try:
            print(f"📧 [CANCELLATION_EMAIL] Preparing cancellation email for {email_data.get('user_email')}")

            # Generar template de cancelación
            email_template = self._generate_cancellation_email_template(
                email_data.get('user_name', 'Usuario'),
                email_data
            )

            # Enviar email
            result = await self._send_email(
                to_email=email_data.get('user_email'),
                subject=email_template['subject'],
                html_body=email_template['html_body'],
                text_body=email_template['text_body']
            )

            if result['success']:
                print(f"✅ [CANCELLATION_EMAIL] Email sent successfully to {email_data.get('user_email')}")
                return {
                    "success": True,
                    "message": "Email de cancelación enviado exitosamente",
                    "email_sent_to": email_data.get('user_email')
                }
            else:
                print(f"❌ [CANCELLATION_EMAIL] Failed to send email: {result.get('error')}")
                return {
                    "success": False,
                    "message": f"Error enviando email: {result.get('error')}",
                    "error": result.get('error')
                }

        except Exception as e:
            print(f"❌ [CANCELLATION_EMAIL] Error in send_cancellation_email: {e}")
            return {
                "success": False,
                "message": f"Error enviando email de cancelación: {str(e)}",
                "error": str(e)
            }

    def _generate_cancellation_email_template(
        self,
        user_name: str,
        appointment_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate appointment cancellation email template"""

        subject = f"🚫 Cita Cancelada - {appointment_data.get('service_name', 'Servicio')}"

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #dc2626; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }
        .content { background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
        .appointment-details { background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .detail-label { font-weight: bold; color: #dc2626; }
        .footer { text-align: center; margin-top: 30px; font-size: 14px; color: #666; }
        .cancellation-icon { font-size: 48px; text-align: center; margin: 20px 0; }
        .reason-box { background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚫 Cita Cancelada</h1>
            <p>Tu cita ha sido cancelada exitosamente</p>
        </div>

        <div class="content">
            <div class="cancellation-icon">❌</div>

            <p>Hola <strong>{{ user_name }}</strong>,</p>

            <p>Tu cita ha sido <strong>cancelada exitosamente</strong>. A continuación los detalles de la cita cancelada:</p>

            <div class="appointment-details">
                <h3 style="color: #dc2626; margin-top: 0;">📋 Detalles de la Cita Cancelada</h3>

                <div class="detail-row">
                    <span class="detail-label">🏥 Servicio:</span>
                    <span>{{ service_name }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">📅 Fecha:</span>
                    <span>{{ date }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">🕐 Hora:</span>
                    <span>{{ time }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">👨‍⚕️ Profesional:</span>
                    <span>{{ professional_name }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">🚫 Estado:</span>
                    <span style="color: #dc2626; font-weight: bold;">CANCELADA</span>
                </div>
            </div>

            {% if cancellation_reason %}
            <div class="reason-box">
                <strong>📝 Razón de cancelación:</strong><br>
                {{ cancellation_reason }}
            </div>
            {% endif %}

            <div style="background-color: #e0f2fe; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #0277bd; margin-top: 0;">💡 ¿Necesitas programar una nueva cita?</h3>
                <p>Puedes agendar una nueva cita cuando desees a través de nuestro sistema de chat.</p>
                <p>Estaremos encantados de atenderte en una nueva oportunidad.</p>
            </div>

            <p>Gracias por informarnos sobre la cancelación.</p>
            <p><strong>{{ company_name }}</strong></p>
        </div>

        <div class="footer">
            <p>Este email fue enviado automáticamente.</p>
            <p>Generado el {{ current_datetime }}</p>
        </div>
    </div>
</body>
</html>
        """

        text_template = """
🚫 CITA CANCELADA

Hola {{ user_name }},

Tu cita ha sido CANCELADA exitosamente.

📋 DETALLES DE LA CITA CANCELADA:
🏥 Servicio: {{ service_name }}
📅 Fecha: {{ date }}
🕐 Hora: {{ time }}
👨‍⚕️ Profesional: {{ professional_name }}
🚫 Estado: CANCELADA

{% if cancellation_reason %}📝 Razón de cancelación: {{ cancellation_reason }}{% endif %}

💡 ¿NECESITAS PROGRAMAR UNA NUEVA CITA?
Puedes agendar una nueva cita cuando desees a través de nuestro sistema de chat.
Estaremos encantados de atenderte en una nueva oportunidad.

Gracias por informarnos sobre la cancelación.

🏥 {{ company_name }}
Este email fue enviado automáticamente.
Generado el {{ current_datetime }}
        """

        # Prepare template data
        template_data = {
            "user_name": user_name,
            "service_name": appointment_data.get('service_name', 'N/A'),
            "date": appointment_data.get('date', 'N/A'),
            "time": appointment_data.get('time', 'N/A'),
            "professional_name": appointment_data.get('professional_name', 'Por asignar'),
            "cancellation_reason": appointment_data.get('cancellation_reason', ''),
            "company_name": self.company_config.company_name,
            "current_datetime": datetime.now().strftime("%d/%m/%Y a las %H:%M")
        }

        # Render templates
        html_body = Template(html_template).render(**template_data)
        text_body = Template(text_template).render(**template_data)

        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body
        }

    def _get_reminder_template(self, user_name: str, appointment_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate appointment reminder email template"""
        # Simplified reminder template
        subject = f"🔔 Recordatorio de Cita - {appointment_data.get('service_name', 'Servicio')}"

        html_body = f"""
        <h2>🔔 Recordatorio de Cita</h2>
        <p>Hola {user_name},</p>
        <p>Te recordamos que tienes una cita programada:</p>
        <ul>
            <li><strong>Servicio:</strong> {appointment_data.get('service_name', 'N/A')}</li>
            <li><strong>Fecha:</strong> {appointment_data.get('date', 'N/A')}</li>
            <li><strong>Hora:</strong> {appointment_data.get('time', 'N/A')}</li>
        </ul>
        <p>¡Te esperamos!</p>
        """

        text_body = f"""
        🔔 RECORDATORIO DE CITA

        Hola {user_name},

        Te recordamos que tienes una cita programada:

        Servicio: {appointment_data.get('service_name', 'N/A')}
        Fecha: {appointment_data.get('date', 'N/A')}
        Hora: {appointment_data.get('time', 'N/A')}

        ¡Te esperamos!
        """

        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body
        }

    def _get_cancellation_template(self, user_name: str, appointment_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate appointment cancellation email template"""
        # Simplified cancellation template
        subject = f"❌ Cita Cancelada - {appointment_data.get('service_name', 'Servicio')}"

        html_body = f"""
        <h2>❌ Cita Cancelada</h2>
        <p>Hola {user_name},</p>
        <p>Tu cita ha sido cancelada:</p>
        <ul>
            <li><strong>Servicio:</strong> {appointment_data.get('service_name', 'N/A')}</li>
            <li><strong>Fecha:</strong> {appointment_data.get('date', 'N/A')}</li>
            <li><strong>Hora:</strong> {appointment_data.get('time', 'N/A')}</li>
        </ul>
        <p>Si necesitas agendar una nueva cita, contáctanos.</p>
        """

        text_body = f"""
        ❌ CITA CANCELADA

        Hola {user_name},

        Tu cita ha sido cancelada:

        Servicio: {appointment_data.get('service_name', 'N/A')}
        Fecha: {appointment_data.get('date', 'N/A')}
        Hora: {appointment_data.get('time', 'N/A')}

        Si necesitas agendar una nueva cita, contáctanos.
        """

        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body
        }

    def _get_reschedule_template(
        self,
        user_name: str,
        appointment_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate appointment reschedule email template"""

        subject = f"🔄 Cita Reagendada - {appointment_data.get('service_name', 'Servicio')}"

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Cita Reagendada</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 20px; }
        .header { background: #ff9800; color: white; padding: 20px; text-align: center; border-radius: 6px 6px 0 0; }
        .content { background: white; padding: 20px; }
        .appointment-details { background: #fff3e0; padding: 15px; border-radius: 6px; margin: 20px 0; }
        .change-highlight { background: #e8f5e8; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #4caf50; }
        .old-details { background: #ffebee; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #f44336; }
        .new-details { background: #e8f5e8; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #4caf50; }
        .detail-row { display: flex; justify-content: space-between; margin: 8px 0; }
        .detail-label { font-weight: bold; }
        .footer { background: #666; color: white; padding: 15px; text-align: center; border-radius: 0 0 6px 6px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 ¡Cita Reagendada!</h1>
            <p>Tu cita ha sido reagendada exitosamente</p>
        </div>

        <div class="content">
            <h2>Hola {{ user_name }},</h2>

            <p>Tu cita ha sido <strong>reagendada exitosamente</strong>. Aquí están los detalles actualizados:</p>

            <div class="change-highlight">
                <h3 style="margin-top: 0; color: #2e7d32;">📋 Resumen del Cambio</h3>

                <div class="old-details">
                    <h4 style="margin-top: 0; color: #c62828;">❌ Fecha Anterior:</h4>
                    <div class="detail-row">
                        <span class="detail-label">📅 Fecha:</span>
                        <span>{{ old_date }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">🕐 Hora:</span>
                        <span>{{ old_time }}</span>
                    </div>
                </div>

                <div class="new-details">
                    <h4 style="margin-top: 0; color: #2e7d32;">✅ Nueva Fecha:</h4>
                    <div class="detail-row">
                        <span class="detail-label">📅 Fecha:</span>
                        <span>{{ new_date }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">🕐 Hora:</span>
                        <span>{{ new_time }}</span>
                    </div>
                </div>
            </div>

            <div class="appointment-details">
                <h3 style="margin-top: 0; color: #ff9800;">📋 Detalles Completos de la Cita</h3>

                <div class="detail-row">
                    <span class="detail-label">🏥 Servicio:</span>
                    <span>{{ service_name }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">📅 Nueva Fecha:</span>
                    <span>{{ new_date }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">🕐 Nueva Hora:</span>
                    <span>{{ new_time }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">👨‍⚕️ Profesional:</span>
                    <span>{{ professional_name }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">⏱️ Duración:</span>
                    <span>{{ duration_minutes }} minutos</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">💰 Precio:</span>
                    <span>${{ "{:,}".format(price) }} COP</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">🆔 ID de Cita:</span>
                    <span>{{ appointment_id }}</span>
                </div>
            </div>

            <div style="background-color: #e0f2fe; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #0277bd;">📱 Recordatorios</h4>
                <p style="margin-bottom: 0;">Te enviaremos recordatorios por email antes de tu nueva fecha de cita.</p>
            </div>

            <div style="background-color: #fff3cd; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #856404;">ℹ️ Información Importante</h4>
                <ul style="margin-bottom: 0;">
                    <li>Tu cita ha sido reagendada para <strong>{{ new_date }} a las {{ new_time }}</strong></li>
                    <li>Llega 10 minutos antes de tu cita</li>
                    <li>Trae tu documento de identidad</li>
                    <li>Si necesitas reagendar nuevamente, hazlo con al menos 24 horas de anticipación</li>
                </ul>
            </div>
        </div>

        <div class="footer">
            <p>🏥 <strong>{{ company_name }}</strong></p>
            <p>Este email fue enviado automáticamente. No respondas a este mensaje.</p>
            <p style="font-size: 12px;">Generado el {{ current_datetime }}</p>
        </div>
    </div>
</body>
</html>
        """

        text_template = """
🔄 ¡CITA REAGENDADA!

Hola {{ user_name }},

Tu cita ha sido reagendada exitosamente. Aquí están los detalles actualizados:

📋 RESUMEN DEL CAMBIO:

❌ FECHA ANTERIOR:
📅 Fecha: {{ old_date }}
🕐 Hora: {{ old_time }}

✅ NUEVA FECHA:
📅 Fecha: {{ new_date }}
🕐 Hora: {{ new_time }}

📋 DETALLES COMPLETOS DE LA CITA:
🏥 Servicio: {{ service_name }}
📅 Nueva Fecha: {{ new_date }}
🕐 Nueva Hora: {{ new_time }}
👨‍⚕️ Profesional: {{ professional_name }}
⏱️ Duración: {{ duration_minutes }} minutos
💰 Precio: ${{ "{:,}".format(price) }} COP
🆔 ID de Cita: {{ appointment_id }}

📱 RECORDATORIOS:
Te enviaremos recordatorios por email antes de tu nueva fecha de cita.

ℹ️ INFORMACIÓN IMPORTANTE:
- Tu cita ha sido reagendada para {{ new_date }} a las {{ new_time }}
- Llega 10 minutos antes de tu cita
- Trae tu documento de identidad
- Si necesitas reagendar nuevamente, hazlo con al menos 24 horas de anticipación

¡Te esperamos en tu nueva fecha!

🏥 {{ company_name }}
Este email fue enviado automáticamente.
Generado el {{ current_datetime }}
        """

        # Prepare template data
        template_data = {
            "user_name": user_name,
            "service_name": appointment_data.get('service_name', 'N/A'),
            "old_date": appointment_data.get('old_date', 'N/A'),
            "old_time": appointment_data.get('old_time', 'N/A'),
            "new_date": appointment_data.get('new_date', appointment_data.get('date', 'N/A')),
            "new_time": appointment_data.get('new_time', appointment_data.get('time', 'N/A')),
            "professional_name": appointment_data.get('professional_name', 'Por asignar'),
            "duration_minutes": appointment_data.get('duration_minutes', 30),
            "price": appointment_data.get('price', 0),
            "appointment_id": appointment_data.get('id', 'N/A'),
            "company_name": self.company_config.company_name,
            "current_datetime": datetime.now().strftime("%d/%m/%Y a las %H:%M")
        }

        # Render templates
        html_body = Template(html_template).render(**template_data)
        text_body = Template(text_template).render(**template_data)

        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body
        }

    async def send_cancellation_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía email de confirmación de cancelación de cita

        Args:
            email_data: Datos del email con información de la cita cancelada

        Returns:
            Dict con resultado del envío
        """
        try:
            print(f"📧 [CANCELLATION_EMAIL] Preparing cancellation email for {email_data.get('user_email')}")

            # Generar template de cancelación
            email_template = self._generate_cancellation_email_template(
                email_data.get('user_name', 'Usuario'),
                email_data
            )

            # Enviar email
            result = await self._send_email(
                to_email=email_data.get('user_email'),
                subject=email_template['subject'],
                html_body=email_template['html_body'],
                text_body=email_template['text_body']
            )

            if result['success']:
                print(f"✅ [CANCELLATION_EMAIL] Email sent successfully to {email_data.get('user_email')}")
                return {
                    "success": True,
                    "message": "Email de cancelación enviado exitosamente",
                    "email_sent_to": email_data.get('user_email')
                }
            else:
                print(f"❌ [CANCELLATION_EMAIL] Failed to send email: {result.get('error')}")
                return {
                    "success": False,
                    "message": f"Error enviando email: {result.get('error')}",
                    "error": result.get('error')
                }

        except Exception as e:
            print(f"❌ [CANCELLATION_EMAIL] Error in send_cancellation_email: {e}")
            return {
                "success": False,
                "message": f"Error enviando email de cancelación: {str(e)}",
                "error": str(e)
            }

    def _generate_cancellation_email_template(
        self,
        user_name: str,
        appointment_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate appointment cancellation email template"""

        subject = f"🚫 Cita Cancelada - {appointment_data.get('service_name', 'Servicio')}"

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #dc2626; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }
        .content { background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
        .appointment-details { background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .detail-label { font-weight: bold; color: #dc2626; }
        .footer { text-align: center; margin-top: 30px; font-size: 14px; color: #666; }
        .cancellation-icon { font-size: 48px; text-align: center; margin: 20px 0; }
        .reason-box { background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚫 Cita Cancelada</h1>
            <p>Tu cita ha sido cancelada exitosamente</p>
        </div>

        <div class="content">
            <div class="cancellation-icon">❌</div>

            <p>Hola <strong>{{ user_name }}</strong>,</p>

            <p>Tu cita ha sido <strong>cancelada exitosamente</strong>. A continuación los detalles de la cita cancelada:</p>

            <div class="appointment-details">
                <h3 style="color: #dc2626; margin-top: 0;">📋 Detalles de la Cita Cancelada</h3>

                <div class="detail-row">
                    <span class="detail-label">🏥 Servicio:</span>
                    <span>{{ service_name }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">📅 Fecha:</span>
                    <span>{{ date }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">🕐 Hora:</span>
                    <span>{{ time }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">👨‍⚕️ Profesional:</span>
                    <span>{{ professional_name }}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">🚫 Estado:</span>
                    <span style="color: #dc2626; font-weight: bold;">CANCELADA</span>
                </div>
            </div>

            {% if cancellation_reason %}
            <div class="reason-box">
                <strong>📝 Razón de cancelación:</strong><br>
                {{ cancellation_reason }}
            </div>
            {% endif %}

            <div style="background-color: #e0f2fe; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #0277bd; margin-top: 0;">💡 ¿Necesitas programar una nueva cita?</h3>
                <p>Puedes agendar una nueva cita cuando desees a través de nuestro sistema de chat.</p>
                <p>Estaremos encantados de atenderte en una nueva oportunidad.</p>
            </div>

            <p>Gracias por informarnos sobre la cancelación.</p>
            <p><strong>{{ company_name }}</strong></p>
        </div>

        <div class="footer">
            <p>Este email fue enviado automáticamente.</p>
            <p>Generado el {{ current_datetime }}</p>
        </div>
    </div>
</body>
</html>
        """

        text_template = """
🚫 CITA CANCELADA

Hola {{ user_name }},

Tu cita ha sido CANCELADA exitosamente.

📋 DETALLES DE LA CITA CANCELADA:
🏥 Servicio: {{ service_name }}
📅 Fecha: {{ date }}
🕐 Hora: {{ time }}
👨‍⚕️ Profesional: {{ professional_name }}
🚫 Estado: CANCELADA

{% if cancellation_reason %}📝 Razón de cancelación: {{ cancellation_reason }}{% endif %}

💡 ¿NECESITAS PROGRAMAR UNA NUEVA CITA?
Puedes agendar una nueva cita cuando desees a través de nuestro sistema de chat.
Estaremos encantados de atenderte en una nueva oportunidad.

Gracias por informarnos sobre la cancelación.

🏥 {{ company_name }}
Este email fue enviado automáticamente.
Generado el {{ current_datetime }}
        """

        # Prepare template data
        template_data = {
            "user_name": user_name,
            "service_name": appointment_data.get('service_name', 'N/A'),
            "date": appointment_data.get('date', 'N/A'),
            "time": appointment_data.get('time', 'N/A'),
            "professional_name": appointment_data.get('professional_name', 'Por asignar'),
            "cancellation_reason": appointment_data.get('cancellation_reason', ''),
            "company_name": self.company_config.company_name,
            "current_datetime": datetime.now().strftime("%d/%m/%Y a las %H:%M")
        }

        # Render templates
        html_body = Template(html_template).render(**template_data)
        text_body = Template(text_template).render(**template_data)

        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body
        }