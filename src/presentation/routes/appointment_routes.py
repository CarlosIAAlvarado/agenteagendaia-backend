from fastapi import APIRouter, Depends, Query, Path
from typing import Optional
from datetime import date
from ..controllers.appointment_controller import AppointmentController
from ...application.dto.appointment_dto import (
    AppointmentCreateDTO, AppointmentRescheduleDTO, AppointmentCancelDTO,
    AppointmentResponseDTO, AppointmentListResponseDTO, AvailabilityRequestDTO,
    AvailabilityResponseDTO
)
from ..dependencies import get_appointment_controller

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("/calendar-view-direct", response_model=dict)
async def get_calendar_appointments_direct(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)")
):
    """Get appointments for calendar view by month and year - DIRECT MongoDB query"""
    from datetime import date as date_class, timedelta, datetime
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"[DEBUG] DIRECT MongoDB query for calendar appointments for {year}-{month:02d}")
    
    try:
        # Calculate first and last day of the month
        first_day = date_class(year, month, 1)
        if month == 12:
            next_month = date_class(year + 1, 1, 1)
        else:
            next_month = date_class(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        
        logger.info(f"[CALENDAR] Date range: {first_day} to {last_day}")
        
        # Direct MongoDB query using async connection
        from ...infrastructure.database.connection import get_database
        db = await get_database()
        appointments_collection = db.appointments
        
        # Query appointments in date range
        query = {
            "$and": [
                {"appointment_date": {"$gte": datetime(first_day.year, first_day.month, first_day.day)}},
                {"appointment_date": {"$lte": datetime(last_day.year, last_day.month, last_day.day, 23, 59, 59)}}
            ]
        }
        
        cursor = appointments_collection.find(query)
        raw_appointments = await cursor.to_list(length=500)
        
        logger.info(f"[DATA] Direct MongoDB query found {len(raw_appointments)} appointments")
        
        # Transform appointments for calendar format
        calendar_appointments = []
        current_datetime = datetime.now()
        
        for raw_apt in raw_appointments:
            appointment_datetime = raw_apt.get('appointment_date')
            if appointment_datetime:
                appointment_date_str = appointment_datetime.strftime("%Y-%m-%d")
                appointment_time_str = appointment_datetime.strftime("%H:%M")
                
                # Check if appointment is in the past
                is_past = appointment_datetime < current_datetime
                
                # Map status values
                status_mapping = {
                    "draft": "pending",
                    "scheduled": "confirmed", 
                    "confirmed": "confirmed",
                    "cancelled": "cancelled",
                    "completed": "completed",
                    "no_show": "cancelled",
                    "rescheduled": "pending"
                }
                
                status = raw_apt.get('status', 'draft')
                mapped_status = status_mapping.get(status, status)
                
                # If it's a past appointment and was scheduled/confirmed, mark as completed
                if is_past and mapped_status == "confirmed":
                    mapped_status = "completed"
                
                calendar_appointments.append({
                    "id": str(raw_apt.get('_id')),
                    "appointment_id": raw_apt.get('appointment_id', str(raw_apt.get('_id'))),
                    "date": appointment_date_str,
                    "time": appointment_time_str,
                    "service": raw_apt.get('service_name', 'Servicio no especificado'),
                    "patient": f"Usuario {raw_apt.get('user_id', 'desconocido')[:8]}...",
                    "status": mapped_status,
                    "is_past": is_past,
                    "professional": raw_apt.get('professional_name'),
                    "duration_minutes": raw_apt.get('duration_minutes'),
                    "price": raw_apt.get('price'),
                    "notes": raw_apt.get('notes')
                })
        
        logger.info(f"[CALENDAR] Returning {len(calendar_appointments)} appointments for calendar view")
        
        return {
            "appointments": calendar_appointments,
            "total": len(calendar_appointments),
            "month": month,
            "year": year,
            "date_range": {
                "start": first_day.isoformat(),
                "end": last_day.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Error getting calendar appointments: {e}")
        return {
            "appointments": [],
            "total": 0,
            "month": month,
            "year": year,
            "error": f"Error loading appointments: {str(e)}"
        }


@router.get("/calendar-view", response_model=dict)
async def get_calendar_appointments(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Get appointments for calendar view by month and year"""
    from datetime import date as date_class, timedelta, datetime
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"[CALENDAR] Getting calendar appointments for {year}-{month:02d}")
    
    try:
        # Calculate first and last day of the month
        first_day = date_class(year, month, 1)
        if month == 12:
            next_month = date_class(year + 1, 1, 1)
        else:
            next_month = date_class(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        
        logger.info(f"[CALENDAR] Date range: {first_day} to {last_day}")
        
        # Get all appointments in the date range without future-only filtering
        # This handles both appointment_date and time_slot formats
        # Use direct MongoDB query for reliability (service layer has complex issues)
        try:
            # Direct MongoDB query using the correct async connection
            from ...infrastructure.database.connection import get_database
            db = await get_database()
            appointments_collection = db.appointments
            
            # Query appointments in date range
            query = {
                "$and": [
                    {"appointment_date": {"$gte": datetime(first_day.year, first_day.month, first_day.day)}},
                    {"appointment_date": {"$lte": datetime(last_day.year, last_day.month, last_day.day, 23, 59, 59)}}
                ]
            }
            
            logger.info(f"[SEARCH] Query: {query}")
            cursor = appointments_collection.find(query)
            raw_appointments = await cursor.to_list(length=500)
            
            logger.info(f"[DATA] Direct MongoDB query found {len(raw_appointments)} appointments")
            
            # Also try to get total count in database
            total_count = await appointments_collection.count_documents({})
            logger.info(f"[DATA] Total appointments in database: {total_count}")
        
        except Exception as e:
            logger.error(f"[ERROR] Error in direct query: {e}")
            raw_appointments = []
        
        # Transform appointments for calendar format
        calendar_appointments = []
        from datetime import datetime
        current_datetime = datetime.now()
        
        for raw_apt in raw_appointments:
            appointment_datetime = raw_apt.get('appointment_date')
            if appointment_datetime:
                appointment_date_str = appointment_datetime.strftime("%Y-%m-%d")
                appointment_time_str = appointment_datetime.strftime("%H:%M")
                
                # Check if appointment is in the past
                is_past = appointment_datetime < current_datetime
                
                # Map status values
                status_mapping = {
                    "draft": "pending",
                    "scheduled": "confirmed", 
                    "confirmed": "confirmed",
                    "cancelled": "cancelled",
                    "completed": "completed",
                    "no_show": "cancelled",
                    "rescheduled": "pending"
                }
                
                status = raw_apt.get('status', 'draft')
                mapped_status = status_mapping.get(status, status)
                
                # If it's a past appointment and was scheduled/confirmed, mark as completed
                if is_past and mapped_status == "confirmed":
                    mapped_status = "completed"
                
                calendar_appointments.append({
                    "id": str(raw_apt.get('_id')),
                    "appointment_id": raw_apt.get('appointment_id', str(raw_apt.get('_id'))),
                    "date": appointment_date_str,
                    "time": appointment_time_str,
                    "service": raw_apt.get('service_name', 'Servicio no especificado'),
                    "patient": f"Usuario {raw_apt.get('user_id', 'desconocido')[:8]}...",
                    "status": mapped_status,
                    "is_past": is_past,
                    "professional": raw_apt.get('professional_name'),
                    "duration_minutes": raw_apt.get('duration_minutes'),
                    "price": raw_apt.get('price'),
                    "notes": raw_apt.get('notes')
                })
        
        logger.info(f"[CALENDAR] Found {len(calendar_appointments)} appointments for calendar view")
        
        return {
            "appointments": calendar_appointments,
            "total": len(calendar_appointments),
            "month": month,
            "year": year,
            "date_range": {
                "start": first_day.isoformat(),
                "end": last_day.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Error getting calendar appointments: {e}")
        # Return empty calendar on error to avoid breaking the UI
        return {
            "appointments": [],
            "total": 0,
            "month": month,
            "year": year,
            "error": f"Error loading appointments: {str(e)}"
        }


@router.post("/", response_model=AppointmentResponseDTO, status_code=201)
async def create_appointment(
    appointment_data: AppointmentCreateDTO,
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Create a new appointment"""
    return await controller.create_appointment(appointment_data)


@router.get("/", response_model=AppointmentListResponseDTO)
async def get_appointments(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    professional_id: Optional[str] = Query(None, description="Filter by professional ID"),
    service_id: Optional[str] = Query(None, description="Filter by service ID"),
    status: Optional[str] = Query(None, description="Filter by appointment status"),
    mode: Optional[str] = Query(None, description="Filter by appointment mode"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    upcoming_only: bool = Query(False, description="Show only upcoming appointments"),
    skip: int = Query(0, ge=0, description="Number of appointments to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of appointments to return"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Get appointments with filters"""
    return await controller.get_appointments(
        user_id=user_id,
        professional_id=professional_id,
        service_id=service_id,
        status_filter=status,
        mode=mode,
        date_from=str(date_from) if date_from else None,
        date_to=str(date_to) if date_to else None,
        upcoming_only=upcoming_only,
        skip=skip,
        limit=limit
    )


@router.post("/availability", response_model=AvailabilityResponseDTO)
async def get_available_slots(
    request: AvailabilityRequestDTO,
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Get available time slots for a service"""
    return await controller.get_available_slots(request)


@router.get("/users/{user_id}", response_model=AppointmentListResponseDTO)
async def get_user_appointments(
    user_id: str = Path(..., description="User ID"),
    upcoming_only: bool = Query(True, description="Show only upcoming appointments"),
    skip: int = Query(0, ge=0, description="Number of appointments to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of appointments to return"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Get appointments for a specific user"""
    return await controller.get_user_appointments(user_id, upcoming_only, skip, limit)


@router.get("/professionals/{professional_id}", response_model=AppointmentListResponseDTO)
async def get_professional_appointments(
    professional_id: str = Path(..., description="Professional ID"),
    upcoming_only: bool = Query(True, description="Show only upcoming appointments"),
    skip: int = Query(0, ge=0, description="Number of appointments to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of appointments to return"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Get appointments for a specific professional"""
    return await controller.get_professional_appointments(professional_id, upcoming_only, skip, limit)


@router.get("/{appointment_id}", response_model=AppointmentResponseDTO)
async def get_appointment_by_id(
    appointment_id: str = Path(..., description="Appointment ID"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Get appointment by ID"""
    return await controller.get_appointment_by_id(appointment_id)


@router.post("/{appointment_id}/confirm", response_model=AppointmentResponseDTO)
async def confirm_appointment(
    appointment_id: str = Path(..., description="Appointment ID"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Confirm an appointment"""
    return await controller.confirm_appointment(appointment_id)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponseDTO)
async def cancel_appointment(
    cancel_data: AppointmentCancelDTO = None,
    appointment_id: str = Path(..., description="Appointment ID"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Cancel an appointment"""
    if cancel_data is None:
        cancel_data = AppointmentCancelDTO()
    return await controller.cancel_appointment(appointment_id, cancel_data)


@router.put("/{appointment_id}/reschedule", response_model=AppointmentResponseDTO)
async def reschedule_appointment(
    reschedule_data: AppointmentRescheduleDTO,
    appointment_id: str = Path(..., description="Appointment ID"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Reschedule an appointment"""
    return await controller.reschedule_appointment(appointment_id, reschedule_data)


@router.post("/{appointment_id}/complete", response_model=AppointmentResponseDTO)
async def complete_appointment(
    appointment_id: str = Path(..., description="Appointment ID"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Mark appointment as completed"""
    return await controller.complete_appointment(appointment_id)


@router.post("/{appointment_id}/no-show", response_model=AppointmentResponseDTO)
async def mark_no_show(
    appointment_id: str = Path(..., description="Appointment ID"),
    controller: AppointmentController = Depends(get_appointment_controller)
):
    """Mark appointment as no show"""
    return await controller.mark_no_show(appointment_id)