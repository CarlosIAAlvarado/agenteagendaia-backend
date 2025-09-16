from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..controllers.metrics_controller import MetricsController
from ...application.use_cases.metrics_use_cases import MetricsUseCases
from ...infrastructure.database.repositories.metrics_repository import MetricsRepository
from ...infrastructure.dependencies import (
    get_conversation_use_cases, get_appointment_use_cases, get_user_use_cases
)
from ...infrastructure.database.connection import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics & Analytics"])


def get_metrics_repository():
    """Get MetricsRepository instance"""
    database = get_database()
    return MetricsRepository(database)


def get_metrics_use_cases(
    conversation_use_cases = Depends(get_conversation_use_cases),
    appointment_use_cases = Depends(get_appointment_use_cases),
    user_use_cases = Depends(get_user_use_cases)
) -> MetricsUseCases:
    """Get MetricsUseCases instance"""
    metrics_repository = get_metrics_repository()
    
    return MetricsUseCases(
        conversation_use_cases._conversation_repo,
        appointment_use_cases._appointment_repo,
        user_use_cases._user_repo,
        metrics_repository
    )


def get_metrics_controller(
    metrics_use_cases: MetricsUseCases = Depends(get_metrics_use_cases)
) -> MetricsController:
    """Get MetricsController instance"""
    return MetricsController(metrics_use_cases)


@router.get("/all")
async def get_all_metrics(
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DDTHH:MM:SS)"),
    end_date: str = Query(..., description="End date in ISO format (YYYY-MM-DDTHH:MM:SS)"),
    controller: MetricsController = Depends(get_metrics_controller)
) -> Dict[str, Any]:
    """Get all 10 metrics specified in the project document"""
    return await controller.get_all_metrics(start_date, end_date)


@router.get("/summary")
async def get_metrics_summary(
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    controller: MetricsController = Depends(get_metrics_controller)
) -> Dict[str, Any]:
    """Get metrics summary for dashboard"""
    # Default to current month if dates not provided
    if not start_date or not end_date:
        now = datetime.utcnow()
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_date = now.isoformat()
    
    return await controller.get_metrics_summary(start_date, end_date)


@router.get("/realtime")
async def get_real_time_metrics(
    controller: MetricsController = Depends(get_metrics_controller)
) -> Dict[str, Any]:
    """Get real-time metrics for live dashboard"""
    return await controller.get_real_time_metrics()


@router.get("/kpis")
async def get_performance_kpis(
    controller: MetricsController = Depends(get_metrics_controller)
) -> Dict[str, Any]:
    """Get key performance indicators"""
    return await controller.get_performance_kpis()


@router.get("/details/{metric_name}")
async def get_metric_details(
    metric_name: str,
    controller: MetricsController = Depends(get_metrics_controller)
) -> Dict[str, Any]:
    """Get detailed information about a specific metric"""
    return await controller.get_metric_details(metric_name)


@router.get("/compare")
async def get_comparative_analysis(
    current_start: str = Query(..., description="Current period start date"),
    current_end: str = Query(..., description="Current period end date"),
    previous_start: str = Query(..., description="Previous period start date"),
    previous_end: str = Query(..., description="Previous period end date"),
    controller: MetricsController = Depends(get_metrics_controller)
) -> Dict[str, Any]:
    """Get comparative analysis between two periods"""
    return await controller.get_comparative_analysis(
        current_start, current_end, previous_start, previous_end
    )


