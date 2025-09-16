from fastapi import HTTPException, status
from typing import Optional
from ...application.use_cases.user_use_cases import UserUseCases
from ...application.dto.user_dto import UserCreateDTO, UserUpdateDTO, UserResponseDTO, UserListResponseDTO
import logging

logger = logging.getLogger(__name__)


class UserController:
    """Controller for User-related endpoints"""
    
    def __init__(self, user_use_cases: UserUseCases):
        self.user_use_cases = user_use_cases
    
    async def create_user(self, user_data: UserCreateDTO) -> UserResponseDTO:
        """Create a new user"""
        try:
            return await self.user_use_cases.create_user(user_data)
        except ValueError as e:
            logger.warning(f"User creation validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_user_by_id(self, user_id: str) -> UserResponseDTO:
        """Get user by ID"""
        try:
            user = await self.user_use_cases.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_user_by_email(self, email: str) -> UserResponseDTO:
        """Get user by email"""
        try:
            user = await self.user_use_cases.get_user_by_email(email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with email {email} not found"
                )
            return user
        except HTTPException:
            raise
        except ValueError as e:
            logger.warning(f"Invalid email format: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error getting user by email {email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_user_by_phone(self, phone: str) -> UserResponseDTO:
        """Get user by phone"""
        try:
            user = await self.user_use_cases.get_user_by_phone(phone)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with phone {phone} not found"
                )
            return user
        except HTTPException:
            raise
        except ValueError as e:
            logger.warning(f"Invalid phone format: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error getting user by phone {phone}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_all_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        active_only: bool = False
    ) -> UserListResponseDTO:
        """Get all users with pagination"""
        try:
            if skip < 0 or limit <= 0 or limit > 500:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination parameters"
                )
            
            return await self.user_use_cases.get_all_users(skip, limit, active_only)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting all users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def update_user(self, user_id: str, user_data: UserUpdateDTO) -> UserResponseDTO:
        """Update user information"""
        try:
            return await self.user_use_cases.update_user(user_id, user_data)
        except ValueError as e:
            logger.warning(f"User update validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error updating user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def activate_user(self, user_id: str) -> UserResponseDTO:
        """Activate user account"""
        try:
            return await self.user_use_cases.activate_user(user_id)
        except ValueError as e:
            logger.warning(f"User activation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error activating user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def deactivate_user(self, user_id: str) -> UserResponseDTO:
        """Deactivate user account"""
        try:
            return await self.user_use_cases.deactivate_user(user_id)
        except ValueError as e:
            logger.warning(f"User deactivation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error deactivating user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def delete_user(self, user_id: str) -> dict:
        """Delete user permanently"""
        try:
            success = await self.user_use_cases.delete_user(user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            
            return {"message": f"User {user_id} deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def search_users(
        self, 
        name: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> UserListResponseDTO:
        """Search users by name"""
        try:
            if not name or len(name.strip()) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Search name must be at least 2 characters long"
                )
            
            if skip < 0 or limit <= 0 or limit > 500:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination parameters"
                )
            
            return await self.user_use_cases.search_users(name.strip(), skip, limit)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error searching users by name '{name}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )