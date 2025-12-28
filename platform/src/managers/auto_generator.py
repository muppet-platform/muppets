"""
Auto-Generator Component for Simplified Template System

This module automatically generates infrastructure, CI/CD, and Kiro configurations
for templates, allowing template developers to focus only on application code and tests.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import get_settings
from ..exceptions import PlatformException
from ..logging_config import get_logger

logger = get_logger(__name__)


class AutoGenerationError(PlatformException):
    """Raised when auto-generation fails."""


@dataclass
class TemplateMetadata:
    """Simplified template metadata focusing on application concerns."""

    name: str
    version: str
    description: str
    language: str
    framework: str
    port: int = 3000

    # Application-specific metadata
    java_version: Optional[str] = None
    java_distribution: Optional[str] = None
    framework_version: Optional[str] = None
    build_tool: Optional[str] = None

    # Features that affect generation
    features: List[str] = field(default_factory=list)

    def __post_init__(self):
        # No need to check features since it's initialized with default_factory
        pass


@dataclass
class GenerationConfig:
    """Configuration for auto-generation."""

    # Infrastructure generation
    generate_infrastructure: bool = True
    infrastructure_modules: List[str] = field(default_factory=list)

    # CI/CD generation
    generate_cicd: bool = True
    cicd_features: List[str] = field(default_factory=list)

    # Kiro generation
    generate_kiro: bool = True
    kiro_features: List[str] = field(default_factory=list)

    # TLS configuration
    enable_tls: bool = True

    def __post_init__(self):
        if self.infrastructure_modules is None:
            self.infrastructure_modules = [
                "fargate-service",
                "monitoring",
                "networking",
                "ecr",
            ]
        if self.cicd_features is None:
            self.cicd_features = ["build", "test", "security", "deploy"]
        if self.kiro_features is None:
            self.kiro_features = ["language-server", "debugging", "steering"]


class AutoGenerator:
    """
    Automatically generates infrastructure, CI/CD, and Kiro configurations
    for simplified templates.
    """

    def __init__(self):
        self.settings = get_settings()
        logger.info("Auto-generator initialized with simplified template processing")

    def generate_infrastructure(
        self,
        template_metadata: TemplateMetadata,
        muppet_name: str,
        output_path: Path,
        config: GenerationConfig,
    ) -> None:
        """
        Generate infrastructure using simplified template approach.
        Infrastructure templates are now processed directly by TemplateManager.

        Args:
            template_metadata: Template metadata
            muppet_name: Name of the muppet
            output_path: Output directory path
            config: Generation configuration
        """
        if not config.generate_infrastructure:
            return

        logger.info(
            f"Infrastructure generation for {template_metadata.name} handled by TemplateManager"
        )

        # Generate Dockerfile for Java applications with Java 21 LTS
        if template_metadata.language == "java":
            dockerfile_content = self._generate_java_dockerfile(template_metadata)
            (output_path / "Dockerfile").write_text(dockerfile_content)

        logger.info("Infrastructure generation completed")

    def generate_cicd(
        self,
        template_metadata: TemplateMetadata,
        muppet_name: str,
        output_path: Path,
        config: GenerationConfig,
    ) -> None:
        """
        Generate CI/CD workflow configurations using template files.

        Args:
            template_metadata: Template metadata
            muppet_name: Name of the muppet
            output_path: Output directory path
            config: Generation configuration
        """
        if not config.generate_cicd:
            print(f"🔍 DEBUG: CI/CD generation disabled for {template_metadata.name}")
            return

        print(f"🔍 DEBUG: Starting CI/CD generation for {template_metadata.name}")
        logger.info(f"Generating CI/CD workflows for {template_metadata.name} template")

        # Template files should already be processed by the main template processing
        # This method is now just for validation and logging
        workflows_dir = output_path / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml"))
            logger.info(
                f"Found {len(workflow_files)} workflow files: {[f.name for f in workflow_files]}"
            )
            print(
                f"🔍 DEBUG: Found {len(workflow_files)} workflow files: {[f.name for f in workflow_files]}"
            )
        else:
            logger.warning(
                "No workflows directory found - workflows may not have been processed"
            )
            print("🔍 DEBUG: No workflows directory found")

        logger.info("CI/CD generation completed")
        print(f"🔍 DEBUG: CI/CD generation completed for {template_metadata.name}")

    def generate_kiro_config(
        self,
        template_metadata: TemplateMetadata,
        muppet_name: str,
        output_path: Path,
        config: GenerationConfig,
    ) -> None:
        """
        Generate Kiro IDE configuration.

        Args:
            template_metadata: Template metadata
            muppet_name: Name of the muppet
            output_path: Output directory path
            config: Generation configuration
        """
        if not config.generate_kiro:
            return

        logger.info(
            f"Generating Kiro configuration for {template_metadata.name} template"
        )

        kiro_dir = output_path / ".kiro"
        kiro_dir.mkdir(parents=True, exist_ok=True)

        # Generate settings
        settings_dir = kiro_dir / "settings"
        settings_dir.mkdir(parents=True, exist_ok=True)

        # Generate language-specific settings
        if template_metadata.language == "java":
            java_settings = self._generate_java_kiro_settings(template_metadata)
            (settings_dir / "java.json").write_text(json.dumps(java_settings, indent=2))

        # Generate MCP configuration
        mcp_config = self._generate_mcp_config(template_metadata, muppet_name)
        (settings_dir / "mcp.json").write_text(json.dumps(mcp_config, indent=2))

        # Generate steering directory structure
        steering_dir = kiro_dir / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)

        # Create shared steering placeholder (will be populated by platform)
        shared_dir = steering_dir / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        (shared_dir / ".gitkeep").write_text("")

        # Create muppet-specific steering directory
        muppet_dir = steering_dir / "muppet-specific"
        muppet_dir.mkdir(parents=True, exist_ok=True)

        # Generate initial muppet-specific steering
        business_logic_md = self._generate_business_logic_steering(
            template_metadata, muppet_name
        )
        (muppet_dir / "business-logic.md").write_text(business_logic_md)

        logger.info("Kiro configuration generation completed")

    def _generate_java_dockerfile(self, template_metadata: TemplateMetadata) -> str:
        """Generate optimized Dockerfile for Java 21 LTS applications."""

        # Enforce Java 21 LTS as per steering requirements
        java_version = template_metadata.java_version or "21"
        if java_version != "21":
            logger.warning(
                f"Template specifies Java {java_version}, but Java 21 LTS is required. Using Java 21."
            )
            java_version = "21"

        return f"""# Auto-generated Dockerfile for {template_metadata.name}
