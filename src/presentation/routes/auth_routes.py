from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from ...application.dto.auth_dto import (
    LoginRequest, RegisterRequest, LoginResponse, TokenResponse,
    RefreshTokenRequest, ChangePasswordRequest, UpdateProfileRequest,
    UserResponse, CreateUserRequest, UpdateUserRequest
)
from ...domain.entities.system_user import SystemUser, UserRole, UserStatus
from ...domain.value_objects.email import Email
from ...infrastructure.database.repositories.system_user_repository import SystemUserRepository
from ...infrastructure.auth.jwt_handler import AuthService
from ...infrastructure.auth.auth_middleware import (
    get_current_user, require_super_admin, require_admin
)
import logging

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Repositorio
user_repository = SystemUserRepository()


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """
    Registro de nuevo usuario
    Por defecto se crea con rol USER
    """
    try:
        # Verificar si el email ya existe
        if await user_repository.email_exists(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Hashear la contraseña
        hashed_password = AuthService.hash_password(request.password)
        
        # Crear nuevo usuario
        new_user = SystemUser(
            id=None,
            email=Email(request.email),
            full_name=request.full_name,
            hashed_password=hashed_password,
            role=request.role or UserRole.USER,
            status=UserStatus.ACTIVE
        )
        
        # Guardar en la base de datos
        created_user = await user_repository.create(new_user)
        
        # Actualizar último login
        await user_repository.update_last_login(created_user.id)
        
        # Crear tokens
        user_data = {
            "id": created_user.id,
            "email": created_user.email.value,
            "full_name": created_user.full_name,
            "role": created_user.role.value
        }
        tokens = AuthService.create_token_pair(user_data)
        
        # Preparar respuesta
        user_response = UserResponse(
            id=created_user.id,
            email=created_user.email.value,
            full_name=created_user.full_name,
            role=created_user.role.value,
            status=created_user.status.value,
            created_at=created_user.created_at,
            last_login=created_user.last_login,
            permissions=created_user.get_permissions_summary()["permissions"]
        )
        
        return LoginResponse(
            user=user_response,
            tokens=TokenResponse(**tokens),
            message="Registro exitoso"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en registro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el registro"
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login de usuario
    """
    try:
        # Buscar usuario por email
        user = await user_repository.get_by_email(request.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Verificar contraseña
        if not AuthService.verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Verificar que el usuario esté activo
        if not user.is_active():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo o suspendido"
            )
        
        # Actualizar último login
        await user_repository.update_last_login(user.id)
        
        # Crear tokens
        user_data = {
            "id": user.id,
            "email": user.email.value,
            "full_name": user.full_name,
            "role": user.role.value
        }
        tokens = AuthService.create_token_pair(user_data)
        
        # Preparar respuesta
        user_response = UserResponse(
            id=user.id,
            email=user.email.value,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            created_at=user.created_at,
            last_login=user.last_login,
            permissions=user.get_permissions_summary()["permissions"]
        )
        
        return LoginResponse(
            user=user_response,
            tokens=TokenResponse(**tokens)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el login"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refrescar tokens usando refresh token
    🔄 SLIDING SESSION: Genera NUEVOS access_token Y refresh_token
    El refresh_token se renueva con 7 días adicionales desde ahora
    """
    try:
        # Ahora retorna AMBOS tokens nuevos
        new_tokens = AuthService.refresh_access_token(request.refresh_token)

        if not new_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado"
            )

        logger.info("🔄 SLIDING SESSION: Tokens renovados - La sesión se extiende 7 días más")

        return TokenResponse(
            access_token=new_tokens["access_token"],
            refresh_token=new_tokens["refresh_token"],  # ← NUEVO refresh token
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refrescando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refrescando token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """
    Obtener información del usuario actual
    """
    try:
        user = await user_repository.get_by_id(current_user["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email.value,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            created_at=user.created_at,
            last_login=user.last_login,
            permissions=user.get_permissions_summary()["permissions"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo usuario actual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo información del usuario"
        )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Cambiar contraseña del usuario actual
    """
    try:
        user = await user_repository.get_by_id(current_user["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar contraseña actual
        if not AuthService.verify_password(request.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña actual incorrecta"
            )
        
        # Hashear nueva contraseña
        new_hashed_password = AuthService.hash_password(request.new_password)
        
        # Actualizar contraseña
        success = await user_repository.update_password(user.id, new_hashed_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error actualizando contraseña"
            )
        
        return {"message": "Contraseña actualizada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cambiando contraseña"
        )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualizar perfil del usuario actual
    """
    try:
        user = await user_repository.get_by_id(current_user["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Actualizar campos si se proporcionan
        if request.full_name:
            user.full_name = request.full_name
        
        if request.email:
            # Verificar que el nuevo email no esté en uso
            if request.email != user.email.value:
                if await user_repository.email_exists(request.email):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El email ya está en uso"
                    )
                user.email = Email(request.email)
        
        # Guardar cambios
        success = await user_repository.update(user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error actualizando perfil"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email.value,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            created_at=user.created_at,
            last_login=user.last_login,
            permissions=user.get_permissions_summary()["permissions"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error actualizando perfil"
        )


# ========== ENDPOINTS PARA SUPER ADMIN ==========

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user: Dict = Depends(require_super_admin)
):
    """
    Crear nuevo usuario (solo super admin)
    """
    try:
        # Verificar si el email ya existe
        if await user_repository.email_exists(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Hashear la contraseña
        hashed_password = AuthService.hash_password(request.password)
        
        # Crear nuevo usuario
        new_user = SystemUser(
            id=None,
            email=Email(request.email),
            full_name=request.full_name,
            hashed_password=hashed_password,
            role=request.role,
            status=request.status or UserStatus.ACTIVE
        )
        
        # Guardar en la base de datos
        created_user = await user_repository.create(new_user)
        
        return UserResponse(
            id=created_user.id,
            email=created_user.email.value,
            full_name=created_user.full_name,
            role=created_user.role.value,
            status=created_user.status.value,
            created_at=created_user.created_at,
            last_login=created_user.last_login,
            permissions=created_user.get_permissions_summary()["permissions"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando usuario"
        )


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: Dict = Depends(require_super_admin)
):
    """
    Obtener todos los usuarios (solo super admin)
    """
    try:
        users = await user_repository.get_all(skip, limit)
        
        return [
            UserResponse(
                id=user.id,
                email=user.email.value,
                full_name=user.full_name,
                role=user.role.value,
                status=user.status.value,
                created_at=user.created_at,
                last_login=user.last_login,
                permissions=user.get_permissions_summary()["permissions"]
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo usuarios"
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: Dict = Depends(require_super_admin)
):
    """
    Actualizar usuario (solo super admin)
    """
    try:
        user = await user_repository.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Actualizar campos si se proporcionan
        if request.full_name:
            user.full_name = request.full_name
        
        if request.email:
            if request.email != user.email.value:
                if await user_repository.email_exists(request.email):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El email ya está en uso"
                    )
                user.email = Email(request.email)
        
        if request.role:
            user.role = request.role
        
        if request.status:
            user.status = request.status
        
        # Guardar cambios
        success = await user_repository.update(user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error actualizando usuario"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email.value,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            created_at=user.created_at,
            last_login=user.last_login,
            permissions=user.get_permissions_summary()["permissions"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error actualizando usuario"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict = Depends(require_super_admin)
):
    """
    Eliminar usuario (solo super admin)
    """
    try:
        # No permitir auto-eliminación
        if user_id == current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propia cuenta"
            )
        
        success = await user_repository.delete(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return {"message": "Usuario eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error eliminando usuario"
        )