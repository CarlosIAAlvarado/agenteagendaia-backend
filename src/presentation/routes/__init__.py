from fastapi import APIRouter
from .user_routes import router as user_router
from .service_routes import router as service_router
from .professional_routes import router as professional_router
from .appointment_routes import router as appointment_router
from .health_routes import router as health_router
from .chat_routes import router as chat_router
from .admin_routes import router as admin_router
from .metrics_routes import router as metrics_router
from .survey_routes import router as survey_router
from .express_registration_routes import router as express_registration_router
from .link_management_routes import router as link_management_router
from .dashboard_routes import router as dashboard_router
from .email_config_routes import router as email_config_router
from .company_config_routes import router as company_config_router

# Main router that includes all sub-routers - PROFESSIONALS ADDED
router = APIRouter()

router.include_router(health_router)
router.include_router(user_router)
router.include_router(service_router)
router.include_router(professional_router)
# Temporarily disabled due to emoji Unicode issues
# router.include_router(appointment_router)
router.include_router(chat_router)
router.include_router(admin_router)
router.include_router(metrics_router)
router.include_router(survey_router)
router.include_router(express_registration_router)
router.include_router(link_management_router)
router.include_router(dashboard_router)
router.include_router(email_config_router)
router.include_router(company_config_router)