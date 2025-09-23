from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class EmailConfigCreateDTO(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    email_from_name: str
    email_from_address: str
    email_enabled: bool = True
    use_tls: bool = True
    use_ssl: bool = False

    @validator('smtp_server')
    def validate_smtp_server(cls, v):
        if not v or not v.strip():
            raise ValueError('SMTP server cannot be empty')
        return v.strip()

    @validator('smtp_port')
    def validate_smtp_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError('SMTP port must be between 1 and 65535')
        return v

    @validator('smtp_username')
    def validate_smtp_username(cls, v):
        if not v or not v.strip():
            raise ValueError('SMTP username cannot be empty')
        return v.strip()

    @validator('smtp_password')
    def validate_smtp_password(cls, v):
        if not v or not v.strip():
            raise ValueError('SMTP password cannot be empty')
        return v

    @validator('email_from_name')
    def validate_email_from_name(cls, v):
        if not v or not v.strip():
            raise ValueError('From name cannot be empty')
        return v.strip()

    @validator('email_from_address')
    def validate_email_from_address(cls, v):
        if not v or not v.strip():
            raise ValueError('From email cannot be empty')
        # Basic email validation
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.strip().lower()


class EmailConfigUpdateDTO(BaseModel):
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    email_enabled: Optional[bool] = None
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None

    @validator('smtp_server')
    def validate_smtp_server(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('SMTP server cannot be empty')
        return v.strip() if v else v

    @validator('smtp_port')
    def validate_smtp_port(cls, v):
        if v is not None and not (1 <= v <= 65535):
            raise ValueError('SMTP port must be between 1 and 65535')
        return v

    @validator('email_from_address')
    def validate_email_from_address(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('From email cannot be empty')
            if '@' not in v:
                raise ValueError('Invalid email format')
            return v.strip().lower()
        return v


class EmailConfigResponseDTO(BaseModel):
    id: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str = "***hidden***"  # Never expose real password
    email_from_name: str
    email_from_address: str
    email_enabled: bool
    use_tls: bool
    use_ssl: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailTestDTO(BaseModel):
    to_email: str
    test_type: str = "connection"  # "connection" or "full_email"

    @validator('to_email')
    def validate_to_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Test email cannot be empty')
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.strip().lower()

    @validator('test_type')
    def validate_test_type(cls, v):
        if v not in ['connection', 'full_email']:
            raise ValueError('Test type must be "connection" or "full_email"')
        return v


class EmailTestResponseDTO(BaseModel):
    success: bool
    message: str
    test_type: str
    details: Optional[dict] = None