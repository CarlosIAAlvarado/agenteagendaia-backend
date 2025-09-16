from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Category:
    id: Optional[str]
    name: str
    description: str
    color: str = "#3B82F6"  # Default blue color
    icon: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Category name must be at least 2 characters long")
        
        if not self.description or len(self.description.strip()) < 5:
            raise ValueError("Category description must be at least 5 characters long")
        
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def update_category(self, name: Optional[str] = None, description: Optional[str] = None, 
                       color: Optional[str] = None, icon: Optional[str] = None):
        """Update category information"""
        if name:
            if len(name.strip()) < 2:
                raise ValueError("Category name must be at least 2 characters long")
            self.name = name.strip()
        
        if description:
            if len(description.strip()) < 5:
                raise ValueError("Category description must be at least 5 characters long")
            self.description = description.strip()
        
        if color:
            self.color = color
        
        if icon is not None:
            self.icon = icon
        
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Activate category"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate category"""
        self.is_active = False
        self.updated_at = datetime.utcnow()