from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de seguridad
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tu-clave-secreta-super-segura-cambiar-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hora
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 días

# Contexto de encriptación para contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Servicio de autenticación y manejo de JWT"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica si la contraseña plana coincide con el hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera un hash de la contraseña"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea un token de acceso JWT
        
        Args:
            data: Datos a codificar en el token (user_id, email, role, etc.)
            expires_delta: Tiempo de expiración opcional
        
        Returns:
            Token JWT codificado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Crea un token de actualización JWT
        
        Args:
            data: Datos a codificar en el token
        
        Returns:
            Refresh token JWT codificado
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decodifica y valida un token JWT
        
        Args:
            token: Token JWT a decodificar
        
        Returns:
            Payload del token si es válido, None si no lo es
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verifica y decodifica un token JWT
        
        Args:
            token: Token JWT a verificar
            token_type: Tipo de token esperado ("access" o "refresh")
        
        Returns:
            Payload del token si es válido y del tipo correcto, None si no
        """
        payload = AuthService.decode_token(token)
        
        if payload and payload.get("type") == token_type:
            return payload
        
        return None
    
    @staticmethod
    def create_token_pair(user_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Crea un par de tokens (access y refresh)
        
        Args:
            user_data: Datos del usuario a incluir en los tokens
        
        Returns:
            Diccionario con access_token y refresh_token
        """
        # Datos esenciales para incluir en el token
        token_data = {
            "user_id": user_data.get("id"),
            "email": user_data.get("email"),
            "role": user_data.get("role"),
            "full_name": user_data.get("full_name")
        }
        
        access_token = AuthService.create_access_token(token_data)
        refresh_token = AuthService.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Genera nuevos tokens (access Y refresh) usando un refresh token válido
        Implementa SLIDING SESSION: El refresh token se renueva con 7 días adicionales

        Args:
            refresh_token: Refresh token JWT

        Returns:
            Diccionario con nuevo access_token y refresh_token si es válido, None si no
        """
        payload = AuthService.verify_token(refresh_token, "refresh")

        if payload:
            # Crear nuevos tokens con los mismos datos
            token_data = {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "full_name": payload.get("full_name")
            }

            # 🔄 SLIDING SESSION: Generar AMBOS tokens nuevos
            # Esto reinicia el contador de 7 días cada vez que el usuario está activo
            new_access_token = AuthService.create_access_token(token_data)
            new_refresh_token = AuthService.create_refresh_token(token_data)  # ← NUEVO refresh con 7 días más

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }

        return None