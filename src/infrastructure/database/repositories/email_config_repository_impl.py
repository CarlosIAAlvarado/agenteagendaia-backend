from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from ....domain.entities.email_config import EmailConfig
from ....domain.repositories.email_config_repository import EmailConfigRepository
from ....domain.value_objects.email import Email
from ..connection import get_database
import logging

logger = logging.getLogger(__name__)


class EmailConfigRepositoryImpl(EmailConfigRepository):
    """MongoDB implementation of EmailConfigRepository"""

    def __init__(self):
        self.collection_name = "email_config"

    async def _get_collection(self):
        """Get MongoDB collection"""
        db = await get_database()
        return db[self.collection_name]

    async def get_current_config(self) -> Optional[EmailConfig]:
        """Get current email configuration - get the most recently updated one"""
        try:
            collection = await self._get_collection()

            # 🔍 DEBUG: Count total configurations
            total_count = await collection.count_documents({})
            logger.info(f"📧 DEBUG: Total email configurations in DB: {total_count}")

            # First try to get the most recently updated configuration
            doc = await collection.find_one(
                {"updated_at": {"$exists": True}},
                sort=[("updated_at", -1)]
            )

            # If no updated_at exists, fallback to most recent by created_at
            if not doc:
                doc = await collection.find_one({}, sort=[("created_at", -1)])

            if not doc:
                logger.info("📧 DEBUG: No email configuration found")
                return None

            logger.info(f"📧 DEBUG: Retrieved config ID: {doc['_id']}, updated_at: {doc.get('updated_at')}, smtp_port: {doc.get('smtp_port')}")
            return self._document_to_entity(doc)

        except Exception as e:
            logger.error(f"Error getting email config: {e}")
            return None

    async def create_config(self, config: EmailConfig) -> EmailConfig:
        """Create new email configuration"""
        try:
            collection = await self._get_collection()

            # 🧹 Clean up: Delete any existing configs (only one should exist)
            deleted_result = await collection.delete_many({})
            logger.info(f"📧 DEBUG: Deleted {deleted_result.deleted_count} existing email configurations")

            doc = self._entity_to_document(config)
            result = await collection.insert_one(doc)

            config.id = str(result.inserted_id)
            logger.info(f"📧 SUCCESS: Email config created with ID: {config.id}")

            return config

        except Exception as e:
            logger.error(f"Error creating email config: {e}")
            raise

    async def update_config(self, config: EmailConfig) -> EmailConfig:
        """Update existing email configuration"""
        try:
            collection = await self._get_collection()

            config.updated_at = datetime.utcnow()
            doc = self._entity_to_document(config)

            # Remove id from update document
            doc.pop('_id', None)

            # Convert string ID to ObjectId for MongoDB query
            object_id = ObjectId(config.id) if isinstance(config.id, str) else config.id

            logger.info(f"📧 DEBUG: Updating config ID: {config.id} (ObjectId: {object_id}), smtp_port: {config.smtp_port}")

            result = await collection.update_one(
                {"_id": object_id},
                {"$set": doc}
            )

            if result.modified_count == 0:
                logger.warning(f"📧 WARNING: No document was updated for ID: {config.id}")
            else:
                logger.info(f"📧 SUCCESS: Email config updated successfully: {config.id}")

            return config

        except Exception as e:
            logger.error(f"Error updating email config: {e}")
            raise

    async def delete_config(self, config_id: str) -> bool:
        """Delete email configuration"""
        try:
            collection = await self._get_collection()
            result = await collection.delete_one({"_id": config_id})

            success = result.deleted_count > 0
            if success:
                logger.info(f"Email config deleted: {config_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting email config: {e}")
            return False

    async def config_exists(self) -> bool:
        """Check if any email configuration exists"""
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({})
            return count > 0

        except Exception as e:
            logger.error(f"Error checking email config existence: {e}")
            return False

    def _entity_to_document(self, config: EmailConfig) -> dict:
        """Convert EmailConfig entity to MongoDB document"""
        doc = {
            "smtp_server": config.smtp_server,
            "smtp_port": config.smtp_port,
            "smtp_username": config.smtp_username,
            "smtp_password": config.smtp_password,  # Note: In production, this should be encrypted
            "email_from_name": config.email_from_name,
            "email_from_address": config.email_from_address.value,
            "email_enabled": config.email_enabled,
            "use_tls": config.use_tls,
            "use_ssl": config.use_ssl,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }

        if config.id:
            doc["_id"] = config.id

        return doc

    def _document_to_entity(self, doc: dict) -> EmailConfig:
        """Convert MongoDB document to EmailConfig entity"""
        return EmailConfig(
            id=str(doc["_id"]),
            smtp_server=doc["smtp_server"],
            smtp_port=doc["smtp_port"],
            smtp_username=doc["smtp_username"],
            smtp_password=doc["smtp_password"],
            email_from_name=doc["email_from_name"],
            email_from_address=Email(doc["email_from_address"]),
            email_enabled=doc.get("email_enabled", True),
            use_tls=doc.get("use_tls", True),
            use_ssl=doc.get("use_ssl", False),
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at")
        )