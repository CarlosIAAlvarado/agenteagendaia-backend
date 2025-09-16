"""
MongoDB Atlas Database Connection Configuration
"""

import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.server_api import ServerApi
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class DatabaseConnection:
    """MongoDB Atlas connection manager"""
    
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    
    # MongoDB Atlas Configuration from settings
    MONGODB_URI = settings.mongodb_uri
    DATABASE_NAME = settings.database_name
    
    @classmethod
    async def get_client(cls) -> AsyncIOMotorClient:
        """Get MongoDB client instance"""
        if cls._client is None:
            try:
                logger.info("Connecting to MongoDB Atlas...")
                cls._client = AsyncIOMotorClient(
                    cls.MONGODB_URI,
                    server_api=ServerApi('1'),
                    maxPoolSize=50,
                    minPoolSize=10,
                    maxIdleTimeMS=45000,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=20000,
                    socketTimeoutMS=30000,
                    retryWrites=True,
                    retryReads=True,
                    w='majority',
                )
                
                # Test the connection
                await cls._client.admin.command('ping')
                logger.info("Successfully connected to MongoDB Atlas!")
                
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB Atlas: {e}")
                raise ConnectionError(f"Database connection failed: {e}")
        
        return cls._client
    
    @classmethod
    async def get_database(cls) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if cls._database is None:
            client = await cls.get_client()
            cls._database = client[cls.DATABASE_NAME]
            logger.info(f"Connected to database: {cls.DATABASE_NAME}")
        
        return cls._database
    
    @classmethod
    async def close_connection(cls):
        """Close database connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("Database connection closed")
    
    @classmethod
    async def health_check(cls) -> dict:
        """Check database connection health"""
        try:
            client = await cls.get_client()
            # Simple ping to check connectivity
            result = await client.admin.command('ping')
            
            # Try to access our specific database (no admin privileges needed)
            db = await cls.get_database()
            collections = await db.list_collection_names()
            
            return {
                "status": "healthy",
                "ping": result,
                "database": cls.DATABASE_NAME,
                "collections_count": len(collections),
                "connection_test": "successful"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": cls.DATABASE_NAME
            }

# Global connection instance
database_connection = DatabaseConnection()

# Convenience functions for dependency injection
async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance for dependency injection"""
    return await database_connection.get_database()

async def get_client() -> AsyncIOMotorClient:
    """Get client instance for dependency injection"""
    return await database_connection.get_client()

# Database collections configuration
class Collections:
    """Database collection names"""
    USERS = "users"
    SERVICES = "services"
    PROFESSIONALS = "professionals"
    APPOINTMENTS = "appointments"
    CONVERSATIONS = "conversations"
    APPOINTMENT_LINKS = "appointment_links"
    LINK_SECURITY_EVENTS = "link_security_events"
    SURVEYS = "surveys"
    SURVEY_RESPONSES = "survey_responses"
    METRICS = "metrics"
    SYSTEM_LOGS = "system_logs"

# Initialize database indexes on startup
async def initialize_database():
    """Initialize database with required indexes"""
    try:
        database = await get_database()
        logger.info("Initializing database indexes...")
        
        # Users collection indexes
        await database[Collections.USERS].create_index("email.value", unique=True)
        await database[Collections.USERS].create_index("phone.value", unique=True)
        
        # Appointments collection indexes
        # Removed unique index on appointment_id - draft appointments have null appointment_id
        await database[Collections.APPOINTMENTS].create_index("user_id")
        await database[Collections.APPOINTMENTS].create_index("professional_id")
        await database[Collections.APPOINTMENTS].create_index("appointment_date")
        await database[Collections.APPOINTMENTS].create_index("status")
        
        # Services collection indexes
        # service_id field removed - using MongoDB _id as unique identifier
        await database[Collections.SERVICES].create_index("name")
        
        # Professionals collection indexes
        # Temporarily disabled professional_id unique index to fix startup issues
        # await database[Collections.PROFESSIONALS].create_index("professional_id", unique=True)
        await database[Collections.PROFESSIONALS].create_index("email", unique=True)
        
        # Conversations collection indexes
        await database[Collections.CONVERSATIONS].create_index("user_id")
        await database[Collections.CONVERSATIONS].create_index("status")
        await database[Collections.CONVERSATIONS].create_index("created_at")
        
        # Appointment Links collection indexes
        await database[Collections.APPOINTMENT_LINKS].create_index("link_id", unique=True)
        await database[Collections.APPOINTMENT_LINKS].create_index("secure_token", unique=True)
        await database[Collections.APPOINTMENT_LINKS].create_index("appointment_id")
        await database[Collections.APPOINTMENT_LINKS].create_index("user_id")
        await database[Collections.APPOINTMENT_LINKS].create_index("expires_at")
        await database[Collections.APPOINTMENT_LINKS].create_index("status")
        
        # Surveys collection indexes
        await database[Collections.SURVEYS].create_index("survey_id", unique=True)
        await database[Collections.SURVEYS].create_index("appointment_id", unique=True)
        await database[Collections.SURVEYS].create_index("user_id")
        await database[Collections.SURVEYS].create_index("expires_at")
        
        # Survey Responses collection indexes
        await database[Collections.SURVEY_RESPONSES].create_index("response_id", unique=True)
        await database[Collections.SURVEY_RESPONSES].create_index("survey_id")
        await database[Collections.SURVEY_RESPONSES].create_index("submitted_at")
        
        # Security Events collection indexes
        await database[Collections.LINK_SECURITY_EVENTS].create_index("link_id")
        await database[Collections.LINK_SECURITY_EVENTS].create_index("event_type")
        await database[Collections.LINK_SECURITY_EVENTS].create_index("timestamp")
        
        logger.info("Database indexes initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize database indexes: {e}")
        raise