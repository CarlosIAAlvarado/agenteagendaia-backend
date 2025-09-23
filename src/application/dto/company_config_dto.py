from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class CompanyConfigCreateDTO(BaseModel):
    company_name: str
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_website: Optional[str] = None
    company_logo_url: Optional[str] = None
    business_hours: Optional[str] = None
    timezone: str = "America/Bogota"

    @validator('company_name')
    def validate_company_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        return v.strip()

    @validator('company_email')
    def validate_company_email(cls, v):
        if v and v.strip():
            if '@' not in v:
                raise ValueError('Invalid email format')
            return v.strip().lower()
        return None

    @validator('company_website')
    def validate_company_website(cls, v):
        if v and v.strip():
            website = v.strip()
            if not (website.startswith('http://') or website.startswith('https://')):
                website = 'https://' + website
            return website
        return None

    @validator('timezone')
    def validate_timezone(cls, v):
        if not v or not v.strip():
            raise ValueError('Timezone cannot be empty')
        return v.strip()


class CompanyConfigUpdateDTO(BaseModel):
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_website: Optional[str] = None
    company_logo_url: Optional[str] = None
    business_hours: Optional[str] = None
    timezone: Optional[str] = None

    @validator('company_name')
    def validate_company_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Company name cannot be empty')
        return v.strip() if v else v

    @validator('company_email')
    def validate_company_email(cls, v):
        if v is not None:
            if v.strip() and '@' not in v:
                raise ValueError('Invalid email format')
            return v.strip().lower() if v.strip() else None
        return v

    @validator('company_website')
    def validate_company_website(cls, v):
        if v is not None and v.strip():
            website = v.strip()
            if not (website.startswith('http://') or website.startswith('https://')):
                website = 'https://' + website
            return website
        return None if v is None else (None if not v.strip() else v.strip())

    @validator('timezone')
    def validate_timezone(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Timezone cannot be empty')
        return v.strip() if v else v


class CompanyConfigResponseDTO(BaseModel):
    id: str
    company_name: str
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_website: Optional[str] = None
    company_logo_url: Optional[str] = None
    business_hours: Optional[str] = None
    timezone: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyContactInfoDTO(BaseModel):
    """DTO for public company contact information"""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    business_hours: Optional[str] = None

    class Config:
        from_attributes = True