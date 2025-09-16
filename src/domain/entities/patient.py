from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from ..value_objects.email import Email
from ..value_objects.phone import Phone


@dataclass
class Patient:
    id: Optional[str]
    name: str
    email: Email
    phone: Phone
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    preferences: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")
        
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def update_contact_info(self, name: Optional[str] = None, email: Optional[Email] = None, phone: Optional[Phone] = None):
        """Update patient contact information"""
        if name:
            if len(name.strip()) < 2:
                raise ValueError("Name must be at least 2 characters long")
            self.name = name.strip()
        
        if email:
            self.email = email
        
        if phone:
            self.phone = phone
        
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate patient record"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Activate patient record"""
        self.is_active = True
        self.updated_at = datetime.utcnow()