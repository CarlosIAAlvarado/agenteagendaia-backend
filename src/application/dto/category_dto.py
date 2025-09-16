from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class CategoryCreateDTO(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Category name")
    description: str = Field(..., min_length=5, max_length=500, description="Category description")
    color: str = Field("#3B82F6", pattern="^#[0-9A-Fa-f]{6}$", description="Hex color for category")
    icon: Optional[str] = Field(None, max_length=100, description="Icon name for category")
    
    @validator('name')
    def validate_name(cls, v):
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        return v.strip()


class CategoryUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Category name")
    description: Optional[str] = Field(None, min_length=5, max_length=500, description="Category description")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color for category")
    icon: Optional[str] = Field(None, max_length=100, description="Icon name for category")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            return v.strip()
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip()
        return v


class CategoryResponseDTO(BaseModel):
    id: str
    name: str
    description: str
    color: str
    icon: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    services_count: Optional[int] = 0  # Number of services in this category
    
    class Config:
        from_attributes = True


class CategoryListResponseDTO(BaseModel):
    categories: List[CategoryResponseDTO]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class CategoryFilterDTO(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    color: Optional[str] = None