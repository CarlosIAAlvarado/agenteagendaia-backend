"""
Appointment Link Repository Interface
Defines the contract for appointment link persistence operations
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..entities.appointment_link import AppointmentLink, LinkAction, LinkStatus


class AppointmentLinkRepository(ABC):
    """Repository interface for appointment link persistence"""
    
    @abstractmethod
    async def create_link(self, link: AppointmentLink) -> AppointmentLink:
        """
        Create a new appointment link
        
        Args:
            link: AppointmentLink entity to create
            
        Returns:
            AppointmentLink: Created link entity
            
        Raises:
            RepositoryError: If link creation fails
        """
        pass
    
    @abstractmethod
    async def get_link_by_id(self, link_id: str) -> Optional[AppointmentLink]:
        """
        Get appointment link by ID
        
        Args:
            link_id: Unique link identifier
            
        Returns:
            AppointmentLink or None if not found
        """
        pass
    
    @abstractmethod
    async def get_link_by_token(self, secure_token: str) -> Optional[AppointmentLink]:
        """
        Get appointment link by secure token
        
        Args:
            secure_token: Secure token string
            
        Returns:
            AppointmentLink or None if not found
        """
        pass
    
    @abstractmethod
    async def get_links_by_appointment(
        self, 
        appointment_id: str,
        action: Optional[LinkAction] = None,
        status: Optional[LinkStatus] = None
    ) -> List[AppointmentLink]:
        """
        Get all links for a specific appointment
        
        Args:
            appointment_id: Appointment identifier
            action: Filter by action type (optional)
            status: Filter by status (optional)
            
        Returns:
            List of AppointmentLink entities
        """
        pass
    
    @abstractmethod
    async def get_links_by_user(
        self,
        user_id: str,
        action: Optional[LinkAction] = None,
        status: Optional[LinkStatus] = None,
        limit: int = 50
    ) -> List[AppointmentLink]:
        """
        Get all links for a specific user
        
        Args:
            user_id: User identifier
            action: Filter by action type (optional)
            status: Filter by status (optional)
            limit: Maximum number of results
            
        Returns:
            List of AppointmentLink entities
        """
        pass
    
    @abstractmethod
    async def update_link(self, link: AppointmentLink) -> AppointmentLink:
        """
        Update an existing appointment link
        
        Args:
            link: AppointmentLink entity with updated data
            
        Returns:
            AppointmentLink: Updated link entity
            
        Raises:
            RepositoryError: If link update fails
            EntityNotFound: If link doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete_link(self, link_id: str) -> bool:
        """
        Delete an appointment link
        
        Args:
            link_id: Link identifier to delete
            
        Returns:
            bool: True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def expire_old_links(self, before_date: Optional[datetime] = None) -> int:
        """
        Mark expired links as expired
        
        Args:
            before_date: Consider links expired before this date (default: now)
            
        Returns:
            int: Number of links marked as expired
        """
        pass
    
    @abstractmethod
    async def get_expired_links(
        self,
        limit: int = 100
    ) -> List[AppointmentLink]:
        """
        Get expired links for cleanup
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of expired AppointmentLink entities
        """
        pass
    
    @abstractmethod
    async def get_active_links_count(
        self,
        user_id: Optional[str] = None,
        action: Optional[LinkAction] = None
    ) -> int:
        """
        Get count of active links
        
        Args:
            user_id: Filter by user (optional)
            action: Filter by action type (optional)
            
        Returns:
            int: Count of active links
        """
        pass
    
    @abstractmethod
    async def get_link_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get analytics data for links in date range
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Dict with analytics data
        """
        pass
    
    @abstractmethod
    async def get_usage_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get link usage statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with usage statistics
        """
        pass
    
    @abstractmethod
    async def bulk_create_links(
        self,
        links: List[AppointmentLink]
    ) -> List[AppointmentLink]:
        """
        Create multiple appointment links in batch
        
        Args:
            links: List of AppointmentLink entities to create
            
        Returns:
            List of created AppointmentLink entities
        """
        pass
    
    @abstractmethod
    async def bulk_update_status(
        self,
        link_ids: List[str],
        new_status: LinkStatus
    ) -> int:
        """
        Update status for multiple links
        
        Args:
            link_ids: List of link IDs to update
            new_status: New status to set
            
        Returns:
            int: Number of links updated
        """
        pass
    
    @abstractmethod
    async def search_links(
        self,
        criteria: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search links with complex criteria
        
        Args:
            criteria: Search criteria dictionary
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Dict with results and pagination info
        """
        pass
    
    @abstractmethod
    async def get_security_events(
        self,
        link_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get security events for a specific link
        
        Args:
            link_id: Link identifier
            limit: Maximum number of results
            
        Returns:
            List of security event records
        """
        pass
    
    @abstractmethod
    async def log_security_event(
        self,
        link_id: str,
        event_type: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Log a security event for a link
        
        Args:
            link_id: Link identifier
            event_type: Type of security event
            details: Event details
            
        Returns:
            bool: True if logged successfully
        """
        pass