from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, AutoReconnect, NetworkTimeout
from typing import Optional
import logging
import asyncio
from .settings import get_settings

logger = logging.getLogger(__name__)

class MongoDatabase:
    client: Optional[AsyncIOMotorClient] = None
    database = None

mongo_db = MongoDatabase()

async def connect_to_mongo(retry_count: int = 3, retry_delay: int = 2):
    """Create database connection with retry logic"""
    settings = get_settings()

    for attempt in range(retry_count):
        try:
            logger.info(f"Attempting to connect to MongoDB (attempt {attempt + 1}/{retry_count})")

            mongo_db.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                maxPoolSize=20,  # Increased pool size
                minPoolSize=5,   # Increased minimum pool
                maxIdleTimeMS=60000,  # Increased idle time
                serverSelectionTimeoutMS=10000,  # Increased timeout
                connectTimeoutMS=20000,  # Connection timeout
                socketTimeoutMS=20000,   # Socket timeout
                retryWrites=True,  # Enable automatic retries for writes
                retryReads=True,   # Enable automatic retries for reads
            )

            # Test the connection
            await mongo_db.client.admin.command('ping')

            mongo_db.database = mongo_db.client[settings.database_name]

            logger.info("Successfully connected to MongoDB")

            # Create indexes
            await create_indexes()
            return

        except (ConnectionFailure, AutoReconnect, NetworkTimeout) as e:
            logger.error(f"Failed to connect to MongoDB (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Max retry attempts reached. Could not connect to MongoDB")
                raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise

async def close_mongo_connection():
    """Close database connection"""
    if mongo_db.client:
        mongo_db.client.close()
        logger.info("MongoDB connection closed")

async def get_database():
    """Get database instance with automatic reconnection"""
    if mongo_db.database is None:
        await connect_to_mongo()

    # Verify connection is still alive
    try:
        await mongo_db.client.admin.command('ping')
    except (ConnectionFailure, AutoReconnect, NetworkTimeout) as e:
        logger.warning(f"Lost connection to MongoDB, attempting to reconnect: {e}")
        await connect_to_mongo()
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        await connect_to_mongo()

    return mongo_db.database

async def create_indexes():
    """Create database indexes for optimal performance"""
    if mongo_db.database is None:
        return
    
    try:
        # Users collection indexes
        await mongo_db.database.users.create_index("email.value", unique=True)
        await mongo_db.database.users.create_index("phone.value", unique=True)
        await mongo_db.database.users.create_index("is_active")
        await mongo_db.database.users.create_index([("name", "text")])
        
        # Services collection indexes
        await mongo_db.database.services.create_index("name", unique=False)  # Cambiado a no único para permitir duplicados controlados por UX
        await mongo_db.database.services.create_index("is_active")
        await mongo_db.database.services.create_index("service_type")
        await mongo_db.database.services.create_index("service_mode")
        await mongo_db.database.services.create_index([("name", "text"), ("description", "text")])
        
        # Professionals collection indexes
        await mongo_db.database.professionals.create_index("email.value", unique=True)
        await mongo_db.database.professionals.create_index("phone.value", unique=True)
        await mongo_db.database.professionals.create_index("is_active")
        await mongo_db.database.professionals.create_index("service_ids")
        await mongo_db.database.professionals.create_index("specialization")
        await mongo_db.database.professionals.create_index([("name", "text"), ("specialization", "text")])
        
        # Appointments collection indexes
        await mongo_db.database.appointments.create_index("user_id")
        await mongo_db.database.appointments.create_index("professional_id")
        await mongo_db.database.appointments.create_index("service_id")
        await mongo_db.database.appointments.create_index("status")
        await mongo_db.database.appointments.create_index("time_slot.start_time")
        await mongo_db.database.appointments.create_index("time_slot.end_time")
        await mongo_db.database.appointments.create_index([("professional_id", 1), ("time_slot.start_time", 1)])
        await mongo_db.database.appointments.create_index([("professional_id", 1), ("status", 1)])
        await mongo_db.database.appointments.create_index([("user_id", 1), ("status", 1)])
        await mongo_db.database.appointments.create_index([("time_slot.start_time", 1), ("time_slot.end_time", 1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

async def ping_database():
    """Health check for database connection"""
    try:
        if mongo_db.client:
            await mongo_db.client.admin.command('ping')
            return True
        return False
    except Exception:
        return False