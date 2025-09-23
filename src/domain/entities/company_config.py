from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from ..value_objects.email import Email
from ..value_objects.phone import Phone


@dataclass
class CompanyConfig:
    """Company information configuration"""

    id: Optional[str]
    company_name: str
    company_address: Optional[str] = None
    company_phone: Optional[Phone] = None
    company_email: Optional[Email] = None
    company_website: Optional[str] = None
    company_logo_url: Optional[str] = None
    business_hours: Optional[str] = None
    timezone: str = "America/Bogota"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def update_company_info(
        self,
        company_name: Optional[str] = None,
        company_address: Optional[str] = None,
        company_phone: Optional[Phone] = None,
        company_email: Optional[Email] = None,
        company_website: Optional[str] = None,
        company_logo_url: Optional[str] = None,
        business_hours: Optional[str] = None,
        timezone: Optional[str] = None
    ):
        """Update company information"""
        if company_name is not None:
            if not company_name.strip():
                raise ValueError("Company name cannot be empty")
            self.company_name = company_name.strip()

        if company_address is not None:
            self.company_address = company_address.strip() if company_address.strip() else None

        if company_phone is not None:
            self.company_phone = company_phone

        if company_email is not None:
            self.company_email = company_email

        if company_website is not None:
            # Simple URL validation
            website = company_website.strip() if company_website else None
            if website and not (website.startswith('http://') or website.startswith('https://')):
                website = 'https://' + website
            self.company_website = website

        if company_logo_url is not None:
            self.company_logo_url = company_logo_url.strip() if company_logo_url.strip() else None

        if business_hours is not None:
            self.business_hours = business_hours.strip() if business_hours.strip() else None

        if timezone is not None:
            if not timezone.strip():
                raise ValueError("Timezone cannot be empty")
            self.timezone = timezone.strip()

        self.updated_at = datetime.utcnow()

    def get_display_name(self) -> str:
        """Get company display name"""
        return self.company_name

    def get_contact_info(self) -> dict:
        """Get formatted contact information"""
        return {
            "name": self.company_name,
            "address": self.company_address,
            "phone": self.company_phone.value if self.company_phone else None,
            "email": self.company_email.value if self.company_email else None,
            "website": self.company_website,
            "business_hours": self.business_hours
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "company_name": self.company_name,
            "company_address": self.company_address,
            "company_phone": self.company_phone.value if self.company_phone else None,
            "company_email": self.company_email.value if self.company_email else None,
            "company_website": self.company_website,
            "company_logo_url": self.company_logo_url,
            "business_hours": self.business_hours,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __str__(self):
        return f"CompanyConfig({self.company_name})"

    def __repr__(self):
        return self.__str__()