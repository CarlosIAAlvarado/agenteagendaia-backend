#!/usr/bin/env python3
"""
Script para crear el usuario Super Admin inicial del sistema
Ejecutar una sola vez para configurar el acceso inicial a la plataforma
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar las dependencias necesarias
from src.domain.entities.system_user import SystemUser, UserRole, UserStatus
from src.domain.value_objects.email import Email
from src.infrastructure.database.repositories.system_user_repository import SystemUserRepository
from src.infrastructure.auth.jwt_handler import AuthService
from src.infrastructure.database.connection import initialize_database

async def create_super_admin():
    """
    Crea el usuario Super Admin inicial
    """
    try:
        # Inicializar la conexión a la base de datos
        await initialize_database()
        print("[OK] Conexión a MongoDB Atlas establecida")
        
        # Crear repositorio de usuarios
        user_repository = SystemUserRepository()
        
        # Credenciales del Super Admin
        SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL", "admin@agenda-ia.com")
        SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "SuperAdmin123!")
        SUPER_ADMIN_NAME = os.getenv("SUPER_ADMIN_NAME", "Super Administrador")
        
        print(f"[INFO] Verificando si el Super Admin ya existe: {SUPER_ADMIN_EMAIL}")
        
        # Verificar si ya existe un super admin con ese email
        existing_user = await user_repository.get_by_email(SUPER_ADMIN_EMAIL)
        
        if existing_user:
            print(f"[WARNING] Ya existe un usuario con el email: {SUPER_ADMIN_EMAIL}")
            print(f"   Rol actual: {existing_user.role.value}")
            print(f"   Estado: {existing_user.status.value}")
            
            # Si el usuario existe pero no es super admin, actualizarlo
            if existing_user.role != UserRole.SUPER_ADMIN:
                print("[INFO] Actualizando usuario existente a Super Admin...")
                existing_user.role = UserRole.SUPER_ADMIN
                existing_user.status = UserStatus.ACTIVE
                
                success = await user_repository.update(existing_user)
                if success:
                    print("[OK] Usuario actualizado exitosamente a Super Admin")
                else:
                    print("[ERROR] Error actualizando el usuario")
                    return False
            else:
                print("[OK] El Super Admin ya existe y está configurado correctamente")
            
            return True
        
        # Crear nuevo Super Admin
        print(f"[INFO] Creando nuevo Super Admin: {SUPER_ADMIN_EMAIL}")
        
        # Hashear la contraseña
        hashed_password = AuthService.hash_password(SUPER_ADMIN_PASSWORD)
        
        # Crear el usuario
        super_admin = SystemUser(
            id=None,
            email=Email(SUPER_ADMIN_EMAIL),
            full_name=SUPER_ADMIN_NAME,
            hashed_password=hashed_password,
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE
        )
        
        # Guardar en la base de datos
        created_user = await user_repository.create(super_admin)
        
        if created_user and created_user.id:
            print("[SUCCESS] Super Admin creado exitosamente!")
            print(f"   ID: {created_user.id}")
            print(f"   Email: {created_user.email.value}")
            print(f"   Nombre: {created_user.full_name}")
            print(f"   Rol: {created_user.role.value}")
            print(f"   Estado: {created_user.status.value}")
            print(f"   Creado: {created_user.created_at}")
            
            print("\n[CREDENTIALS] CREDENCIALES DE ACCESO:")
            print(f"   Email: {SUPER_ADMIN_EMAIL}")
            print(f"   Contraseña: {SUPER_ADMIN_PASSWORD}")
            print("\n[IMPORTANT] IMPORTANTE: Cambia la contraseña después del primer login")
            
            return True
        else:
            print("[ERROR] Error creando el Super Admin")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error durante la inicialización: {e}")
        return False

async def verify_super_admin():
    """
    Verifica que el Super Admin fue creado correctamente
    """
    try:
        user_repository = SystemUserRepository()
        
        # Buscar usuarios con rol de Super Admin
        super_admins = await user_repository.get_by_role(UserRole.SUPER_ADMIN)
        
        print(f"\n[SUMMARY] RESUMEN DEL SISTEMA:")
        print(f"   Super Admins encontrados: {len(super_admins)}")
        
        for admin in super_admins:
            print(f"   - {admin.email.value} (ID: {admin.id}) - {admin.status.value}")
        
        # Contar usuarios por rol
        total_super_admins = await user_repository.count_by_role(UserRole.SUPER_ADMIN)
        total_admins = await user_repository.count_by_role(UserRole.ADMIN)
        total_users = await user_repository.count_by_role(UserRole.USER)
        
        print(f"\n[STATS] ESTADÍSTICAS DE USUARIOS:")
        print(f"   Super Admins: {total_super_admins}")
        print(f"   Admins: {total_admins}")
        print(f"   Users: {total_users}")
        print(f"   Total: {total_super_admins + total_admins + total_users}")
        
        return len(super_admins) > 0
        
    except Exception as e:
        print(f"[ERROR] Error verificando el sistema: {e}")
        return False

async def main():
    """
    Función principal del script
    """
    print("[INIT] INICIALIZADOR DE SUPER ADMIN - AGENDA IA")
    print("=" * 50)
    
    # Crear Super Admin
    success = await create_super_admin()
    
    if success:
        # Verificar que todo esté correcto
        await verify_super_admin()
        
        print("\n[SUCCESS] INICIALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print("\n[NEXT] PRÓXIMOS PASOS:")
        print("1. Inicia el servidor backend: python -m uvicorn main:app --reload --port 8000")
        print("2. Ve a la página de login del dashboard")
        print("3. Inicia sesión con las credenciales mostradas arriba")
        print("4. Cambia la contraseña desde el perfil de usuario")
        print("5. Crea usuarios adicionales según sea necesario")
        
    else:
        print("\n[ERROR] LA INICIALIZACIÓN FALLÓ")
        print("Verifica la configuración de la base de datos y las variables de entorno")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    # Ejecutar el script
    asyncio.run(main())