from abc import ABC, abstractmethod
from typing import Optional
from ..entities.company_config import CompanyConfig


class CompanyConfigRepository(ABC):
    """Abstract repository for company configuration"""

    @abstractmethod
    async def get_current_config(self) -> Optional[CompanyConfig]:
        """Get current company configuration"""
        pass

    @abstractmethod
    async def create_config(self, config: CompanyConfig) -> CompanyConfig:
        """Create new company configuration"""
        pass

    @abstractmethod
    async def update_config(self, config: CompanyConfig) -> CompanyConfig:
        """Update existing company configuration"""
        pass

    @abstractmethod
    async def delete_config(self, config_id: str) -> bool:
        """Delete company configuration"""
        pass

    @abstractmethod
    async def config_exists(self) -> bool:
        """Check if any company configuration exists"""
        pass