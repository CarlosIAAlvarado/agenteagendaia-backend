from datetime import datetime
import pytz
from typing import Optional
from ..config.settings import get_settings


def get_colombia_timezone():
    """Get Colombia timezone object"""
    return pytz.timezone('America/Bogota')


def get_utc_timezone():
    """Get UTC timezone object"""
    return pytz.utc


def get_default_timezone():
    """Get default timezone from settings"""
    settings = get_settings()
    return pytz.timezone(settings.default_timezone)


def utc_to_colombia(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to Colombia timezone
    
    Args:
        utc_dt: UTC datetime (timezone-aware or naive)
        
    Returns:
        datetime: Colombia timezone aware datetime
    """
    if utc_dt is None:
        return None
    
    colombia_tz = get_colombia_timezone()
    
    # If datetime is naive, assume it's UTC
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    
    return utc_dt.astimezone(colombia_tz)


def colombia_to_utc(colombia_dt: datetime) -> datetime:
    """Convert Colombia datetime to UTC
    
    Args:
        colombia_dt: Colombia timezone datetime (timezone-aware or naive)
        
    Returns:
        datetime: UTC timezone aware datetime
    """
    if colombia_dt is None:
        return None
    
    colombia_tz = get_colombia_timezone()
    
    # If datetime is naive, assume it's in Colombia timezone
    if colombia_dt.tzinfo is None:
        colombia_dt = colombia_tz.localize(colombia_dt)
    
    return colombia_dt.astimezone(pytz.utc)


def now_colombia() -> datetime:
    """Get current datetime in Colombia timezone
    
    Returns:
        datetime: Current Colombia timezone aware datetime
    """
    colombia_tz = get_colombia_timezone()
    return datetime.now(colombia_tz)


def now_utc() -> datetime:
    """Get current datetime in UTC
    
    Returns:
        datetime: Current UTC timezone aware datetime
    """
    return datetime.now(pytz.utc)


def utc_to_local(utc_dt: datetime, timezone_str: str = None) -> datetime:
    """Convert UTC datetime to local timezone
    
    Args:
        utc_dt: UTC datetime
        timezone_str: Target timezone string (defaults to Colombia)
        
    Returns:
        datetime: Local timezone aware datetime
    """
    if utc_dt is None:
        return None
    
    if timezone_str is None:
        settings = get_settings()
        timezone_str = settings.default_timezone
    
    local_tz = pytz.timezone(timezone_str)
    
    # If datetime is naive, assume it's UTC
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    
    return utc_dt.astimezone(local_tz)


def local_to_utc(local_dt: datetime, timezone_str: str = None) -> datetime:
    """Convert local datetime to UTC
    
    Args:
        local_dt: Local timezone datetime
        timezone_str: Source timezone string (defaults to Colombia)
        
    Returns:
        datetime: UTC timezone aware datetime
    """
    if local_dt is None:
        return None
    
    if timezone_str is None:
        settings = get_settings()
        timezone_str = settings.default_timezone
    
    local_tz = pytz.timezone(timezone_str)
    
    # If datetime is naive, assume it's in local timezone
    if local_dt.tzinfo is None:
        local_dt = local_tz.localize(local_dt)
    
    return local_dt.astimezone(pytz.utc)


def format_colombia_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime in Colombia timezone
    
    Args:
        dt: datetime to format (will be converted to Colombia timezone)
        format_str: Format string
        
    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        return ""
    
    colombia_dt = utc_to_colombia(dt) if dt.tzinfo is None or dt.tzinfo == pytz.utc else dt
    return colombia_dt.strftime(format_str)


def parse_colombia_datetime(datetime_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse datetime string as Colombia timezone
    
    Args:
        datetime_str: datetime string to parse
        format_str: Format string
        
    Returns:
        datetime: Colombia timezone aware datetime
    """
    if not datetime_str:
        return None
    
    colombia_tz = get_colombia_timezone()
    naive_dt = datetime.strptime(datetime_str, format_str)
    return colombia_tz.localize(naive_dt)