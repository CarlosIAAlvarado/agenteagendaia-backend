from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from ..value_objects.email import Email


@dataclass
class EmailConfig:
    """Configuration for email sending"""

    id: Optional[str]
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str  # Should be encrypted in production
    email_from_name: str
    email_from_address: Email
    email_enabled: bool = True
    use_tls: bool = True
    use_ssl: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def update_config(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        email_from_name: Optional[str] = None,
        email_from_address: Optional[Email] = None,
        email_enabled: Optional[bool] = None,
        use_tls: Optional[bool] = None,
        use_ssl: Optional[bool] = None
    ):
        """Update email configuration"""
        if smtp_server is not None:
            if not smtp_server.strip():
                raise ValueError("SMTP server cannot be empty")
            self.smtp_server = smtp_server.strip()

        if smtp_port is not None:
            if not (1 <= smtp_port <= 65535):
                raise ValueError("SMTP port must be between 1 and 65535")
            self.smtp_port = smtp_port

        if smtp_username is not None:
            if not smtp_username.strip():
                raise ValueError("SMTP username cannot be empty")
            self.smtp_username = smtp_username.strip()

        if smtp_password is not None:
            if not smtp_password.strip():
                raise ValueError("SMTP password cannot be empty")
            self.smtp_password = smtp_password

        if email_from_name is not None:
            if not email_from_name.strip():
                raise ValueError("From name cannot be empty")
            self.email_from_name = email_from_name.strip()

        if email_from_address is not None:
            self.email_from_address = email_from_address

        if email_enabled is not None:
            self.email_enabled = email_enabled

        if use_tls is not None:
            self.use_tls = use_tls

        if use_ssl is not None:
            self.use_ssl = use_ssl

        self.updated_at = datetime.utcnow()

    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return (
            bool(self.smtp_server.strip()) and
            1 <= self.smtp_port <= 65535 and
            bool(self.smtp_username.strip()) and
            bool(self.smtp_password.strip()) and
            bool(self.email_from_name.strip()) and
            self.email_from_address is not None
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "smtp_username": self.smtp_username,
            "smtp_password": "***hidden***",  # Never expose password
            "email_from_name": self.email_from_name,
            "email_from_address": self.email_from_address.value,
            "email_enabled": self.email_enabled,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __str__(self):
        return f"EmailConfig({self.email_from_address.value}, enabled={self.email_enabled})"

    def __repr__(self):
        return self.__str__()