from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from ....domain.entities.company_config import CompanyConfig
from ....domain.repositories.company_config_repository import CompanyConfigRepository
from ....domain.value_objects.email import Email
from ....domain.value_objects.phone import Phone
from ..connection import get_database
import logging

logger = logging.getLogger(__name__)


class CompanyConfigRepositoryImpl(CompanyConfigRepository):
    """MongoDB implementation of CompanyConfigRepository"""

    def __init__(self):
        self.collection_name = "company_config"

    async def _get_collection(self):
        """Get MongoDB collection"""
        db = await get_database()
        return db[self.collection_name]

    async def get_current_config(self) -> Optional[CompanyConfig]:
        """Get current company configuration - get the most recently updated one"""
        try:
            collection = await self._get_collection()

            # 🏢 DEBUG: Count total configurations
            total_count = await collection.count_documents({})
            logger.info(f"🏢 DEBUG: Total company configurations in DB: {total_count}")

            # First try to get the most recently updated configuration
            doc = await collection.find_one(
                {"updated_at": {"$exists": True}},
                sort=[("updated_at", -1)]
            )

            # If no updated_at exists, fallback to most recent by created_at
            if not doc:
                doc = await collection.find_one({}, sort=[("created_at", -1)])

            if not doc:
                logger.info("🏢 DEBUG: No company configuration found")
                return None

            logger.info(f"🏢 DEBUG: Retrieved config ID: {doc['_id']}, updated_at: {doc.get('updated_at')}, company_name: {doc.get('company_name')}")
            return self._document_to_entity(doc)

        except Exception as e:
            logger.error(f"Error getting company config: {e}")
            return None

    async def create_config(self, config: CompanyConfig) -> CompanyConfig:
        """Create new company configuration"""
        try:
            collection = await self._get_collection()

            # 🧹 Clean up: Delete any existing configs (only one should exist)
            deleted_result = await collection.delete_many({})
            logger.info(f"🏢 DEBUG: Deleted {deleted_result.deleted_count} existing company configurations")

            doc = self._entity_to_document(config)
            result = await collection.insert_one(doc)

            config.id = str(result.inserted_id)
            logger.info(f"🏢 SUCCESS: Company config created with ID: {config.id}")

            return config

        except Exception as e:
            logger.error(f"Error creating company config: {e}")
            raise

    async def update_config(self, config: CompanyConfig) -> CompanyConfig:
        """Update existing company configuration"""
        try:
            collection = await self._get_collection()

            config.updated_at = datetime.utcnow()
            doc = self._entity_to_document(config)

            # Remove id from update document
            doc.pop('_id', None)

            # Convert string ID to ObjectId for MongoDB query
            object_id = ObjectId(config.id) if isinstance(config.id, str) else config.id

            logger.info(f"🏢 DEBUG: Updating config ID: {config.id} (ObjectId: {object_id}), company_name: {config.company_name}")

            result = await collection.update_one(
                {"_id": object_id},
                {"$set": doc}
            )

            if result.modified_count == 0:
                logger.warning(f"🏢 WARNING: No document was updated for ID: {config.id}")
            else:
                logger.info(f"🏢 SUCCESS: Company config updated successfully: {config.id}")

            return config

        except Exception as e:
            logger.error(f"Error updating company config: {e}")
            raise

    async def delete_config(self, config_id: str) -> bool:
        """Delete company configuration"""
        try:
            collection = await self._get_collection()
            result = await collection.delete_one({"_id": config_id})

            success = result.deleted_count > 0
            if success:
                logger.info(f"Company config deleted: {config_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting company config: {e}")
            return False

    async def config_exists(self) -> bool:
        """Check if any company configuration exists"""
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({})
            return count > 0

        except Exception as e:
            logger.error(f"Error checking company config existence: {e}")
            return False

    def _entity_to_document(self, config: CompanyConfig) -> dict:
        """Convert CompanyConfig entity to MongoDB document"""
        doc = {
            "company_name": config.company_name,
            "company_address": config.company_address,
            "company_phone": config.company_phone.value if config.company_phone else None,
            "company_email": config.company_email.value if config.company_email else None,
            "company_website": config.company_website,
            "company_logo_url": config.company_logo_url,
            "business_hours": config.business_hours,
            "timezone": config.timezone,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }

        if config.id:
            doc["_id"] = config.id

        return doc

    def _document_to_entity(self, doc: dict) -> CompanyConfig:
        """Convert MongoDB document to CompanyConfig entity"""
        # Handle optional phone
        phone = None
        if doc.get("company_phone"):
            try:
                phone = Phone(doc["company_phone"])
            except ValueError:
                logger.warning(f"Invalid phone format in company config: {doc.get('company_phone')}")

        # Handle optional email
        email = None
        if doc.get("company_email"):
            try:
                email = Email(doc["company_email"])
            except ValueError:
                logger.warning(f"Invalid email format in company config: {doc.get('company_email')}")

        return CompanyConfig(
            id=str(doc["_id"]),
            company_name=doc["company_name"],
            company_address=doc.get("company_address"),
            company_phone=phone,
            company_email=email,
            company_website=doc.get("company_website"),
            company_logo_url=doc.get("company_logo_url"),
            business_hours=doc.get("business_hours"),
            timezone=doc.get("timezone", "America/Bogota"),
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at")
        )