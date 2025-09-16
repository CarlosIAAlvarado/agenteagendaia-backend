from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional
from ..controllers.professional_controller import ProfessionalController
from ...application.use_cases.professional_use_cases import ProfessionalUseCases
from ...infrastructure.dependencies import get_professional_use_cases
from ...application.dto.professional_dto import (
    ProfessionalResponseDTO, ProfessionalCreateDTO, ProfessionalUpdateDTO,
    ProfessionalListResponseDTO, ProfessionalFilterDTO, AddServiceToProfessionalDTO,
    RemoveServiceFromProfessionalDTO
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/professionals", tags=["Professionals"])


def get_professional_controller(
    professional_use_cases: ProfessionalUseCases = Depends(get_professional_use_cases)
) -> ProfessionalController:
    """Dependency to get ProfessionalController instance"""
    return ProfessionalController(professional_use_cases)


@router.get("/", response_model=ProfessionalListResponseDTO)
async def get_all_professionals(
    skip: int = Query(0, ge=0, description="Number of professionals to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of professionals to return"),
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalListResponseDTO:
    """Get all professionals with pagination"""
    try:
        return await controller.get_all_professionals(skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting all professionals: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving professionals")


@router.get("/active", response_model=ProfessionalListResponseDTO)
async def get_active_professionals(
    skip: int = Query(0, ge=0, description="Number of professionals to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of professionals to return"),
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalListResponseDTO:
    """Get all active professionals"""
    try:
        return await controller.get_active_professionals(skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting active professionals: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving active professionals")


@router.get("/{professional_id}", response_model=ProfessionalResponseDTO)
async def get_professional_by_id(
    professional_id: str,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalResponseDTO:
    """Get professional by ID"""
    try:
        professional = await controller.get_professional_by_id(professional_id)
        if not professional:
            raise HTTPException(status_code=404, detail="Professional not found")
        return professional
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting professional {professional_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving professional")


@router.get("/search/{search_term}", response_model=ProfessionalListResponseDTO)
async def search_professionals(
    search_term: str,
    skip: int = Query(0, ge=0, description="Number of professionals to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of professionals to return"),
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalListResponseDTO:
    """Search professionals by name or specialization"""
    try:
        return await controller.search_professionals(search_term, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error searching professionals with term '{search_term}': {e}")
        raise HTTPException(status_code=500, detail="Error searching professionals")


@router.get("/service/{service_id}", response_model=List[ProfessionalResponseDTO])
async def get_professionals_by_service(
    service_id: str,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> List[ProfessionalResponseDTO]:
    """Get professionals who provide a specific service"""
    try:
        return await controller.get_professionals_by_service(service_id)
    except Exception as e:
        logger.error(f"Error getting professionals by service '{service_id}': {e}")
        raise HTTPException(status_code=500, detail="Error retrieving professionals by service")


@router.get("/specialization/{specialization}", response_model=List[ProfessionalResponseDTO])
async def get_professionals_by_specialization(
    specialization: str,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> List[ProfessionalResponseDTO]:
    """Get professionals by specialization"""
    try:
        return await controller.get_professionals_by_specialization(specialization)
    except Exception as e:
        logger.error(f"Error getting professionals by specialization '{specialization}': {e}")
        raise HTTPException(status_code=500, detail="Error retrieving professionals by specialization")


@router.get("/available/{day}", response_model=List[ProfessionalResponseDTO])
async def get_available_professionals(
    day: str,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> List[ProfessionalResponseDTO]:
    """Get professionals available on a specific day (monday, tuesday, etc.)"""
    try:
        return await controller.get_available_professionals(day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting available professionals for day '{day}': {e}")
        raise HTTPException(status_code=500, detail="Error retrieving available professionals")


@router.post("/", response_model=ProfessionalResponseDTO)
async def create_professional(
    professional_data: ProfessionalCreateDTO,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalResponseDTO:
    """Create a new professional"""
    try:
        return await controller.create_professional(professional_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating professional: {e}")
        raise HTTPException(status_code=500, detail="Error creating professional")


@router.put("/{professional_id}", response_model=ProfessionalResponseDTO)
async def update_professional(
    professional_id: str,
    professional_data: ProfessionalUpdateDTO,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalResponseDTO:
    """Update existing professional"""
    try:
        updated_professional = await controller.update_professional(professional_id, professional_data)
        if not updated_professional:
            raise HTTPException(status_code=404, detail="Professional not found")
        return updated_professional
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating professional {professional_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating professional")


@router.delete("/{professional_id}")
async def delete_professional(
    professional_id: str,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> dict:
    """Delete professional by ID"""
    try:
        success = await controller.delete_professional(professional_id)
        if not success:
            raise HTTPException(status_code=404, detail="Professional not found")
        return {"message": "Professional deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting professional {professional_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting professional")


@router.patch("/{professional_id}/activate", response_model=ProfessionalResponseDTO)
async def activate_professional(
    professional_id: str,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalResponseDTO:
    """Activate professional"""
    try:
        professional = await controller.activate_professional(professional_id)
        if not professional:
            raise HTTPException(status_code=404, detail="Professional not found")
        return professional
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating professional {professional_id}: {e}")
        raise HTTPException(status_code=500, detail="Error activating professional")


@router.patch("/{professional_id}/deactivate", response_model=ProfessionalResponseDTO)
async def deactivate_professional(
    professional_id: str,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalResponseDTO:
    """Deactivate professional"""
    try:
        professional = await controller.deactivate_professional(professional_id)
        if not professional:
            raise HTTPException(status_code=404, detail="Professional not found")
        return professional
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating professional {professional_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deactivating professional")


@router.post("/{professional_id}/services", response_model=ProfessionalResponseDTO)
async def add_service_to_professional(
    professional_id: str,
    service_data: AddServiceToProfessionalDTO,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalResponseDTO:
    """Add service to professional"""
    try:
        professional = await controller.add_service_to_professional(professional_id, service_data.service_id)
        if not professional:
            raise HTTPException(status_code=404, detail="Professional not found")
        return professional
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding service to professional {professional_id}: {e}")
        raise HTTPException(status_code=500, detail="Error adding service to professional")


@router.delete("/{professional_id}/services/{service_id}", response_model=ProfessionalResponseDTO)
async def remove_service_from_professional(
    professional_id: str,
    service_id: str,
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalResponseDTO:
    """Remove service from professional"""
    try:
        professional = await controller.remove_service_from_professional(professional_id, service_id)
        if not professional:
            raise HTTPException(status_code=404, detail="Professional not found")
        return professional
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing service from professional {professional_id}: {e}")
        raise HTTPException(status_code=500, detail="Error removing service from professional")


@router.post("/filter", response_model=ProfessionalListResponseDTO)
async def filter_professionals(
    filters: ProfessionalFilterDTO = Body(...),
    skip: int = Query(0, ge=0, description="Number of professionals to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of professionals to return"),
    controller: ProfessionalController = Depends(get_professional_controller)
) -> ProfessionalListResponseDTO:
    """Filter professionals based on criteria"""
    try:
        return await controller.filter_professionals(filters, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error filtering professionals: {e}")
        raise HTTPException(status_code=500, detail="Error filtering professionals")