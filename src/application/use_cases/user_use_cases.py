from typing import List, Optional
from datetime import datetime
from ...domain.entities.patient import Patient
from ...domain.value_objects.email import Email
from ...domain.value_objects.phone import Phone
from ...domain.repositories.user_repository import IUserRepository
from ..dto.user_dto import UserCreateDTO, UserUpdateDTO, UserResponseDTO, UserListResponseDTO
import logging

logger = logging.getLogger(__name__)


class UserUseCases:
    """Use cases for User entity operations"""
    
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository
    
    async def create_user(self, user_data: UserCreateDTO) -> UserResponseDTO:
        """Create a new user"""
        try:
            # Check if user already exists
            email = Email(user_data.email)
            phone = Phone(user_data.phone)
            
            if await self._user_repository.exists_by_email(email):
                raise ValueError(f"User with email {user_data.email} already exists")
            
            if await self._user_repository.exists_by_phone(phone):
                raise ValueError(f"User with phone {user_data.phone} already exists")
            
            # Create user entity
            user = Patient(
                id=None,
                name=user_data.name,
                email=email,
                phone=phone,
                created_at=datetime.utcnow()
            )
            
            # Save to repository
            created_user = await self._user_repository.create(user)
            
            logger.info(f"Created user: {created_user.id}")
            
            # Return DTO
            return UserResponseDTO(
                id=created_user.id,
                name=created_user.name,
                email=created_user.email.value,
                phone=created_user.phone.value,
                is_active=created_user.is_active,
                created_at=created_user.created_at,
                updated_at=created_user.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponseDTO]:
        """Get user by ID"""
        try:
            user = await self._user_repository.get_by_id(user_id)
            
            if not user:
                return None
            
            return UserResponseDTO(
                id=user.id,
                name=user.name,
                email=user.email.value,
                phone=user.phone.value,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponseDTO]:
        """Get user by email"""
        try:
            email_obj = Email(email)
            user = await self._user_repository.get_by_email(email_obj)
            
            if not user:
                return None
            
            return UserResponseDTO(
                id=user.id,
                name=user.name,
                email=user.email.value,
                phone=user.phone.value,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    async def get_user_by_phone(self, phone: str) -> Optional[UserResponseDTO]:
        """Get user by phone"""
        try:
            phone_obj = Phone(phone)
            user = await self._user_repository.get_by_phone(phone_obj)
            
            if not user:
                return None
            
            return UserResponseDTO(
                id=user.id,
                name=user.name,
                email=user.email.value,
                phone=user.phone.value,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error getting user by phone {phone}: {e}")
            raise
    
    async def get_all_users(self, skip: int = 0, limit: int = 100, active_only: bool = False) -> UserListResponseDTO:
        """Get all users with pagination"""
        try:
            if active_only:
                users = await self._user_repository.get_active_users(skip, limit)
                total = await self._user_repository.count_active()
            else:
                users = await self._user_repository.get_all(skip, limit)
                total = await self._user_repository.count_total()
            
            user_dtos = [
                UserResponseDTO(
                    id=user.id,
                    name=user.name,
                    email=user.email.value,
                    phone=user.phone.value,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
                for user in users
            ]
            
            return UserListResponseDTO(
                users=user_dtos,
                total=total,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            raise
    
    async def update_user(self, user_id: str, user_data: UserUpdateDTO) -> UserResponseDTO:
        """Update user information"""
        try:
            # Get existing user
            user = await self._user_repository.get_by_id(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            # Check for conflicts if email or phone are being updated
            if user_data.email:
                new_email = Email(user_data.email)
                if new_email.value != user.email.value:
                    if await self._user_repository.exists_by_email(new_email):
                        raise ValueError(f"User with email {user_data.email} already exists")
            
            if user_data.phone:
                new_phone = Phone(user_data.phone)
                if new_phone.value != user.phone.value:
                    if await self._user_repository.exists_by_phone(new_phone):
                        raise ValueError(f"User with phone {user_data.phone} already exists")
            
            # Update user fields
            if user_data.name:
                user.name = user_data.name
            if user_data.email:
                user.email = Email(user_data.email)
            if user_data.phone:
                user.phone = Phone(user_data.phone)
            
            user.updated_at = datetime.utcnow()
            
            # Save changes
            updated_user = await self._user_repository.update(user)
            
            logger.info(f"Updated user: {user_id}")
            
            return UserResponseDTO(
                id=updated_user.id,
                name=updated_user.name,
                email=updated_user.email.value,
                phone=updated_user.phone.value,
                is_active=updated_user.is_active,
                created_at=updated_user.created_at,
                updated_at=updated_user.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    async def activate_user(self, user_id: str) -> UserResponseDTO:
        """Activate user account"""
        try:
            user = await self._user_repository.get_by_id(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            user.activate()
            updated_user = await self._user_repository.update(user)
            
            logger.info(f"Activated user: {user_id}")
            
            return UserResponseDTO(
                id=updated_user.id,
                name=updated_user.name,
                email=updated_user.email.value,
                phone=updated_user.phone.value,
                is_active=updated_user.is_active,
                created_at=updated_user.created_at,
                updated_at=updated_user.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error activating user {user_id}: {e}")
            raise
    
    async def deactivate_user(self, user_id: str) -> UserResponseDTO:
        """Deactivate user account"""
        try:
            user = await self._user_repository.get_by_id(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            user.deactivate()
            updated_user = await self._user_repository.update(user)
            
            logger.info(f"Deactivated user: {user_id}")
            
            return UserResponseDTO(
                id=updated_user.id,
                name=updated_user.name,
                email=updated_user.email.value,
                phone=updated_user.phone.value,
                is_active=updated_user.is_active,
                created_at=updated_user.created_at,
                updated_at=updated_user.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {e}")
            raise
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user permanently"""
        try:
            success = await self._user_repository.delete(user_id)
            
            if success:
                logger.info(f"Deleted user: {user_id}")
            else:
                logger.warning(f"User {user_id} not found for deletion")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise
    
    async def search_users(self, name: str, skip: int = 0, limit: int = 100) -> UserListResponseDTO:
        """Search users by name"""
        try:
            users = await self._user_repository.search_by_name(name, skip, limit)
            
            # For search results, we don't have exact total count, so we return the found count
            total = len(users)
            
            user_dtos = [
                UserResponseDTO(
                    id=user.id,
                    name=user.name,
                    email=user.email.value,
                    phone=user.phone.value,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
                for user in users
            ]
            
            return UserListResponseDTO(
                users=user_dtos,
                total=total,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error searching users by name '{name}': {e}")
            raise