# Generated by Muppet Platform Auto-Generator
# Uses Amazon Corretto 21 LTS as per platform requirements

# Build stage
FROM amazoncorretto:21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \\
    curl \\
    unzip

# Set working directory
WORKDIR /app

# Copy Gradle wrapper and build files
COPY gradlew ./
COPY gradle/ gradle/
COPY build.gradle settings.gradle gradle.properties ./

# Make gradlew executable
RUN chmod +x gradlew

# Validate Java 21 LTS
RUN java -version 2>&1 | grep -q "21.*LTS" || (echo "❌ Java 21 LTS required" && exit 1)
RUN echo "✅ Using Amazon Corretto 21 LTS"

# Download dependencies (for better caching)
COPY src/main/resources/ src/main/resources/
RUN ./gradlew dependencies --no-daemon

# Copy source code
COPY src/ src/

# Build application (shadow JAR for fat JAR with dependencies)
RUN ./gradlew shadowJar --no-daemon

# Verify JAR was created
RUN ls -la build/libs/ && find build/libs/ -name "*.jar" -type f | head -1

# Runtime stage
FROM amazoncorretto:21-alpine AS runtime

# Install runtime dependencies
RUN apk add --no-cache \\
    curl \\
    dumb-init

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \\
    adduser -u 1001 -S appuser -G appgroup

# Set working directory
WORKDIR /app

