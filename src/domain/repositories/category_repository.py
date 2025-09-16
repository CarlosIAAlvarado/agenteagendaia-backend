from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.category import Category


class ICategoryRepository(ABC):
    
    @abstractmethod
    async def create(self, category: Category) -> Category:
        """Create a new category"""
        pass
    
    @abstractmethod
    async def get_by_id(self, category_id: str) -> Optional[Category]:
        """Get category by ID"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get all categories"""
        pass
    
    @abstractmethod
    async def get_active(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get all active categories"""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 50) -> List[Category]:
        """Search categories by name"""
        pass
    
    @abstractmethod
    async def update(self, category_id: str, category: Category) -> Optional[Category]:
        """Update category"""
        pass
    
    @abstractmethod
    async def delete(self, category_id: str) -> bool:
        """Delete category"""
        pass
    
    @abstractmethod
    async def activate(self, category_id: str) -> Optional[Category]:
        """Activate category"""
        pass
    
    @abstractmethod
    async def deactivate(self, category_id: str) -> Optional[Category]:
        """Deactivate category"""
        pass
    
    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """Check if category with given name exists"""
        pass