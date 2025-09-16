from datetime import datetime
from typing import Optional
from enum import Enum
from dataclasses import dataclass
from ..value_objects.email import Email


class UserRole(Enum):
    """Roles de usuario del sistema"""
    SUPER_ADMIN = "super_admin"  # Control total
    ADMIN = "admin"              # Gestionar citas + ver datos
    USER = "user"                # Solo acceso al chat IA


class UserStatus(Enum):
    """Estado del usuario del sistema"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


@dataclass
class SystemUser:
    """Usuario del sistema con autenticación y control de acceso basado en roles"""
    
    id: Optional[str]
    email: Email
    full_name: str
    hashed_password: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        """Validación e inicialización"""
        if not self.full_name or len(self.full_name.strip()) < 2:
            raise ValueError("El nombre completo debe tener al menos 2 caracteres")
        
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    # Métodos de verificación de estado
    def is_active(self) -> bool:
        """Verifica si el usuario está activo"""
        return self.status == UserStatus.ACTIVE
    
    def is_super_admin(self) -> bool:
        """Verifica si es super administrador"""
        return self.role == UserRole.SUPER_ADMIN
    
    def is_admin(self) -> bool:
        """Verifica si es administrador o super administrador"""
        return self.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    def is_basic_user(self) -> bool:
        """Verifica si es un usuario básico"""
        return self.role == UserRole.USER
    
    # Permisos específicos por rol
    def can_access_dashboard(self) -> bool:
        """
        Puede acceder al dashboard
        Super Admin: Sí
        Admin: Sí
        User: No
        """
        return self.is_admin() and self.is_active()
    
    def can_manage_all_data(self) -> bool:
        """
        Puede gestionar todos los datos (crear, editar, eliminar todo)
        Super Admin: Sí
        Admin: No
        User: No
        """
        return self.is_super_admin() and self.is_active()
    
    def can_manage_appointments(self) -> bool:
        """
        Puede gestionar citas (crear, editar, eliminar, reagendar)
        Super Admin: Sí
        Admin: Sí
        User: No
        """
        return self.is_admin() and self.is_active()
    
    def can_view_all_appointments(self) -> bool:
        """
        Puede ver todas las citas
        Super Admin: Sí
        Admin: Sí
        User: No
        """
        return self.is_admin() and self.is_active()
    
    def can_manage_users(self) -> bool:
        """
        Puede gestionar otros usuarios del sistema
        Super Admin: Sí
        Admin: No
        User: No
        """
        return self.is_super_admin() and self.is_active()
    
    def can_manage_professionals(self) -> bool:
        """
        Puede gestionar profesionales
        Super Admin: Sí
        Admin: No (solo puede ver)
        User: No
        """
        return self.is_super_admin() and self.is_active()
    
    def can_manage_services(self) -> bool:
        """
        Puede gestionar servicios
        Super Admin: Sí
        Admin: No (solo puede ver)
        User: No
        """
        return self.is_super_admin() and self.is_active()
    
    def can_view_reports(self) -> bool:
        """
        Puede ver reportes y estadísticas
        Super Admin: Sí
        Admin: Sí
        User: No
        """
        return self.is_admin() and self.is_active()
    
    def can_access_chat(self) -> bool:
        """
        Puede acceder al chat con IA
        Super Admin: Sí
        Admin: Sí
        User: Sí
        """
        return self.is_active()
    
    def can_export_data(self) -> bool:
        """
        Puede exportar datos
        Super Admin: Sí
        Admin: No
        User: No
        """
        return self.is_super_admin() and self.is_active()
    
    # Métodos de actualización
    def update_last_login(self):
        """Actualiza el timestamp del último login"""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def change_role(self, new_role: UserRole):
        """Cambia el rol del usuario (solo super admin puede hacer esto)"""
        self.role = new_role
        self.updated_at = datetime.utcnow()
    
    def update_profile(self, full_name: Optional[str] = None, email: Optional[Email] = None):
        """Actualiza información del perfil"""
        if full_name:
            if len(full_name.strip()) < 2:
                raise ValueError("El nombre completo debe tener al menos 2 caracteres")
            self.full_name = full_name.strip()
        
        if email:
            self.email = email
        
        self.updated_at = datetime.utcnow()
    
    def update_password(self, new_hashed_password: str):
        """Actualiza la contraseña hasheada"""
        self.hashed_password = new_hashed_password
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Desactiva la cuenta del usuario"""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Activa la cuenta del usuario"""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def suspend(self):
        """Suspende la cuenta del usuario"""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
    
    def get_permissions_summary(self) -> dict:
        """Obtiene un resumen de todos los permisos del usuario"""
        return {
            "role": self.role.value,
            "status": self.status.value,
            "permissions": {
                "access_dashboard": self.can_access_dashboard(),
                "manage_all_data": self.can_manage_all_data(),
                "manage_appointments": self.can_manage_appointments(),
                "view_all_appointments": self.can_view_all_appointments(),
                "manage_users": self.can_manage_users(),
                "manage_professionals": self.can_manage_professionals(),
                "manage_services": self.can_manage_services(),
                "view_reports": self.can_view_reports(),
                "access_chat": self.can_access_chat(),
                "export_data": self.can_export_data()
            }
        }
    
    def __str__(self):
        return f"SystemUser({self.email.value}, {self.role.value})"
    
    def __repr__(self):
        return self.__str__()