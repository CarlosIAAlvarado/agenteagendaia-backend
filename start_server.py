#!/usr/bin/env python3
"""
Script mejorado para ejecutar el servidor Agenda IA
Incluye validaciones y mejores prácticas
"""
import uvicorn
import sys
import os
from pathlib import Path

def main():
    """Ejecuta el servidor con configuración optimizada"""
    
    # Verificar que estamos en el directorio correcto
    if not Path("main.py").exists():
        print("❌ Error: Este script debe ejecutarse desde el directorio backend/")
        sys.exit(1)
    
    # Verificar que existe el archivo .env
    if not Path(".env").exists():
        print("⚠️  Advertencia: No se encontró archivo .env")
        print("   Asegúrate de que las variables de entorno estén configuradas")
    
    print("🚀 Iniciando Agenda IA API Server...")
    print("📍 Host: 0.0.0.0")
    print("🔌 Puerto: 8000") 
    print("🔄 Auto-reload: Activado")
    print("📖 Documentación: http://localhost:8000/docs")
    print("🌐 API Base: http://localhost:8000/api/v1")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["src"],  # Solo recargar cuando cambien archivos en src/
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error al iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()