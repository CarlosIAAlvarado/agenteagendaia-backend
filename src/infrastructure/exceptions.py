"""
Infrastructure Exceptions
Custom exceptions for infrastructure layer
"""


class InfrastructureError(Exception):
    """Base exception for infrastructure layer"""
    pass


class RepositoryError(InfrastructureError):
    """Exception raised when repository operations fail"""
    pass


class EntityNotFound(RepositoryError):
    """Exception raised when an entity is not found in the repository"""
    pass


class DatabaseConnectionError(InfrastructureError):
    """Exception raised when database connection fails"""
    pass


class ExternalServiceError(InfrastructureError):
    """Exception raised when external service calls fail"""
    pass


class BusinessLogicError(Exception):
    """Exception raised when business logic validation fails"""
    pass


class ValidationError(Exception):
    """Exception raised when data validation fails"""
    pass


class AuthenticationError(Exception):
    """Exception raised when authentication fails"""
    pass


class AuthorizationError(Exception):
    """Exception raised when authorization fails"""
    pass


class ConfigurationError(InfrastructureError):
    """Exception raised when configuration is invalid"""
    pass


class AIServiceError(ExternalServiceError):
    """Exception raised when AI service calls fail"""
    pass


class VectorStoreError(InfrastructureError):
    """Exception raised when vector store operations fail"""
    pass