# -*- coding: utf-8 -*-
"""
Dashboard Routes - Endpoints para métricas del dashboard
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import logging
# from ..middleware.error_handler import handle_errors
from ...infrastructure.dependencies import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Obtiene las métricas reales para el dashboard
    """
    logger.info("📊 Obteniendo métricas del dashboard...")
    
    # Fechas para cálculos - Convertir a UTC para coincidir con DB
    now_utc = datetime.now(timezone.utc)  # UTC time para coincidir con DB
    today_start_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end_utc = now_utc.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # Métricas en paralelo
    try:
        # 1. Citas agendadas hoy (created_at = hoy)
        citas_hoy = await db.appointments.count_documents({
            "created_at": {
                "$gte": today_start_utc,
                "$lte": today_end_utc
            }
        })
        
        # 2. Usuarios activos
        usuarios_activos = await db.users.count_documents({"is_active": True})
        
        # 3. Citas pendientes (futuras y programadas)
        citas_pendientes = await db.appointments.count_documents({
            "status": {"$in": ["scheduled", "confirmed"]},
            "appointment_date": {"$gte": now_utc}
        })
        
        # 4. Citas pasadas para tasa de completación
        citas_pasadas = await db.appointments.count_documents({
            "appointment_date": {"$lt": now_utc}
        })

        citas_completadas = await db.appointments.count_documents({
            "status": "completed",
            "appointment_date": {"$lt": now_utc}
        })
        
        # Calcular tasa de completación
        tasa_completada = 0
        if citas_pasadas > 0:
            tasa_completada = (citas_completadas / citas_pasadas) * 100
        
        # 5. Cambios respecto al día anterior
        yesterday_start_utc = (now_utc - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end_utc = (now_utc - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)

        citas_ayer = await db.appointments.count_documents({
            "created_at": {
                "$gte": yesterday_start_utc,
                "$lte": yesterday_end_utc
            }
        })
        
        # Calcular cambios
        cambio_citas_hoy = citas_hoy - citas_ayer
        
        # Usuarios nuevos en los últimos 7 días
        semana_pasada = now_utc - timedelta(days=7)
        usuarios_nuevos = await db.users.count_documents({
            "created_at": {"$gte": semana_pasada}
        })
        
        # 6. Total de citas en el sistema
        total_citas = await db.appointments.count_documents({})
        
        # 7. Próximas 5 citas
        proximas_citas_cursor = db.appointments.find({
            "appointment_date": {"$gte": now_utc},
            "status": {"$in": ["scheduled", "confirmed"]}
        }).sort("appointment_date", 1).limit(5)
        
        proximas_citas = []
        async for appointment in proximas_citas_cursor:
            # Obtener información del usuario
            user = await db.users.find_one({"_id": appointment["user_id"]})
            user_name = user["name"] if user else "Usuario desconocido"
            
            proximas_citas.append({
                "id": str(appointment["_id"]),
                "user_name": user_name,
                "service_name": appointment.get("service_name", "Servicio"),
                "appointment_date": appointment["appointment_date"].isoformat(),
                "status": appointment["status"],
                "professional_name": appointment.get("professional_name", "Por asignar")
            })
        
        # 8. Usuarios recientes (últimos 5)
        usuarios_recientes_cursor = db.users.find({
            "is_active": True
        }).sort("created_at", -1).limit(5)
        
        usuarios_recientes = []
        async for user in usuarios_recientes_cursor:
            # Contar citas del usuario
            citas_usuario = await db.appointments.count_documents({"user_id": str(user["_id"])})
            
            usuarios_recientes.append({
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"],
                "phone": user.get("phone", ""),
                "created_at": user["created_at"].isoformat(),
                "total_appointments": citas_usuario,
                "is_active": user["is_active"]
            })
        
        # Estructura de respuesta
        metrics = {
            "stats": {
                "citas_hoy": {
                    "value": citas_hoy,
                    "change": cambio_citas_hoy,
                    "change_type": "increase" if cambio_citas_hoy >= 0 else "decrease"
                },
                "usuarios_activos": {
                    "value": usuarios_activos,
                    "change": usuarios_nuevos,
                    "change_type": "increase" if usuarios_nuevos > 0 else "neutral"
                },
                "citas_pendientes": {
                    "value": citas_pendientes,
                    "change": 0,  # Calculado en tiempo real
                    "change_type": "neutral"
                },
                "tasa_completada": {
                    "value": f"{tasa_completada:.1f}%",
                    "change": 0,  # Se podría calcular vs período anterior
                    "change_type": "neutral"
                }
            },
            "proximas_citas": proximas_citas,
            "usuarios_recientes": usuarios_recientes,
            "summary": {
                "total_appointments": total_citas,
                "total_users": usuarios_activos,
                "appointments_today": citas_hoy,
                "completion_rate": round(tasa_completada, 1)
            }
        }
        
        logger.info(f"✅ Métricas del dashboard obtenidas: {citas_hoy} citas hoy, {usuarios_activos} usuarios activos")
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas del dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")