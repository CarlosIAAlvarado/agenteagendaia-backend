from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from ....domain.entities.system_user import SystemUser, UserRole, UserStatus
from ....domain.value_objects.email import Email
from ..connection import get_database
import logging

logger = logging.getLogger(__name__)


class SystemUserRepository:
    """Repositorio para usuarios del sistema en MongoDB"""
    
    def __init__(self):
        self._collection_name = "system_users"
    
    async def _get_collection(self):
        """Obtiene la colección de usuarios del sistema"""
        db = await get_database()
        return db[self._collection_name]
    
    async def create(self, user: SystemUser) -> SystemUser:
        """
        Crea un nuevo usuario del sistema
        
        Args:
            user: Usuario a crear
        
        Returns:
            Usuario creado con ID asignado
        """
        try:
            collection = await self._get_collection()
            
            user_doc = {
                "email": user.email.value,
                "full_name": user.full_name,
                "hashed_password": user.hashed_password,
                "role": user.role.value,
                "status": user.status.value,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login": user.last_login
            }
            
            result = await collection.insert_one(user_doc)
            user.id = str(result.inserted_id)
            
            logger.info(f"Usuario del sistema creado: {user.email.value}")
            return user
            
        except Exception as e:
            logger.error(f"Error creando usuario del sistema: {e}")
            raise
    
    async def get_by_id(self, user_id: str) -> Optional[SystemUser]:
        """
        Obtiene un usuario por su ID
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Usuario si existe, None si no
        """
        try:
            collection = await self._get_collection()
            doc = await collection.find_one({"_id": ObjectId(user_id)})
            
            if doc:
                return self._document_to_user(doc)
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por ID {user_id}: {e}")
            return None
    
    async def get_by_email(self, email: str) -> Optional[SystemUser]:
        """
        Obtiene un usuario por su email
        
        Args:
            email: Email del usuario
        
        Returns:
            Usuario si existe, None si no
        """
        try:
            collection = await self._get_collection()
            doc = await collection.find_one({"email": email.lower()})
            
            if doc:
                return self._document_to_user(doc)
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por email {email}: {e}")
            return None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[SystemUser]:
        """
        Obtiene todos los usuarios del sistema
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a devolver
        
        Returns:
            Lista de usuarios del sistema
        """
        try:
            collection = await self._get_collection()
            cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)
            
            return [self._document_to_user(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error obteniendo todos los usuarios: {e}")
            return []
    
    async def get_by_role(self, role: UserRole) -> List[SystemUser]:
        """
        Obtiene usuarios por rol
        
        Args:
            role: Rol de usuario
        
        Returns:
            Lista de usuarios con ese rol
        """
        try:
            collection = await self._get_collection()
            cursor = collection.find({"role": role.value})
            docs = await cursor.to_list(length=None)
            
            return [self._document_to_user(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Error obteniendo usuarios por rol {role.value}: {e}")
            return []
    
    async def update(self, user: SystemUser) -> bool:
        """
        Actualiza un usuario del sistema
        
        Args:
            user: Usuario con datos actualizados
        
        Returns:
            True si se actualizó correctamente, False si no
        """
        try:
            if not user.id:
                return False
            
            collection = await self._get_collection()
            
            update_doc = {
                "$set": {
                    "email": user.email.value,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "status": user.status.value,
                    "updated_at": datetime.utcnow(),
                    "last_login": user.last_login
                }
            }
            
            # Si se actualizó la contraseña, incluirla
            if hasattr(user, "_password_updated") and user._password_updated:
                update_doc["$set"]["hashed_password"] = user.hashed_password
            
            result = await collection.update_one(
                {"_id": ObjectId(user.id)},
                update_doc
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error actualizando usuario {user.id}: {e}")
            return False
    
    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        """
        Actualiza solo la contraseña de un usuario
        
        Args:
            user_id: ID del usuario
            hashed_password: Nueva contraseña hasheada
        
        Returns:
            True si se actualizó correctamente, False si no
        """
        try:
            collection = await self._get_collection()
            
            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "hashed_password": hashed_password,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error actualizando contraseña del usuario {user_id}: {e}")
            return False
    
    async def update_last_login(self, user_id: str) -> bool:
        """
        Actualiza el último login del usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            True si se actualizó correctamente, False si no
        """
        try:
            collection = await self._get_collection()
            
            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "last_login": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error actualizando último login del usuario {user_id}: {e}")
            return False
    
    async def delete(self, user_id: str) -> bool:
        """
        Elimina un usuario del sistema
        
        Args:
            user_id: ID del usuario a eliminar
        
        Returns:
            True si se eliminó correctamente, False si no
        """
        try:
            collection = await self._get_collection()
            result = await collection.delete_one({"_id": ObjectId(user_id)})
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error eliminando usuario {user_id}: {e}")
            return False
    
    async def email_exists(self, email: str) -> bool:
        """
        Verifica si un email ya está registrado
        
        Args:
            email: Email a verificar
        
        Returns:
            True si el email existe, False si no
        """
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({"email": email.lower()})
            return count > 0
            
        except Exception as e:
            logger.error(f"Error verificando si existe email {email}: {e}")
            return False
    
    async def count_by_role(self, role: UserRole) -> int:
        """
        Cuenta usuarios por rol
        
        Args:
            role: Rol de usuario
        
        Returns:
            Número de usuarios con ese rol
        """
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"role": role.value})
            
        except Exception as e:
            logger.error(f"Error contando usuarios por rol {role.value}: {e}")
            return 0
    
    def _document_to_user(self, doc: dict) -> SystemUser:
        """
        Convierte un documento de MongoDB a una entidad SystemUser
        
        Args:
            doc: Documento de MongoDB
        
        Returns:
            Entidad SystemUser
        """
        return SystemUser(
            id=str(doc["_id"]),
            email=Email(doc["email"]),
            full_name=doc["full_name"],
            hashed_password=doc["hashed_password"],
            role=UserRole(doc["role"]),
            status=UserStatus(doc.get("status", UserStatus.ACTIVE.value)),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
            last_login=doc.get("last_login")
        )