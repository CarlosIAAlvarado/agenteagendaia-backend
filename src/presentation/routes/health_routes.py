from fastapi import APIRouter, Depends
from ...infrastructure.config.database import ping_database
from ...infrastructure.dependencies import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Agenda IA API"
    }


@router.get("/database")
async def database_health_check():
    """Database health check endpoint"""
    try:
        is_healthy = await ping_database()
        
        if is_healthy:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected"
            }
        else:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "disconnected"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "error",
            "error": str(e)
        }


@router.get("/detailed")
async def detailed_health_check(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Detailed health check with all components"""
    try:
        # Test database connection directly with the same db instance used by the app
        await db.command("ping")
        db_healthy = True
        
        # Test that we can access collections
        users_count = await db.users.count_documents({})
        appointments_count = await db.appointments.count_documents({})
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Agenda IA API",
            "version": "1.0.0",
            "components": {
                "api": "healthy",
                "database": "healthy",
                "users_collection": f"accessible ({users_count} records)",
                "appointments_collection": f"accessible ({appointments_count} records)"
            },
            "uptime": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Agenda IA API",
            "version": "1.0.0",
            "components": {
                "api": "healthy",
                "database": "error"
            },
            "error": str(e)
        }