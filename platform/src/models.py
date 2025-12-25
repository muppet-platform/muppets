"""
Data models for the Muppet Platform.

This module defines the core data structures used throughout the platform
for representing muppets, state, and configuration.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MuppetStatus(Enum):
    """Enumeration of possible muppet states."""

    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    DELETING = "deleting"


@dataclass
class Muppet:
    """
    Core muppet data model.

    Represents a muppet instance with all its metadata and state information.
    """

    name: str
    template: str
    status: MuppetStatus
    github_repo_url: str
    fargate_service_arn: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    terraform_version: str = "1.6.0"  # OpenTofu version
    port: int = 3000

    def to_dict(self) -> Dict[str, Any]:
        """Convert muppet to dictionary representation."""
        data = asdict(self)
        # Convert enum to string
        data["status"] = self.status.value
        # Convert datetime objects to ISO strings
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_github_repo(cls, repo_data: Dict[str, Any]) -> "Muppet":
        """
        Reconstruct muppet state from GitHub repository metadata.

        Args:
            repo_data: GitHub repository data from API

        Returns:
            Muppet instance reconstructed from repository metadata
        """
        # Extract muppet metadata from repository topics and description
        topics = repo_data.get("topics", [])
        description = repo_data.get("description", "")

        # Parse template from topics (e.g., 'template:java-micronaut')
        template = "unknown"
        for topic in topics:
            if topic.startswith("template:"):
                template = topic.replace("template:", "")
                break

        # Parse status from topics (e.g., 'status-running')
        status = MuppetStatus.RUNNING  # Default status
        for topic in topics:
            if topic.startswith("status-"):
                status_str = topic.replace("status-", "")
                try:
                    status = MuppetStatus(status_str)
                except ValueError:
                    status = MuppetStatus.ERROR
                break

        return cls(
            name=repo_data["name"],
            template=template,
            status=status,
            github_repo_url=repo_data["html_url"],
            created_at=datetime.fromisoformat(
                repo_data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                repo_data["updated_at"].replace("Z", "+00:00")
            ),
        )


@dataclass
class PlatformState:
    """
    Complete platform state aggregated from multiple sources.

    This represents the current state of all muppets and platform configuration
    reconstructed from GitHub, Parameter Store, and ECS.
    """

    muppets: List[Muppet]
    active_deployments: Dict[str, str]  # muppet_name -> fargate_arn
    terraform_versions: Dict[str, str]  # module_name -> version
    last_updated: datetime

    @classmethod
    def empty(cls) -> "PlatformState":
        """Create an empty platform state."""
        return cls(
            muppets=[],
            active_deployments={},
            terraform_versions={},
            last_updated=datetime.utcnow(),
        )

    def get_muppet(self, name: str) -> Optional[Muppet]:
        """Get a muppet by name."""
        for muppet in self.muppets:
            if muppet.name == name:
                return muppet
        return None

    def add_muppet(self, muppet: Muppet) -> None:
        """Add or update a muppet in the state."""
        # Remove existing muppet with same name
        self.muppets = [m for m in self.muppets if m.name != muppet.name]
        # Add the new/updated muppet
        self.muppets.append(muppet)
        self.last_updated = datetime.utcnow()

    def remove_muppet(self, name: str) -> bool:
        """Remove a muppet from the state."""
        original_count = len(self.muppets)
        self.muppets = [m for m in self.muppets if m.name != name]

        # Also remove from active deployments
        if name in self.active_deployments:
            del self.active_deployments[name]

        self.last_updated = datetime.utcnow()
        return len(self.muppets) < original_count


@dataclass
class Template:
    """
    Template metadata model.

    Represents a muppet template with its configuration and capabilities.
    """

    name: str
    version: str
    description: str
    language: str
    framework: str
    terraform_modules: List[str]
    required_variables: List[str]
    supported_features: List[str]
    port: int = 3000
    metadata: Dict[str, Any] = None
    template_files: List[str] = None

    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.metadata is None:
            self.metadata = {}
        if self.template_files is None:
            self.template_files = []

    def validate(self) -> bool:
        """Validate template configuration."""
        # Basic validation - ensure required fields are present
        return (
            bool(self.name)
            and bool(self.version)
            and bool(self.language)
            and bool(self.framework)
            and isinstance(self.terraform_modules, list)
            and isinstance(self.required_variables, list)
            and isinstance(self.supported_features, list)
        )

    @classmethod
    def discover_templates(cls) -> List["Template"]:
        """
        Discover all available templates.

        This method now delegates to the TemplateManager for actual discovery.
        This is kept for backward compatibility.
        """
        # Import here to avoid circular imports
        from .managers.template_manager import TemplateManager

        template_manager = TemplateManager()
        return template_manager.discover_templates()


@dataclass
class InfrastructureConfig:
    """
    Infrastructure configuration model.

    Represents the infrastructure configuration for a muppet deployment.
    """

    muppet_name: str
    template_name: str
    terraform_module_versions: Dict[str, str]
    aws_region: str
    fargate_cluster: str
    vpc_config: Dict[str, Any]
    monitoring_config: Dict[str, Any]
