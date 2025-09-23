from abc import ABC, abstractmethod
from typing import Optional
from ..entities.email_config import EmailConfig


class EmailConfigRepository(ABC):
    """Abstract repository for email configuration"""

    @abstractmethod
    async def get_current_config(self) -> Optional[EmailConfig]:
        """Get current email configuration"""
        pass

    @abstractmethod
    async def create_config(self, config: EmailConfig) -> EmailConfig:
        """Create new email configuration"""
        pass

    @abstractmethod
    async def update_config(self, config: EmailConfig) -> EmailConfig:
        """Update existing email configuration"""
        pass

    @abstractmethod
    async def delete_config(self, config_id: str) -> bool:
        """Delete email configuration"""
        pass

    @abstractmethod
    async def config_exists(self) -> bool:
        """Check if any email configuration exists"""
        pass