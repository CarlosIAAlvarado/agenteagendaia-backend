@echo off
echo ========================================
echo   AGENDA IA - INSTALAR DEPENDENCIAS
echo ========================================
echo.

echo Actualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando dependencias principales...
pip install fastapi==0.109.0
pip install uvicorn[standard]==0.27.0
pip install motor==3.3.2
pip install pymongo==4.6.1
pip install openai==1.10.0
pip install pydantic==2.5.3
pip install pydantic-settings==2.1.0
pip install python-dotenv==1.0.1
pip install websockets==12.0
pip install email-validator==2.1.0
pip install python-jose[cryptography]==3.3.0
pip install chromadb==0.4.22
pip install sentence-transformers==2.3.1
pip install numpy==1.26.3
pip install aiofiles==23.2.1
pip install requests==2.31.0

echo.
echo ========================================
echo   INSTALACION COMPLETADA
echo ========================================
echo.

echo Probando conexiones...
python test_connections.py

pause