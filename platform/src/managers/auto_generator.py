"""
Auto-Generator Component for Simplified Template System

This module automatically generates infrastructure, CI/CD, and Kiro configurations
for templates, allowing template developers to focus only on application code and tests.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..config import get_settings
from ..exceptions import PlatformException
from ..logging_config import get_logger
from .infrastructure_template_processor import InfrastructureTemplateProcessor

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
    features: List[str] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []


@dataclass
class GenerationConfig:
    """Configuration for auto-generation."""

    # Infrastructure generation
    generate_infrastructure: bool = True
    infrastructure_modules: List[str] = None

    # CI/CD generation
    generate_cicd: bool = True
    cicd_features: List[str] = None

    # Kiro generation
    generate_kiro: bool = True
    kiro_features: List[str] = None

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
        self.infrastructure_processor = InfrastructureTemplateProcessor()
        logger.info(
            "Auto-generator initialized with template-based infrastructure processing"
        )

    def generate_infrastructure(
        self,
        template_metadata: TemplateMetadata,
        muppet_name: str,
        output_path: Path,
        config: GenerationConfig,
    ) -> None:
        """
        Generate infrastructure using template-based approach.

        Args:
            template_metadata: Template metadata
            muppet_name: Name of the muppet
            output_path: Output directory path
            config: Generation configuration
        """
        if not config.generate_infrastructure:
            return

        logger.info(
            f"Generating infrastructure for {template_metadata.name} template using templates"
        )

        # Prepare template metadata for processor
        template_meta_dict = {
            "name": template_metadata.name,
            "version": template_metadata.version,
            "description": template_metadata.description,
            "language": template_metadata.language,
            "framework": template_metadata.framework,
            "port": template_metadata.port,
            "java_version": template_metadata.java_version,
            "java_distribution": template_metadata.java_distribution,
            "framework_version": template_metadata.framework_version,
            "build_tool": template_metadata.build_tool,
            "features": template_metadata.features or [],
        }

        # Prepare variables for template processing
        template_variables = {
            "enable_tls": config.enable_tls,
            "aws_region": "us-west-2",  # Default, can be overridden
            "environment": "development",  # Default, can be overridden
        }

        # Use template processor to generate infrastructure
        self.infrastructure_processor.generate_infrastructure(
            template_meta_dict, muppet_name, output_path, template_variables
        )

        # Generate Dockerfile for Java applications with Java 21 LTS
        if template_metadata.language == "java":
            dockerfile_content = self._generate_java_dockerfile(template_metadata)
            (output_path / "Dockerfile").write_text(dockerfile_content)

        logger.info("Infrastructure generation completed using templates")

    def generate_cicd(
        self,
        template_metadata: TemplateMetadata,
        muppet_name: str,
        output_path: Path,
        config: GenerationConfig,
    ) -> None:
        """
        Generate CI/CD workflow configurations.

        Args:
            template_metadata: Template metadata
            muppet_name: Name of the muppet
            output_path: Output directory path
            config: Generation configuration
        """
        if not config.generate_cicd:
            return

        logger.info(f"Generating CI/CD workflows for {template_metadata.name} template")

        github_dir = output_path / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)

        # Generate CI workflow
        ci_workflow = self._generate_ci_workflow(template_metadata, config)
        (github_dir / "ci.yml").write_text(ci_workflow)

        # Generate CD workflow
        cd_workflow = self._generate_cd_workflow(template_metadata, config)
        (github_dir / "cd.yml").write_text(cd_workflow)

        # Generate security workflow
        security_workflow = self._generate_security_workflow(template_metadata, config)
        (github_dir / "security.yml").write_text(security_workflow)

        logger.info("CI/CD generation completed")

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
COPY gradlew gradlew.bat ./
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

# Build application
RUN ./gradlew build --no-daemon -x test

# Verify JAR was created
RUN ls -la build/libs/ && test -f build/libs/*.jar

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

# Copy JAR from build stage
COPY --from=builder /app/build/libs/*.jar app.jar

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

    def _generate_ci_workflow(
        self, template_metadata: TemplateMetadata, config: GenerationConfig
    ) -> str:
        """Generate CI workflow content with Java 21 LTS enforcement."""

        # Language-specific build steps with Java 21 LTS enforcement
        build_steps = ""
        if template_metadata.language == "java":
            # Enforce Java 21 LTS as per steering requirements
            java_version = template_metadata.java_version or "21"
            if java_version != "21":
                logger.warning(
                    f"Template specifies Java {java_version}, but Java 21 LTS is required. Using Java 21."
                )
                java_version = "21"

            build_steps = f"""
      - name: Set up Amazon Corretto JDK 21 (LTS)
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'corretto'

      - name: Validate Java 21 LTS
        run: |
          JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
          if [ "$JAVA_VERSION" -ne 21 ]; then
            echo "❌ Java 21 LTS required, found Java $JAVA_VERSION"
            if [ "$JAVA_VERSION" -gt 21 ]; then
              echo "⚠️  Java $JAVA_VERSION is newer than Java 21 LTS and may cause compatibility issues"
              echo "   Non-LTS Java versions are not supported in production environments"
            fi
            exit 1
          fi
          echo "✅ Java 21 LTS detected"

      - name: Cache Gradle packages
        uses: actions/cache@v3
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: ${{{{ runner.os }}}}-gradle-${{{{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}}}
          restore-keys: |
            ${{{{ runner.os }}}}-gradle-

      - name: Make gradlew executable
        run: chmod +x ./gradlew

      - name: Validate Gradle uses Java 21
        run: |
          ./gradlew --version
          GRADLE_JAVA_VERSION=$(./gradlew --version | grep "JVM:" | sed 's/.*JVM: *\\([0-9]*\\).*/\\1/')
          if [ "$GRADLE_JAVA_VERSION" -ne 21 ]; then
            echo "❌ Gradle is using Java $GRADLE_JAVA_VERSION, but Java 21 LTS is required"
            exit 1
          fi
          echo "✅ Gradle is using Java 21 LTS"

      - name: Build with Gradle
        run: ./gradlew build --no-daemon

      - name: Run tests
        run: ./gradlew test --no-daemon

      - name: Generate test report
        uses: dorny/test-reporter@v1
        if: success() || failure()
        with:
          name: Test Results
          path: build/test-results/test/*.xml
          reporter: java-junit

      - name: Generate JaCoCo test coverage report
        run: ./gradlew jacocoTestReport --no-daemon

      - name: Upload coverage reports to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: build/reports/jacoco/test/jacocoTestReport.xml
"""

        return f"""# Auto-generated CI workflow for {template_metadata.name} template
# Generated by Muppet Platform Auto-Generator
# Enforces Java 21 LTS as per platform requirements

name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        {build_steps}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: build/test-results/

      - name: Upload coverage reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: coverage-reports
          path: build/reports/jacoco/

  security:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Amazon Corretto JDK 21 (LTS)
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'corretto'

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

  build:
    runs-on: ubuntu-latest
    needs: [test, security]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Amazon Corretto JDK 21 (LTS)
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'corretto'

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        run: |
          docker build -t ${{{{ github.repository }}}}:${{{{ github.sha }}}} .

      - name: Test Docker image
        run: |
          # Start container and test health endpoint
          docker run -d --name test-container -p 8080:3000 ${{{{ github.repository }}}}:${{{{ github.sha }}}}
          sleep 10
          curl -f http://localhost:8080/health || exit 1
          docker stop test-container
          docker rm test-container
          echo "✅ Docker image test passed"
"""

    def _generate_cd_workflow(
        self, template_metadata: TemplateMetadata, config: GenerationConfig
    ) -> str:
        """Generate comprehensive CD workflow with infrastructure deployment."""
        return f"""# Auto-generated CD workflow for {template_metadata.name} template
# Generated by Muppet Platform Auto-Generator
# Includes infrastructure deployment, container deployment, and monitoring

name: CD

on:
  push:
    branches: [ main ]
  release:
    types: [ published ]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'development'
        type: choice
        options:
        - development
        - staging
        - production

env:
  AWS_REGION: ${{{{ vars.AWS_REGION || 'us-west-2' }}}}
  MUPPET_NAME: ${{{{ github.repository_owner }}}}/${{{{ github.event.repository.name }}}}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{{{ steps.meta.outputs.tags }}}}
      image-digest: ${{{{ steps.build.outputs.digest }}}}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Amazon Corretto JDK 21 (LTS)
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'corretto'

      - name: Validate Java 21 LTS
        run: |
          JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
          if [ "$JAVA_VERSION" -ne 21 ]; then
            echo "❌ Java 21 LTS required, found Java $JAVA_VERSION"
            exit 1
          fi
          echo "✅ Using Java 21 LTS"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
          aws-secret-access-key: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
          aws-region: ${{{{ env.AWS_REGION }}}}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{{{ steps.login-ecr.outputs.registry }}}}/${{{{ env.MUPPET_NAME }}}}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{{{branch}}}}-
            type=raw,value=latest,enable={{{{is_default_branch}}}}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push Docker image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{{{ steps.meta.outputs.tags }}}}
          labels: ${{{{ steps.meta.outputs.labels }}}}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

      - name: Verify image
        run: |
          # Pull and test the image
          docker pull ${{{{ steps.meta.outputs.tags }}}}

          # Test container startup
          docker run --rm -d --name test-container -p 8080:{template_metadata.port} ${{{{ steps.meta.outputs.tags }}}}
          sleep 30

          # Test health endpoint
          curl -f http://localhost:8080/health || exit 1

          # Cleanup
          docker stop test-container
          echo "✅ Container image verified successfully"

  deploy-infrastructure:
    runs-on: ubuntu-latest
    needs: build-and-push
    strategy:
      matrix:
        environment:
          - ${{{{ github.event.inputs.environment || (github.ref == 'refs/heads/main' && 'development' || 'staging') }}}}

    environment: ${{{{ matrix.environment }}}}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
          aws-secret-access-key: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
          aws-region: ${{{{ env.AWS_REGION }}}}

      - name: Set up OpenTofu
        uses: opentofu/setup-opentofu@v1
        with:
          tofu_version: 1.6.0

      - name: Initialize OpenTofu
        working-directory: terraform
        run: |
          tofu init

      - name: Validate OpenTofu configuration
        working-directory: terraform
        run: |
          tofu validate
          tofu fmt -check

      - name: Plan infrastructure changes
        working-directory: terraform
        env:
          TF_VAR_muppet_name: ${{{{ env.MUPPET_NAME }}}}
          TF_VAR_environment: ${{{{ matrix.environment }}}}
          TF_VAR_ecr_repository_url: ${{{{ needs.build-and-push.outputs.image-tag }}}}
          TF_VAR_image_tag: ${{{{ github.sha }}}}
          TF_VAR_aws_region: ${{{{ env.AWS_REGION }}}}
        run: |
          tofu plan -out=tfplan

      - name: Apply infrastructure changes
        working-directory: terraform
        env:
          TF_VAR_muppet_name: ${{{{ env.MUPPET_NAME }}}}
          TF_VAR_environment: ${{{{ matrix.environment }}}}
          TF_VAR_ecr_repository_url: ${{{{ needs.build-and-push.outputs.image-tag }}}}
          TF_VAR_image_tag: ${{{{ github.sha }}}}
          TF_VAR_aws_region: ${{{{ env.AWS_REGION }}}}
        run: |
          tofu apply -auto-approve tfplan

      - name: Get deployment outputs
        id: outputs
        working-directory: terraform
        run: |
          echo "application-url=$(tofu output -raw application_url)" >> $GITHUB_OUTPUT
          echo "service-name=$(tofu output -raw service_name)" >> $GITHUB_OUTPUT
          echo "cluster-name=$(tofu output -raw cluster_name)" >> $GITHUB_OUTPUT
          echo "load-balancer-dns=$(tofu output -raw load_balancer_dns)" >> $GITHUB_OUTPUT

  deploy-service:
    runs-on: ubuntu-latest
    needs: [build-and-push, deploy-infrastructure]
    strategy:
      matrix:
        environment:
          - ${{{{ github.event.inputs.environment || (github.ref == 'refs/heads/main' && 'development' || 'staging') }}}}

    environment: ${{{{ matrix.environment }}}}

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
          aws-secret-access-key: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
          aws-region: ${{{{ env.AWS_REGION }}}}

      - name: Update ECS service
        run: |
          # Force new deployment with updated image
          aws ecs update-service \\
            --cluster ${{{{ needs.deploy-infrastructure.outputs.cluster-name }}}} \\
            --service ${{{{ needs.deploy-infrastructure.outputs.service-name }}}} \\
            --force-new-deployment

      - name: Wait for deployment to complete
        run: |
          # Wait for service to reach steady state
          aws ecs wait services-stable \\
            --cluster ${{{{ needs.deploy-infrastructure.outputs.cluster-name }}}} \\
            --services ${{{{ needs.deploy-infrastructure.outputs.service-name }}}}

      - name: Verify deployment
        run: |
          # Wait for application to be ready
          sleep 60

          # Test application health
          curl -f ${{{{ needs.deploy-infrastructure.outputs.application-url }}}}/health || exit 1

          echo "✅ Deployment verified successfully"
          echo "🚀 Application available at: ${{{{ needs.deploy-infrastructure.outputs.application-url }}}}"

  post-deployment:
    runs-on: ubuntu-latest
    needs: [build-and-push, deploy-infrastructure, deploy-service]
    if: always()

    steps:
      - name: Deployment summary
        run: |
          echo "## Deployment Summary" >> $GITHUB_STEP_SUMMARY
          echo "- **Environment**: ${{{{ matrix.environment || 'development' }}}}" >> $GITHUB_STEP_SUMMARY
          echo "- **Image**: ${{{{ needs.build-and-push.outputs.image-tag }}}}" >> $GITHUB_STEP_SUMMARY
          echo "- **Application URL**: ${{{{ needs.deploy-infrastructure.outputs.application-url }}}}" >> $GITHUB_STEP_SUMMARY
          echo "- **Load Balancer**: ${{{{ needs.deploy-infrastructure.outputs.load-balancer-dns }}}}" >> $GITHUB_STEP_SUMMARY
          echo "- **Status**: ${{{{ job.status }}}}" >> $GITHUB_STEP_SUMMARY

      - name: Notify deployment status
        if: failure()
        run: |
          echo "❌ Deployment failed. Check the logs above for details."
          exit 1
"""

    def _generate_security_workflow(
        self, template_metadata: TemplateMetadata, config: GenerationConfig
    ) -> str:
        """Generate security workflow content."""
        return f"""# Auto-generated security workflow for {template_metadata.name} template
# Generated by Muppet Platform Auto-Generator

name: Security Scan

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run dependency check
        uses: dependency-check/Dependency-Check_Action@main
        with:
          project: '${{{{ github.repository }}}}'
          path: '.'
          format: 'SARIF'

      - name: Upload dependency check results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'reports/dependency-check-report.sarif'
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
