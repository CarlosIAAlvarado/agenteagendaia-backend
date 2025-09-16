"""
Appointment Link Domain Entity
Manages secure links for appointment rescheduling and cancellation
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class LinkAction(str, Enum):
    """Action types for appointment links"""
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    CONFIRM = "confirm"


class LinkStatus(str, Enum):
    """Status of a link"""
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    INVALID = "invalid"


@dataclass
class AppointmentLink:
    """
    Represents a secure link for appointment management actions
    """
    appointment_id: str
    user_id: str
    action: LinkAction
    expires_at: datetime
    link_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    secure_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    status: LinkStatus = LinkStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    used_at: Optional[datetime] = None
    usage_count: int = 0
    max_usage: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    custom_message: Optional[str] = None
    ip_restrictions: Optional[list] = None
    user_agent_restrictions: Optional[list] = None
    
    def __post_init__(self):
        """Validate entity after initialization"""
        if self.expires_at <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")
        
        if not self.appointment_id or not self.user_id:
            raise ValueError("Appointment ID and User ID are required")
    
    @classmethod
    def create_reschedule_link(
        cls,
        appointment_id: str,
        user_id: str,
        expires_in_hours: int = 48,
        custom_message: Optional[str] = None
    ) -> 'AppointmentLink':
        """Create a new reschedule link"""
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        return cls(
            appointment_id=appointment_id,
            user_id=user_id,
            action=LinkAction.RESCHEDULE,
            expires_at=expires_at,
            custom_message=custom_message,
            max_usage=3  # Allow up to 3 reschedule attempts
        )
    
    @classmethod
    def create_cancel_link(
        cls,
        appointment_id: str,
        user_id: str,
        expires_in_hours: int = 48,
        custom_message: Optional[str] = None
    ) -> 'AppointmentLink':
        """Create a new cancellation link"""
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        return cls(
            appointment_id=appointment_id,
            user_id=user_id,
            action=LinkAction.CANCEL,
            expires_at=expires_at,
            custom_message=custom_message,
            max_usage=1  # Single use for cancellation
        )
    
    @classmethod
    def create_confirm_link(
        cls,
        appointment_id: str,
        user_id: str,
        expires_in_hours: int = 24,
        custom_message: Optional[str] = None
    ) -> 'AppointmentLink':
        """Create a new confirmation link"""
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        return cls(
            appointment_id=appointment_id,
            user_id=user_id,
            action=LinkAction.CONFIRM,
            expires_at=expires_at,
            custom_message=custom_message,
            max_usage=1  # Single use for confirmation
        )
    
    def is_valid(self) -> bool:
        """Check if link is still valid"""
        now = datetime.utcnow()
        
        # Check expiration
        if now >= self.expires_at:
            self.status = LinkStatus.EXPIRED
            return False
        
        # Check usage limit
        if self.usage_count >= self.max_usage:
            self.status = LinkStatus.USED
            return False
        
        # Check status
        if self.status != LinkStatus.ACTIVE:
            return False
        
        return True
    
    def is_expired(self) -> bool:
        """Check if link has expired"""
        return datetime.utcnow() >= self.expires_at
    
    def is_used(self) -> bool:
        """Check if link has been used up"""
        return self.usage_count >= self.max_usage
    
    def use_link(self) -> bool:
        """Mark link as used and increment usage count"""
        if not self.is_valid():
            return False
        
        self.usage_count += 1
        self.used_at = datetime.utcnow()
        
        if self.usage_count >= self.max_usage:
            self.status = LinkStatus.USED
        
        return True
    
    def revoke(self) -> None:
        """Revoke the link, making it invalid"""
        self.status = LinkStatus.INVALID
    
    def extend_expiration(self, hours: int) -> None:
        """Extend link expiration by specified hours"""
        if hours > 0 and self.is_valid():
            self.expires_at += timedelta(hours=hours)
    
    def add_ip_restriction(self, ip_address: str) -> None:
        """Add IP address restriction"""
        if self.ip_restrictions is None:
            self.ip_restrictions = []
        
        if ip_address not in self.ip_restrictions:
            self.ip_restrictions.append(ip_address)
    
    def check_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP address is allowed"""
        if self.ip_restrictions is None:
            return True
        
        return ip_address in self.ip_restrictions
    
    def add_user_agent_restriction(self, user_agent: str) -> None:
        """Add user agent restriction"""
        if self.user_agent_restrictions is None:
            self.user_agent_restrictions = []
        
        if user_agent not in self.user_agent_restrictions:
            self.user_agent_restrictions.append(user_agent)
    
    def check_user_agent_allowed(self, user_agent: str) -> bool:
        """Check if user agent is allowed"""
        if self.user_agent_restrictions is None:
            return True
        
        return any(allowed in user_agent for allowed in self.user_agent_restrictions)
    
    def get_full_url(self, base_url: str) -> str:
        """Generate the full URL for this link"""
        return f"{base_url}/appointment-link/{self.action.value}/{self.secure_token}"
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the link"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            "link_id": self.link_id,
            "appointment_id": self.appointment_id,
            "user_id": self.user_id,
            "action": self.action.value,
            "secure_token": self.secure_token,
            "status": self.status.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "used_at": self.used_at,
            "usage_count": self.usage_count,
            "max_usage": self.max_usage,
            "metadata": self.metadata,
            "custom_message": self.custom_message,
            "ip_restrictions": self.ip_restrictions,
            "user_agent_restrictions": self.user_agent_restrictions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppointmentLink':
        """Create entity from dictionary"""
        return cls(
            link_id=data["link_id"],
            appointment_id=data["appointment_id"],
            user_id=data["user_id"],
            action=LinkAction(data["action"]),
            secure_token=data["secure_token"],
            status=LinkStatus(data["status"]),
            created_at=data["created_at"],
            expires_at=data["expires_at"],
            used_at=data.get("used_at"),
            usage_count=data.get("usage_count", 0),
            max_usage=data.get("max_usage", 1),
            metadata=data.get("metadata", {}),
            custom_message=data.get("custom_message"),
            ip_restrictions=data.get("ip_restrictions"),
            user_agent_restrictions=data.get("user_agent_restrictions")
        )
    
    def __str__(self) -> str:
        return f"AppointmentLink(id={self.link_id}, action={self.action.value}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return self.__str__()