# Copy JAR from build stage (shadow JAR only)
COPY --from=builder /app/build/libs/*-all.jar app.jar

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Validate Java 21 LTS in runtime
RUN java -version 2>&1 | grep -q "21.*LTS" || (echo "❌ Java 21 LTS required in runtime" && exit 1)
RUN echo "✅ Runtime using Amazon Corretto 21 LTS"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:{template_metadata.port}/health || exit 1

# Expose port
EXPOSE {template_metadata.port}

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Run application with optimized JVM settings for containers
CMD ["java", \\
     "-XX:+UseContainerSupport", \\
     "-XX:MaxRAMPercentage=75.0", \\
     "-XX:+UseG1GC", \\
     "-XX:+UseStringDeduplication", \\
     "-Djava.security.egd=file:/dev/./urandom", \\
     "-jar", "app.jar"]
"""

    def _generate_java_kiro_settings(
        self, template_metadata: TemplateMetadata
    ) -> Dict[str, Any]:
        """Generate Java-specific Kiro settings with Java 21 LTS enforcement."""

        # Enforce Java 21 LTS as per steering requirements
        java_version = template_metadata.java_version or "21"
        if java_version != "21":
            logger.warning(
                f"Template specifies Java {java_version}, but Java 21 LTS is required. Using Java 21."
            )
            java_version = "21"

        return {
            "java": {
                "version": "21",
                "distribution": "amazon-corretto",
                "home": "/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home",
                "enforcement": {
                    "lts_only": True,
                    "allowed_versions": ["21"],
                    "forbidden_versions": ["22", "23", "24", "25"],
                },
            },
            "gradle": {
                "version": "8.5",
                "wrapper": True,
                "daemon": False,
                "java_compatibility": {"source": "VERSION_21", "target": "VERSION_21"},
            },
            "micronaut": {
                "version": template_metadata.framework_version or "4.0.4",
                "features": ["health", "metrics", "logging", "validation", "security"],
                "java_compatibility": "21+",
            },
            "extensions": [
                "vscjava.vscode-java-pack",
                "vscjava.vscode-gradle",
                "redhat.java",
                "vscjava.vscode-java-debug",
                "vscjava.vscode-java-test",
                "vscjava.vscode-maven",
            ],
            "settings": {
                "java.configuration.runtimes": [
                    {
                        "name": "JavaSE-21",
                        "path": "/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home",
                        "default": True,
                    }
                ],
                "java.compile.nullAnalysis.mode": "automatic",
                "java.format.settings.url": "https://raw.githubusercontent.com/google/styleguide/gh-pages/eclipse-java-google-style.xml",
                "java.configuration.checkProjectSettingsExclusions": False,
                "java.project.sourcePaths": ["src/main/java"],
                "java.project.testSourcePaths": ["src/test/java"],
                "java.project.outputPath": "build/classes",
                "gradle.nestedProjects": True,
            },
            "validation": {
                "java_version_check": {
                    "enabled": True,
                    "required_version": "21",
                    "error_on_mismatch": True,
                },
                "gradle_java_check": {
                    "enabled": True,
                    "required_compatibility": "VERSION_21",
                },
            },
        }

    def _generate_mcp_config(
        self, template_metadata: TemplateMetadata, muppet_name: str
    ) -> Dict[str, Any]:
        """Generate MCP configuration for the muppet."""
        return {
            "mcpServers": {
                "muppet-platform": {
                    "command": "uv",
                    "args": ["run", "mcp-server"],
                    "cwd": "{{platform_path}}",
                    "env": {
                        "MUPPET_NAME": muppet_name,
                        "TEMPLATE_TYPE": template_metadata.name,
                    },
                }
            }
        }

    def _generate_business_logic_steering(
        self, template_metadata: TemplateMetadata, muppet_name: str
    ) -> str:
        """Generate initial business logic steering documentation."""
        return f"""# Business Logic Guidelines for {muppet_name}

This document contains muppet-specific development guidelines and patterns.

## Overview

{muppet_name} is a {template_metadata.language} {template_metadata.framework} service that provides [describe your service's purpose here].

## Architecture Patterns

### Service Layer
- Keep business logic in service classes
- Use dependency injection for testability
- Implement proper error handling and validation

### Data Access
- Use repository pattern for data access
- Implement proper transaction management
- Consider caching for frequently accessed data

### API Design
- Follow RESTful principles
- Use proper HTTP status codes (see shared/http-responses.md)
- Implement proper request/response validation

## Testing Strategy

### Unit Tests
- Aim for 70%+ test coverage (see shared/test-coverage.md)
- Mock external dependencies
- Test edge cases and error conditions

### Integration Tests
- Test API endpoints end-to-end
- Use test containers for database testing
- Validate business workflows

## Performance Considerations

### Response Times
- Target < 200ms for simple operations
- Target < 1s for complex operations
- Monitor and alert on performance degradation

### Resource Usage
- Monitor memory usage and optimize as needed
- Use connection pooling for database connections
- Implement proper caching strategies

## Security Guidelines

See shared/security.md for platform-wide security requirements.

### Service-Specific Security
- [Add any service-specific security requirements here]
- Validate all input parameters
- Implement proper authentication/authorization

## Monitoring and Logging

See shared/logging.md for logging standards.

### Business Metrics
- Track key business metrics
- Implement health checks for dependencies
- Set up alerts for critical failures

## Development Workflow

1. Create feature branch from main
2. Implement changes with tests
3. Run local verification: `./scripts/test.sh`
4. Submit pull request
5. Deploy via CI/CD pipeline

## Useful Commands

```bash
# Build the application
./gradlew build

# Run tests
./gradlew test

# Run locally
./scripts/run.sh

# Build Docker image
docker build -t {muppet_name} .
```

## Resources

- [Micronaut Documentation](https://docs.micronaut.io/)
- [Amazon Corretto 21 Guide](https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/)
- [Platform Documentation](../../../docs/)
"""
