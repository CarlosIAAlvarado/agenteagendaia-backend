# 🚀 Agenda IA - Backend API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/atlas)
[![Status](https://img.shields.io/badge/Status-Funcional-brightgreen.svg)](.)

> Backend del sistema de agendamiento inteligente con arquitectura hexagonal, FastAPI y MongoDB Atlas.

## 📋 Estado Actual - v1.0 (Post-Fix)

**✅ COMPLETAMENTE FUNCIONAL** - Última actualización: 12/09/2025

### 🔧 Problemas Solucionados:
- ✅ **Creación de servicios**: Índice único problemático eliminado
- ✅ **MongoDB Atlas**: Conexión estable y índices optimizados  
- ✅ **API Endpoints**: Todos los CRUD funcionando correctamente
- ✅ **Validación de datos**: Manejo de errores mejorado en español
- ✅ **WebSockets**: Chat en tiempo real operativo

## 🏗️ Arquitectura Hexagonal

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                   │
│  • Routes (FastAPI)     • Controllers    • WebSockets  │
│  • Request/Response     • Middleware     • Error Handlers│
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────┐
│                   APPLICATION LAYER                     │
│  • Use Cases           • DTOs (Pydantic)               │
│  • Business Logic     • Data Validation                │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────┐
│                     DOMAIN LAYER                        │
│  • Entities           • Domain Services                │
│  • Repository Interfaces    • Business Rules           │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                    │
│  • MongoDB Atlas      • OpenAI API    • ChromaDB      │
│  • External Services  • Database Mappers              │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Inicio Rápido

### Prerrequisitos
```bash
# Python 3.11 o superior
python --version
# Python 3.11.x

# pip actualizado
pip install --upgrade pip
```

### Instalación
```bash
# 1. Navegar al directorio backend
cd backend

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 4. Iniciar servidor de desarrollo
python main.py
```

### Verificación
- **API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs  
- **Documentación ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## ⚙️ Configuración

### Variables de Entorno (`.env`)
```env
# Base de Datos
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/
DATABASE_NAME=Agenda_Ai

# Inteligencia Artificial  
OPENAI_API_KEY=sk-proj-...
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Servidor
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Seguridad
SECRET_KEY=tu_clave_secreta_muy_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logs
LOG_LEVEL=INFO
```

## 📊 Estructura del Proyecto

```
backend/
├── main.py                     # Punto de entrada de la aplicación
├── requirements.txt            # Dependencias Python
├── .env.example               # Plantilla de variables de entorno
├── chroma_db/                 # Base de datos vectorial ChromaDB
└── src/
    ├── __init__.py
    ├── application/           # Capa de Aplicación
    │   ├── dto/              # Data Transfer Objects
    │   │   ├── appointment_dto.py
    │   │   ├── auth_dto.py
    │   │   ├── service_dto.py
    │   │   └── user_dto.py
    │   └── use_cases/        # Casos de Uso
    │       ├── appointment_use_cases.py
    │       ├── service_use_cases.py
    │       └── user_use_cases.py
    ├── domain/               # Capa de Dominio
    │   ├── entities/         # Entidades de Negocio
    │   │   ├── appointment.py
    │   │   ├── service.py
    │   │   └── user.py
    │   ├── repositories/     # Interfaces de Repositorio
    │   │   ├── appointment_repository.py
    │   │   └── service_repository.py
    │   └── services/         # Servicios de Dominio
    │       └── ai_tools/     # Herramientas de IA
    ├── infrastructure/       # Capa de Infraestructura
    │   ├── ai/              # Integración OpenAI
    │   │   └── agenda_ia_agent_fallback.py
    │   ├── config/          # Configuración
    │   │   ├── database.py
    │   │   └── settings.py
    │   └── database/        # Implementación MongoDB
    │       ├── connection.py
    │       ├── mappers/     # Mappers Entidad <-> Documento
    │       └── repositories/ # Implementaciones de Repositorio
    └── presentation/        # Capa de Presentación
        ├── controllers/     # Controladores API
        ├── middleware/      # Middleware
        ├── routes/          # Definición de Rutas
        └── websockets/      # WebSocket Handlers
```

## 🛠️ Tecnologías Implementadas

### Core Framework
- **FastAPI 0.104+**: Framework web moderno, rápido y con documentación automática
- **Uvicorn**: Servidor ASGI de alta performance
- **Pydantic 2.0+**: Validación de datos y serialización

### Base de Datos
- **MongoDB Atlas**: Base de datos NoSQL en la nube
- **Motor**: Driver asíncrono de MongoDB para Python
- **ChromaDB**: Base de datos vectorial para RAG

### Inteligencia Artificial
- **OpenAI API**: GPT-4o-mini para conversación natural
- **LangChain**: Framework para aplicaciones con LLM
- **Sentence Transformers**: Embeddings para búsqueda semántica

### Seguridad & Autenticación
- **JWT**: JSON Web Tokens para autenticación
- **Passlib**: Hashing de contraseñas
- **Python-Jose**: Manejo de tokens JWT

### Desarrollo & Calidad
- **Python-Dotenv**: Manejo de variables de entorno
- **Pytest**: Framework de testing
- **Black**: Formateo de código
- **Flake8**: Linting

## 📡 API Endpoints

### Servicios (`/api/v1/services/`)
```http
GET    /api/v1/services/           # Listar servicios
POST   /api/v1/services/           # Crear servicio ✅ FUNCIONAL
PUT    /api/v1/services/{id}       # Actualizar servicio
DELETE /api/v1/services/{id}       # Eliminar servicio
GET    /api/v1/services/{id}       # Obtener servicio por ID
GET    /api/v1/services/search?q=  # Buscar servicios
```

### Usuarios (`/api/v1/users/`)
```http
GET    /api/v1/users/              # Listar usuarios
POST   /api/v1/users/              # Crear usuario
PUT    /api/v1/users/{id}          # Actualizar usuario
DELETE /api/v1/users/{id}          # Eliminar usuario
```

### Citas (`/api/v1/appointments/`)
```http
GET    /api/v1/appointments/       # Listar citas
POST   /api/v1/appointments/       # Crear cita
PUT    /api/v1/appointments/{id}   # Actualizar cita
DELETE /api/v1/appointments/{id}   # Cancelar cita
GET    /api/v1/appointments/calendar # Vista calendario
```

### Profesionales (`/api/v1/professionals/`)
```http
GET    /api/v1/professionals/      # Listar profesionales
POST   /api/v1/professionals/      # Crear profesional
PUT    /api/v1/professionals/{id}  # Actualizar profesional
```

### Chat IA (`/api/v1/chat/`)
```http
POST   /api/v1/chat/               # Enviar mensaje a IA
WS     /ws/chat                    # WebSocket para chat en tiempo real
```

### Utilitarios
```http
GET    /health                     # Health check
GET    /docs                       # Documentación Swagger UI
GET    /redoc                      # Documentación ReDoc
```

## 📊 Base de Datos MongoDB

### Colecciones
```javascript
// services - Servicios disponibles
{
  "_id": ObjectId,
  "name": "Consulta General",           // ✅ SIN índice único
  "description": "Consulta médica general",
  "duration_minutes": 30,
  "service_type": "medical",
  "service_mode": "presential", 
  "price": 50000.0,
  "is_active": true,
  "created_at": ISODate,
  "updated_at": ISODate
}

// users - Usuarios/Pacientes  
{
  "_id": ObjectId,
  "name": "Juan Pérez",
  "email": { "value": "juan@email.com" },  // ✅ Índice único
  "phone": { "value": "+57123456789" },
  "identification": "12345678",
  "is_active": true
}

// professionals - Profesionales de salud
{
  "_id": ObjectId, 
  "name": "Dr. Ana García",
  "email": { "value": "ana@clinica.com" }, // ✅ Índice único
  "specialization": "Medicina General",
  "service_ids": [ObjectId, ObjectId],
  "is_active": true
}

// appointments - Citas programadas
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "professional_id": ObjectId, 
  "service_id": ObjectId,
  "time_slot": {
    "start_time": ISODate,
    "end_time": ISODate
  },
  "status": "scheduled", // scheduled, confirmed, completed, cancelled
  "notes": "Consulta de control"
}
```

### Índices Configurados ✅
```javascript
// Índices NO únicos (permiten duplicados)
db.services.createIndex({"name": 1}, {unique: false})

// Índices únicos (necesarios para integridad)  
db.users.createIndex({"email.value": 1}, {unique: true})
db.professionals.createIndex({"email.value": 1}, {unique: true})

// Índices compuestos para consultas eficientes
db.appointments.createIndex({"professional_id": 1, "time_slot.start_time": 1})
db.appointments.createIndex({"user_id": 1, "status": 1})
```

## 🤖 Sistema de IA

### Agente Conversacional
- **Modelo**: GPT-4o-mini de OpenAI
- **Capacidades**: Comprensión de intenciones, generación de respuestas naturales
- **Herramientas**: Programación de citas, consulta de disponibilidad, registro express

### RAG (Retrieval Augmented Generation)
- **Vector DB**: ChromaDB para almacenar embeddings
- **Embeddings**: Sentence Transformers para búsqueda semántica
- **Contexto**: Información sobre servicios, profesionales y políticas

### Herramientas Disponibles
1. **appointment_scheduling_tool**: Programar nuevas citas
2. **express_registration_tool**: Registro rápido de usuarios
3. **service_consultation_tool**: Consultar información de servicios

## 🔒 Seguridad Implementada

### Validación de Datos
```python
# Todos los endpoints validan entrada con Pydantic
class ServiceCreateDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    duration_minutes: int = Field(..., gt=0, le=480)
    service_type: ServiceType
    price: Optional[float] = Field(None, ge=0)
```

### Manejo de Errores  
- Excepciones centralizadas con middleware
- Logs estructurados para debugging
- Respuestas de error consistentes en español

### Variables de Entorno
- Configuración sensible en `.env`
- Validación de configuración al inicio
- Secrets separados del código fuente

## 🧪 Testing

### Ejecutar Tests
```bash
# Tests unitarios
pytest tests/ -v

# Tests con cobertura
pytest tests/ --cov=src --cov-report=html

# Tests de integración
pytest tests/integration/ -v
```

### Estructura de Tests
```
tests/
├── unit/                    # Tests unitarios
│   ├── test_use_cases.py
│   ├── test_entities.py
│   └── test_repositories.py
├── integration/             # Tests de integración  
│   ├── test_api_endpoints.py
│   └── test_database.py
└── fixtures/               # Datos de prueba
    └── sample_data.py
```

## 📈 Monitoreo & Logs

### Logging Configurado
```python
# Configuración de logs en main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Métricas Disponibles
- Tiempo de respuesta de endpoints
- Conexiones a base de datos
- Errores por tipo y endpoint
- Uso de memoria y CPU

## 🚀 Despliegue

### Desarrollo Local
```bash
# Servidor de desarrollo con hot reload
python main.py

# Configuración automática:
# - Host: 0.0.0.0:8000  
# - Reload: Activado
# - Docs: /docs disponible
```

### Producción
```bash
# Usando Uvicorn directamente
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# O usando Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker
```dockerfile
# Dockerfile incluido en el proyecto
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 📚 Documentación de APIs

### Swagger UI
Accede a `http://localhost:8000/docs` para:
- Explorar todos los endpoints disponibles
- Probar requests directamente desde el navegador  
- Ver esquemas de request/response
- Descargar especificación OpenAPI

### ReDoc
Accede a `http://localhost:8000/redoc` para:
- Documentación más legible y estructurada
- Navegación por categorías
- Ejemplos de uso detallados

## 🔧 Scripts Útiles

### Mantenimiento de Base de Datos
```bash
# Limpiar índices problemáticos
python clean_database.py

# Poblar datos de prueba
python populate_realistic_data.py

# Verificar integridad
python verify_db_fields.py
```

### Debugging
```bash
# Verificar conexión MongoDB
python -c "from src.infrastructure.config.database import ping_database; print(ping_database())"

# Test específico de servicios
python test_service_creation.py
```

## 📝 Changelog Backend

### v1.0 (Post-Fix) - 12/09/2025
- ✅ **SOLUCIONADO**: Eliminado índice único problemático `service_id_1`
- ✅ **MEJORADO**: Validación de servicios con mensajes en español
- ✅ **OPTIMIZADO**: Configuración de índices MongoDB Atlas
- ✅ **ESTABILIZADO**: Conexión con base de datos sin errores

### v0.9 (Pre-Fix)  
- ⚠️ Índices únicos causando DuplicateKeyError
- ⚠️ Problemas al crear servicios desde API
- ⚠️ Errores de conexión intermitentes

## 🤝 Contribución

1. Seguir arquitectura hexagonal establecida
2. Implementar tests para nuevas funcionalidades  
3. Validar con Pydantic todos los datos de entrada
4. Mantener documentación actualizada
5. Usar logging apropiado para debugging

## 📞 Soporte

Para problemas técnicos:
1. Verificar logs en consola y `app.log`
2. Validar variables de entorno en `.env`
3. Confirmar conexión a MongoDB Atlas
4. Revisar documentación en `/docs`

---

**🎉 Backend completamente funcional y listo para producción!**

*Última actualización: 12 de Septiembre, 2025*