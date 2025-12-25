"""
Configuration management for the Muppet Platform using Pydantic.

This module defines all configuration settings with proper validation,
environment variable support, and default values.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AWSConfig(BaseSettings):
    """AWS-specific configuration settings."""

    model_config = {"env_prefix": "AWS_"}

    region: str = Field(default="us-west-2", description="AWS region")
    fargate_cluster_name: str = Field(
        default="muppet-platform-cluster", description="ECS Fargate cluster name"
    )
    capacity_providers: List[str] = Field(
        default=["FARGATE", "FARGATE_SPOT"], description="ECS capacity providers"
    )
    vpc_cidr: str = Field(default="10.0.0.0/16", description="VPC CIDR block")
    availability_zones: List[str] = Field(
        default=["us-west-2a", "us-west-2b"], description="Availability zones"
    )


class GitHubConfig(BaseSettings):
    """GitHub-specific configuration settings."""

    model_config = {"env_prefix": "GITHUB_"}

    organization: str = Field(
        default="muppet-platform", description="GitHub organization name"
    )
    token: Optional[str] = Field(default=None, description="GitHub API token")
    visibility: str = Field(default="private", description="Repository visibility")
    branch_protection: bool = Field(
        default=True, description="Enable branch protection"
    )
    required_reviews: int = Field(default=1, description="Required reviews for PRs")
    dismiss_stale_reviews: bool = Field(
        default=True, description="Dismiss stale reviews"
    )

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v):
        if v not in ["public", "private", "internal"]:
            raise ValueError("visibility must be public, private, or internal")
        return v


class MonitoringConfig(BaseSettings):
    """Monitoring and logging configuration settings."""

    model_config = {"env_prefix": "MONITORING_"}

    cloudwatch_log_retention_days: int = Field(
        default=7, description="CloudWatch log retention in days"
    )
    cloudwatch_metrics_enabled: bool = Field(
        default=True, description="Enable CloudWatch metrics"
    )
    cloudwatch_alarms_enabled: bool = Field(
        default=True, description="Enable CloudWatch alarms"
    )
    xray_enabled: bool = Field(default=False, description="Enable AWS X-Ray tracing")
    xray_sampling_rate: float = Field(default=0.1, description="X-Ray sampling rate")

    @field_validator("xray_sampling_rate")
    @classmethod
    def validate_sampling_rate(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("xray_sampling_rate must be between 0.0 and 1.0")
        return v


class MCPConfig(BaseSettings):
    """MCP server configuration settings."""

    model_config = {"env_prefix": "MCP_"}

    name: str = Field(default="mcp-server", description="MCP server name")
    port: int = Field(default=8001, description="MCP server port")
    protocol: str = Field(default="stdio", description="MCP protocol")

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v):
        if v not in ["stdio", "http", "websocket"]:
            raise ValueError("protocol must be stdio, http, or websocket")
        return v


class Settings(BaseSettings):
    """Main application settings."""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    # Application settings
    name: str = Field(default="platform-service", description="Service name")
    version: str = Field(default="0.1.0", description="Service version")
    host: str = Field(default="0.0.0.0", description="HTTP server host")  # nosec B104
    port: int = Field(default=8000, description="HTTP server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Allowed CORS origins",
    )

    # Integration mode settings
    integration_mode: str = Field(
        default="mock",
        description="Integration mode: 'mock' for testing, 'real' for production",
    )
    aws_endpoint_url: Optional[str] = Field(
        default=None, description="Custom AWS endpoint URL (for LocalStack)"
    )

    @field_validator("integration_mode")
    @classmethod
    def validate_integration_mode(cls, v):
        valid_modes = ["mock", "local", "real"]
        if v not in valid_modes:
            raise ValueError(f"integration_mode must be one of {valid_modes}")
        return v

    # Component configurations
    aws: AWSConfig = Field(default_factory=AWSConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
