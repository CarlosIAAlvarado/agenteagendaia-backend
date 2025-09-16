from fastapi import APIRouter, Depends, Query
from typing import Optional
from ..controllers.user_controller import UserController
from ...application.dto.user_dto import UserCreateDTO, UserUpdateDTO, UserResponseDTO, UserListResponseDTO
from ..dependencies import get_user_controller

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponseDTO, status_code=201)
async def create_user(
    user_data: UserCreateDTO,
    controller: UserController = Depends(get_user_controller)
):
    """Create a new user"""
    return await controller.create_user(user_data)


@router.get("/", response_model=UserListResponseDTO)
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of users to return"),
    active_only: bool = Query(False, description="Return only active users"),
    controller: UserController = Depends(get_user_controller)
):
    """Get all users with pagination"""
    return await controller.get_all_users(skip, limit, active_only)


@router.get("/search", response_model=UserListResponseDTO)
async def search_users(
    name: str = Query(..., min_length=2, description="Name to search for"),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of users to return"),
    controller: UserController = Depends(get_user_controller)
):
    """Search users by name"""
    return await controller.search_users(name, skip, limit)


@router.get("/by-email/{email}", response_model=UserResponseDTO)
async def get_user_by_email(
    email: str,
    controller: UserController = Depends(get_user_controller)
):
    """Get user by email address"""
    return await controller.get_user_by_email(email)


@router.get("/by-phone/{phone}", response_model=UserResponseDTO)
async def get_user_by_phone(
    phone: str,
    controller: UserController = Depends(get_user_controller)
):
    """Get user by phone number"""
    return await controller.get_user_by_phone(phone)


@router.get("/{user_id}", response_model=UserResponseDTO)
async def get_user_by_id(
    user_id: str,
    controller: UserController = Depends(get_user_controller)
):
    """Get user by ID"""
    return await controller.get_user_by_id(user_id)


@router.put("/{user_id}", response_model=UserResponseDTO)
async def update_user(
    user_id: str,
    user_data: UserUpdateDTO,
    controller: UserController = Depends(get_user_controller)
):
    """Update user information"""
    return await controller.update_user(user_id, user_data)


@router.post("/{user_id}/activate", response_model=UserResponseDTO)
async def activate_user(
    user_id: str,
    controller: UserController = Depends(get_user_controller)
):
    """Activate user account"""
    return await controller.activate_user(user_id)


@router.post("/{user_id}/deactivate", response_model=UserResponseDTO)
async def deactivate_user(
    user_id: str,
    controller: UserController = Depends(get_user_controller)
):
    """Deactivate user account"""
    return await controller.deactivate_user(user_id)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    controller: UserController = Depends(get_user_controller)
):
    """Delete user permanently"""
    return await controller.delete_user(user_id)