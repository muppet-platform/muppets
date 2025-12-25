"""
Custom exception classes for the Muppet Platform.

This module defines platform-specific exceptions with proper error codes,
messages, and structured error handling.
"""

from typing import Optional, Dict, Any


class PlatformException(Exception):
    """
    Base exception class for all platform-specific errors.

    Provides structured error information including error type,
    HTTP status code, and additional details.
    """

    def __init__(
        self,
        message: str,
        error_type: str = "PLATFORM_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}


class ValidationError(PlatformException):
    """Exception raised for input validation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class MuppetNotFoundError(PlatformException):
    """Exception raised when a requested muppet is not found."""

    def __init__(self, muppet_name: str):
        super().__init__(
            message=f"Muppet '{muppet_name}' not found",
            error_type="MUPPET_NOT_FOUND",
            status_code=404,
            details={"muppet_name": muppet_name},
        )


class MuppetAlreadyExistsError(PlatformException):
    """Exception raised when trying to create a muppet that already exists."""

    def __init__(self, muppet_name: str):
        super().__init__(
            message=f"Muppet '{muppet_name}' already exists",
            error_type="MUPPET_ALREADY_EXISTS",
            status_code=409,
            details={"muppet_name": muppet_name},
        )


class TemplateNotFoundError(PlatformException):
    """Exception raised when a requested template is not found."""

    def __init__(self, template_name: str):
        super().__init__(
            message=f"Template '{template_name}' not found",
            error_type="TEMPLATE_NOT_FOUND",
            status_code=404,
            details={"template_name": template_name},
        )


class InfrastructureError(PlatformException):
    """Exception raised for infrastructure provisioning errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="INFRASTRUCTURE_ERROR",
            status_code=500,
            details=details,
        )


class GitHubError(PlatformException):
    """Exception raised for GitHub API errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, error_type="GITHUB_ERROR", status_code=502, details=details
        )


class AWSError(PlatformException):
    """Exception raised for AWS service errors."""

    def __init__(
        self, message: str, service: str, details: Optional[Dict[str, Any]] = None
    ):
        error_details = {"aws_service": service}
        if details:
            error_details.update(details)

        super().__init__(
            message=message,
            error_type="AWS_ERROR",
            status_code=502,
            details=error_details,
        )


class ConfigurationError(PlatformException):
    """Exception raised for configuration errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )


class AuthenticationError(PlatformException):
    """Exception raised for authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message, error_type="AUTHENTICATION_ERROR", status_code=401
        )


class AuthorizationError(PlatformException):
    """Exception raised for authorization errors."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message, error_type="AUTHORIZATION_ERROR", status_code=403
        )


class DeploymentError(PlatformException):
    """Exception raised for deployment errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="DEPLOYMENT_ERROR",
            status_code=500,
            details=details,
        )