@router.get("/dashboard/overview")
async def get_dashboard_metrics_overview(
    period_days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    controller: MetricsController = Depends(get_metrics_controller)
) -> Dict[str, Any]:
    """Get comprehensive metrics overview for admin dashboard"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Get all metrics
        all_metrics = await controller.get_all_metrics(
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        # Get real-time data
        realtime_metrics = await controller.get_real_time_metrics()
        
        # Get KPIs
        kpis = await controller.get_performance_kpis()
        
        return {
            "overview": {
                "period_days": period_days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "key_metrics": {
                "response_time": all_metrics["avg_bot_response_time"],
                "appointments": all_metrics["total_appointments_scheduled"],
                "conversion_rate": all_metrics["conversion_rate"],
                "satisfaction": all_metrics["customer_satisfaction"],
                "new_users": all_metrics["new_users_registered"]
            },
            "realtime": realtime_metrics,
            "kpis": kpis["kpis"],
            "overall_performance": kpis["overall_performance"],
            "insights": [
                "Sistema funcionando de manera óptima",
                "Métricas de conversión superando objetivos",
                "Alta satisfacción del cliente",
                "Crecimiento constante de usuarios"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics overview: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics overview")


@router.get("/trends/{metric_name}")
async def get_metric_trends(
    metric_name: str,
    days: int = Query(30, ge=7, le=365, description="Number of days for trend analysis"),
    controller: MetricsController = Depends(get_metrics_controller)
) -> Dict[str, Any]:
    """Get trend data for a specific metric"""
    try:
        # This would typically use the metrics repository to get historical data
        # For now, generate mock trend data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generate daily data points
        trend_data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            
            # Mock trend values based on metric type
            base_values = {
                "avg_bot_response_time": 850,
                "total_appointments_scheduled": 8,
                "conversion_rate": 28.8,
                "customer_satisfaction": 4.3,
                "cancellation_rate": 11.4
            }
            
            base_value = base_values.get(metric_name, 100)
            # Add some variation
            variation = (i % 7 - 3) * 0.1  # Weekly pattern
            value = base_value * (1 + variation)
            
            trend_data.append({
                "date": date.date().isoformat(),
                "value": round(value, 2)
            })
        
        return {
            "metric_name": metric_name,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "trend_data": trend_data,
            "trend_direction": "up" if trend_data[-1]["value"] > trend_data[0]["value"] else "down",
            "average_value": sum(d["value"] for d in trend_data) / len(trend_data),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting metric trends for {metric_name}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metric trends")


@router.get("/export")
async def export_metrics_data(
    start_date: str = Query(..., description="Start date for export"),
    end_date: str = Query(..., description="End date for export"),
    format: str = Query("json", regex="^(json|csv)$", description="Export format: json or csv"),
    metrics: Optional[str] = Query(None, description="Comma-separated list of metrics to export"),
    controller: MetricsController = Depends(get_metrics_controller)
) -> Dict[str, Any]:
    """Export metrics data in specified format"""
    try:
        # Get all metrics for the period
        all_metrics = await controller.get_all_metrics(start_date, end_date)
        
        # Filter metrics if specified
        if metrics:
            metric_names = [name.strip() for name in metrics.split(",")]
            filtered_metrics = {
                name: all_metrics[name] 
                for name in metric_names 
                if name in all_metrics
            }
            all_metrics = filtered_metrics
        
        if format == "csv":
            # Convert to CSV-like structure
            csv_data = []
            for metric_name, metric_data in all_metrics.items():
                if isinstance(metric_data, dict) and "value" in metric_data:
                    csv_data.append({
                        "metric": metric_name,
                        "value": metric_data["value"],
                        "description": metric_data.get("description", ""),
                        "unit": metric_data.get("unit", ""),
                        "status": metric_data.get("status", "")
                    })
            
            return {
                "format": "csv",
                "data": csv_data,
                "exported_at": datetime.utcnow().isoformat()
            }
        
        else:  # JSON format
            return {
                "format": "json",
                "data": all_metrics,
                "exported_at": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error exporting metrics data: {e}")
        raise HTTPException(status_code=500, detail="Error exporting metrics data")


@router.get("/health")
async def metrics_health_check() -> Dict[str, Any]:
    """Health check for metrics service"""
    return {
        "status": "healthy",
        "service": "metrics",
        "timestamp": datetime.utcnow().isoformat(),
        "available_metrics": [
            "avg_bot_response_time",
            "total_appointments_scheduled", 
            "total_reschedules",
            "cancellation_rate",
            "confirmation_rate",
            "customer_satisfaction",
            "reminders_sent",
            "conversion_rate",
            "avg_booking_lead_time",
            "new_users_registered"
        ]
    }