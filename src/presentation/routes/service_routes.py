from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional
from ..controllers.service_controller import ServiceController
from ...application.use_cases.service_use_cases import ServiceUseCases
from ...infrastructure.dependencies import get_service_use_cases
from ...application.dto.service_dto import ServiceDTO, ServiceCreateDTO, ServiceUpdateDTO
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/services", tags=["Services"])


def get_service_controller(
    service_use_cases: ServiceUseCases = Depends(get_service_use_cases)
) -> ServiceController:
    """Dependency to get ServiceController instance"""
    return ServiceController(service_use_cases)


@router.get("/", response_model=List[ServiceDTO])
async def get_all_services(
    skip: int = Query(0, ge=0, description="Number of services to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of services to return"),
    controller: ServiceController = Depends(get_service_controller)
) -> List[ServiceDTO]:
    """Get all services with pagination"""
    try:
        return await controller.get_all_services(skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting all services: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving services")


@router.get("/active", response_model=List[ServiceDTO])
async def get_active_services(
    skip: int = Query(0, ge=0, description="Number of services to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of services to return"),
    controller: ServiceController = Depends(get_service_controller)
) -> List[ServiceDTO]:
    """Get all active services"""
    try:
        return await controller.get_active_services(skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting active services: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving active services")


@router.get("/{service_id}", response_model=ServiceDTO)
async def get_service_by_id(
    service_id: str,
    controller: ServiceController = Depends(get_service_controller)
) -> ServiceDTO:
    """Get service by ID"""
    try:
        service = await controller.get_service_by_id(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service {service_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving service")


@router.get("/search/{name}", response_model=List[ServiceDTO])
async def search_services_by_name(
    name: str,
    skip: int = Query(0, ge=0, description="Number of services to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of services to return"),
    controller: ServiceController = Depends(get_service_controller)
) -> List[ServiceDTO]:
    """Search services by name"""
    try:
        return await controller.search_services_by_name(name, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error searching services by name '{name}': {e}")
        raise HTTPException(status_code=500, detail="Error searching services")


@router.get("/type/{service_type}", response_model=List[ServiceDTO])
async def get_services_by_type(
    service_type: str,
    skip: int = Query(0, ge=0, description="Number of services to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of services to return"),
    controller: ServiceController = Depends(get_service_controller)
) -> List[ServiceDTO]:
    """Get services by type (medical, beauty, consultation, maintenance, other)"""
    try:
        return await controller.get_services_by_type(service_type, skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting services by type '{service_type}': {e}")
        raise HTTPException(status_code=500, detail="Error retrieving services by type")


@router.post("/", response_model=ServiceDTO)
async def create_service(
    service_data: ServiceCreateDTO,
    controller: ServiceController = Depends(get_service_controller)
) -> ServiceDTO:
    """Create a new service"""
    try:
        return await controller.create_service(service_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating service: {e}")
        raise HTTPException(status_code=500, detail="Error creating service")


@router.put("/{service_id}", response_model=ServiceDTO)
async def update_service(
    service_id: str,
    service_data: ServiceUpdateDTO,
    controller: ServiceController = Depends(get_service_controller)
) -> ServiceDTO:
    """Update existing service"""
    try:
        updated_service = await controller.update_service(service_id, service_data)
        if not updated_service:
            raise HTTPException(status_code=404, detail="Service not found")
        return updated_service
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating service {service_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating service")


@router.delete("/{service_id}")
async def delete_service(
    service_id: str,
    controller: ServiceController = Depends(get_service_controller)
) -> dict:
    """Delete service by ID"""
    try:
        success = await controller.delete_service(service_id)
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")
        return {"message": "Service deleted successfully", "service_id": service_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting service {service_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting service")


@router.patch("/{service_id}/activate")
async def activate_service(
    service_id: str,
    controller: ServiceController = Depends(get_service_controller)
) -> ServiceDTO:
    """Activate service"""
    try:
        service = await controller.activate_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating service {service_id}: {e}")
        raise HTTPException(status_code=500, detail="Error activating service")


@router.patch("/{service_id}/deactivate")
async def deactivate_service(
    service_id: str,
    controller: ServiceController = Depends(get_service_controller)
) -> ServiceDTO:
    """Deactivate service"""
    try:
        service = await controller.deactivate_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating service {service_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deactivating service")


@router.get("/stats/summary")
async def get_services_stats(
    controller: ServiceController = Depends(get_service_controller)
) -> dict:
    """Get services statistics summary"""
    try:
        return await controller.get_services_stats()
    except Exception as e:
        logger.error(f"Error getting services stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving services statistics")


@router.post("/bulk-upload")
async def bulk_upload_services(
    file: UploadFile = File(...),
    controller: ServiceController = Depends(get_service_controller)
) -> dict:
    """Upload services in bulk via CSV or JSON file"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file type
        if not (file.filename.endswith('.csv') or file.filename.endswith('.json')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file format. Only CSV and JSON files are supported."
            )
        
        # Read file content
        content = await file.read()
        
        # Process bulk upload
        result = await controller.bulk_upload_services(content, file.filename)
        
        return {
            "message": "Bulk upload completed successfully",
            "total_processed": result["total_processed"],
            "successful_uploads": result["successful_uploads"],
            "failed_uploads": result["failed_uploads"],
            "errors": result["errors"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk upload: {e}")
        raise HTTPException(status_code=500, detail="Error processing bulk upload")