import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Phone:
    value: str
    country_code: str = "+57"  # Colombia default
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Phone number cannot be empty")
        
        cleaned_phone = self._clean_phone_number(self.value)
        
        if not self._is_valid_phone(cleaned_phone):
            raise ValueError(f"Invalid phone number format: {self.value}")
        
        # Update the value with cleaned version
        object.__setattr__(self, 'value', cleaned_phone)
    
    def _clean_phone_number(self, phone: str) -> str:
        """Remove all non-numeric characters except +"""
        # Remove all non-numeric characters except +
        cleaned = re.sub(r'[^\d+]', '', phone.strip())
        
        # If it starts with +, keep it
        if cleaned.startswith('+'):
            return cleaned
        
        # If it's a Colombian number without country code (10 digits starting with 3)
        if len(cleaned) == 10 and cleaned.startswith('3'):
            return f"{self.country_code}{cleaned}"
        
        # If it's a Colombian number without country code (other lengths)
        if 7 <= len(cleaned) <= 10:
            # For shorter numbers, just add country code
            return f"{self.country_code}{cleaned}"
        
        return cleaned
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Colombian mobile numbers: +57 3XX XXX XXXX (most common)
        colombian_mobile = r'^\+57[3][0-9]{9}$'
        
        # Colombian landline or other numbers: +57 XXXXXXX (7-10 digits)
        colombian_general = r'^\+57[0-9]{7,10}$'
        
        # General international format: +XX XXXXXXXXX (8-15 digits after country code)
        international = r'^\+[1-9]\d{1,3}\d{8,15}$'
        
        return bool(
            re.match(colombian_mobile, phone) or 
            re.match(colombian_general, phone) or 
            re.match(international, phone)
        )
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Phone):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    @property
    def formatted(self) -> str:
        """Return formatted phone number for display"""
        if self.value.startswith('+57'):
            # Colombian format: +57 3XX XXX XXXX
            number = self.value[3:]  # Remove +57
            return f"+57 {number[:3]} {number[3:6]} {number[6:]}"
        
        # International format
        return self.value
    
    @property
    def national_format(self) -> str:
        """Return national format (without country code)"""
        if self.value.startswith('+57'):
            return self.value[3:]  # Remove +57
        return self.value.lstrip('+').lstrip(self.country_code.lstrip('+'))