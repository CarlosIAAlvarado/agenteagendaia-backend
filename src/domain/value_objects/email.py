import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Email cannot be empty")
        
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip().lower()) is not None
    
    def __str__(self) -> str:
        return self.value.lower()
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Email):
            return False
        return self.value.lower() == other.value.lower()
    
    def __hash__(self) -> int:
        return hash(self.value.lower())
    
    @property
    def domain(self) -> str:
        """Get the domain part of the email"""
        return self.value.split('@')[1].lower()
    
    @property
    def username(self) -> str:
        """Get the username part of the email"""
        return self.value.split('@')[0].lower()