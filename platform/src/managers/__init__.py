"""
Manager modules for the Muppet Platform.

This package contains high-level manager classes that orchestrate
complex operations across multiple components.
"""

from .github_manager import GitHubManager
from .infrastructure_manager import InfrastructureManager
from .steering_manager import SteeringManager
from .template_manager import TemplateManager

__all__ = [
    "GitHubManager",
    "TemplateManager",
    "InfrastructureManager",
    "SteeringManager",
]
