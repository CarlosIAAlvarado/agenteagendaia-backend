from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from .jwt_handler import AuthService
from ...domain.entities.system_user import UserRole

# Esquema de seguridad HTTP Bearer
security = HTTPBearer()


class AuthMiddleware:
    """Middleware para autenticación y autorización"""
    
    @staticmethod
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """
        Obtiene el usuario actual desde el token JWT
        
        Args:
            credentials: Credenciales de autorización HTTP
        
        Returns:
            Datos del usuario decodificados del token
        
        Raises:
            HTTPException: Si el token es inválido o ha expirado
        """
        token = credentials.credentials
        
        # Verificar y decodificar el token
        payload = AuthService.verify_token(token, "access")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    @staticmethod
    async def require_role(required_roles: list[UserRole]):
        """
        Middleware para requerir roles específicos
        
        Args:
            required_roles: Lista de roles permitidos
        
        Returns:
            Función de dependencia que verifica el rol del usuario
        """
        async def role_checker(current_user: Dict = Depends(AuthMiddleware.get_current_user)):
            user_role = current_user.get("role")
            
            # Convertir el string del role a UserRole enum
            try:
                user_role_enum = UserRole(user_role)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Rol de usuario inválido"
                )
            
            # Verificar si el usuario tiene uno de los roles requeridos
            if user_role_enum not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No tienes permisos suficientes. Se requiere rol: {', '.join([r.value for r in required_roles])}"
                )
            
            return current_user
        
        return role_checker
    
    
    @staticmethod
    async def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
        """
        Autenticación opcional - no lanza error si no hay token
        
        Args:
            credentials: Credenciales de autorización HTTP opcionales
        
        Returns:
            Datos del usuario si hay token válido, None si no hay token
        """
        if not credentials:
            return None
        
        token = credentials.credentials
        payload = AuthService.verify_token(token, "access")
        
        return payload


# Funciones de conveniencia para usar en las rutas
get_current_user = AuthMiddleware.get_current_user

def require_super_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Requiere que el usuario sea Super Admin
    
    Args:
        current_user: Usuario actual obtenido del token
    
    Returns:
        Datos del usuario si es Super Admin
    
    Raises:
        HTTPException: Si el usuario no es Super Admin
    """
    if current_user.get("role") != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de Super Administrador"
        )
    return current_user

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Requiere que el usuario sea Admin o Super Admin
    
    Args:
        current_user: Usuario actual obtenido del token
    
    Returns:
        Datos del usuario si es Admin o Super Admin
    
    Raises:
        HTTPException: Si el usuario no es Admin o Super Admin
    """
    allowed_roles = [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de Administrador"
        )
    return current_user

optional_auth = AuthMiddleware.optional_auth

def require_roles(*roles: UserRole):
    """
    Función helper para requerir múltiples roles
    
    Args:
        *roles: Roles permitidos
    
    Returns:
        Dependencia de FastAPI
    """
    return Depends(AuthMiddleware.require_role(list(roles)))