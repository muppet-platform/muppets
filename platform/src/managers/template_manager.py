"""
Template Manager Component

This module provides template discovery, validation, and code generation
capabilities for the Muppet Platform. It handles template metadata management,
parameter injection, and code generation from templates.
"""

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..exceptions import PlatformException
from ..logging_config import get_logger
from ..models import Template

logger = get_logger(__name__)


class TemplateValidationError(PlatformException):
    """Raised when template validation fails."""


class TemplateNotFoundError(PlatformException):
    """Raised when a requested template is not found."""


class CodeGenerationError(PlatformException):
    """Raised when code generation fails."""


@dataclass
class TemplateMetadata:
    """Extended template metadata with file paths and validation info."""

    template: Template
    template_path: Path
    config_path: Path
    last_validated: Optional[str] = None
    validation_errors: List[str] = None

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


@dataclass
class GenerationContext:
    """Context for template code generation."""

    muppet_name: str
    template_name: str
    parameters: Dict[str, Any]
    output_path: Path
    aws_region: str = "us-east-1"
    environment: str = "development"

    def get_all_variables(self) -> Dict[str, Any]:
        """Get all template variables including defaults."""
        variables = {
            "muppet_name": self.muppet_name,
            "template_name": self.template_name,
            "aws_region": self.aws_region,
            "environment": self.environment,
        }

        # Add platform path for MCP server configuration
        # This points to the platform directory relative to the muppet
        platform_root = Path(__file__).parent.parent.parent.parent
        variables["platform_path"] = str(platform_root / "platform")

        # Add Java-specific variables for Java templates
        if self.template_name == "java-micronaut":
            variables["java_package_name"] = self._to_java_package_name(
                self.muppet_name
            )

        variables.update(self.parameters)
        return variables

    def _to_java_package_name(self, name: str) -> str:
        """
        Convert a muppet name to a valid Java package name.

        Java package naming rules:
        - Must start with a letter
        - Can contain letters, digits, and underscores
        - Cannot contain hyphens or other special characters
        - Cannot be a Java keyword
        - Should be lowercase by convention
        - Should not be empty or excessively long

        Args:
            name: Muppet name to convert

        Returns:
            Valid Java package name

        Raises:
            ValueError: If name cannot be converted to a valid package name
        """
        if not name or not name.strip():
            raise ValueError("Muppet name cannot be empty")

        # Convert to lowercase and strip whitespace
        package_name = name.strip().lower()

        # Replace hyphens with underscores
        package_name = package_name.replace("-", "_")

        # Remove any other invalid characters (keep only letters, digits, underscores)
        package_name = re.sub(r"[^a-z0-9_]", "_", package_name)

        # Clean up multiple consecutive underscores
        package_name = re.sub(r"_+", "_", package_name)

        # Remove leading and trailing underscores
        package_name = package_name.strip("_")

        # If empty after cleaning, use a default
        if not package_name:
            package_name = "muppet"

        # Ensure it starts with a letter (prepend 'pkg_' if it starts with a digit)
        if package_name[0].isdigit():
            package_name = "pkg_" + package_name

        # Handle Java keywords by appending underscore
        java_keywords = {
            "abstract",
            "assert",
            "boolean",
            "break",
            "byte",
            "case",
            "catch",
            "char",
            "class",
            "const",
            "continue",
            "default",
            "do",
            "double",
            "else",
            "enum",
            "extends",
            "final",
            "finally",
            "float",
            "for",
            "goto",
            "i",
            "implements",
            "import",
            "instanceo",
            "int",
            "interface",
            "long",
            "native",
            "new",
            "package",
            "private",
            "protected",
            "public",
            "return",
            "short",
            "static",
            "strictfp",
            "super",
            "switch",
            "synchronized",
            "this",
            "throw",
            "throws",
            "transient",
            "try",
            "void",
            "volatile",
            "while",
        }

        if package_name in java_keywords:
            package_name += "_"

        # Validate final length (Java packages should be reasonable length)
        if len(package_name) > 50:
            # Truncate but ensure it doesn't end with underscore
            package_name = package_name[:50].rstrip("_")
            if not package_name:  # Edge case: all underscores
                package_name = "muppet"

        return package_name


class TemplateManager:
    """
    Manages muppet templates including discovery, validation, and code generation.

    This component handles:
    - Template discovery from the templates directory
    - Template metadata validation
    - Code generation with parameter injection
    - Template versioning and metadata management
    """

    def __init__(self, templates_root: Optional[Path] = None):
        """
        Initialize the template manager.

        Args:
            templates_root: Root directory containing templates.
                          Defaults to ../../../templates relative to this file.
        """
        if templates_root is None:
            # Check if running in Docker container with mounted templates
            docker_templates = Path("/app/templates")
            if docker_templates.exists():
                self.templates_root = docker_templates
            else:
                # Default to templates directory relative to platform
                current_file = Path(__file__)
                self.templates_root = (
                    current_file.parent.parent.parent.parent / "templates"
                )
        else:
            self.templates_root = Path(templates_root)

        self._template_cache: Dict[str, TemplateMetadata] = {}

        logger.info(f"Template manager initialized with root: {self.templates_root}")

    def discover_templates(self) -> List[Template]:
        """
        Discover all available templates in the templates directory.

        Returns:
            List of discovered templates

        Raises:
            TemplateValidationError: If template discovery fails
        """
        logger.info("Discovering templates...")
        templates = []

        if not self.templates_root.exists():
            logger.warning(
                f"Templates root directory does not exist: {self.templates_root}"
            )
            return templates

        for template_dir in self.templates_root.iterdir():
            if not template_dir.is_dir():
                continue

            # Skip special directories
            if template_dir.name.startswith(".") or template_dir.name in [
                "tests",
                "template-tools",
            ]:
                continue

            template_yaml = template_dir / "template.yaml"
            if not template_yaml.exists():
                logger.warning(
                    f"Template directory {template_dir.name} missing template.yaml"
                )
                continue

            try:
                template = self._load_template_metadata(template_dir)
                templates.append(template.template)
                self._template_cache[template.template.name] = template
                logger.info(
                    f"Discovered template: {template.template.name} v{template.template.version}"
                )
            except Exception as e:
                logger.error(f"Failed to load template {template_dir.name}: {e}")
                continue

        logger.info(f"Discovered {len(templates)} templates")
        return templates

    def get_template(self, name: str) -> Optional[Template]:
        """
        Get a specific template by name.

        Args:
            name: Template name

        Returns:
            Template if found, None otherwise
        """
        if name not in self._template_cache:
            # Try to discover templates if not cached
            self.discover_templates()

        template_metadata = self._template_cache.get(name)
        return template_metadata.template if template_metadata else None

    def validate_template(self, name: str) -> bool:
        """
        Validate a template's structure and configuration.

        Args:
            name: Template name to validate

        Returns:
            True if template is valid

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateValidationError: If template validation fails
        """
        template_metadata = self._template_cache.get(name)
        if not template_metadata:
            raise TemplateNotFoundError(f"Template '{name}' not found")

        logger.info(f"Validating template: {name}")
        errors = []

        # Validate basic template structure
        if not template_metadata.template.validate():
            errors.append("Basic template validation failed")

        # Validate required files exist
        template_files = getattr(template_metadata.template, "template_files", [])
        for file_path in template_files:
            full_path = template_metadata.template_path / file_path
            if not full_path.exists():
                errors.append(f"Required template file missing: {file_path}")

        # Validate Terraform modules are specified
        if not template_metadata.template.terraform_modules:
            errors.append("No Terraform modules specified")

        # Validate required variables are specified
        if not template_metadata.template.required_variables:
            errors.append("No required variables specified")

        template_metadata.validation_errors = errors

        if errors:
            error_msg = f"Template validation failed for '{name}': {'; '.join(errors)}"
            logger.error(error_msg)
            raise TemplateValidationError(error_msg)

        logger.info(f"Template '{name}' validation successful")
        return True

    def generate_code(self, context: GenerationContext) -> Path:
        """
        Generate code from a template with parameter injection.

        Args:
            context: Generation context with template name, parameters, and output path

        Returns:
            Path to generated code directory

        Raises:
            TemplateNotFoundError: If template is not found
            CodeGenerationError: If code generation fails
        """
        logger.info(
            f"Generating code for muppet '{context.muppet_name}' using template '{context.template_name}'"
        )

        # Get template metadata
        template_metadata = self._template_cache.get(context.template_name)
        if not template_metadata:
            raise TemplateNotFoundError(f"Template '{context.template_name}' not found")

        # Validate template before generation
        try:
            self.validate_template(context.template_name)
        except TemplateValidationError as e:
            raise CodeGenerationError(
                f"Cannot generate code from invalid template: {e}"
            )

        # Ensure output directory exists
        context.output_path.mkdir(parents=True, exist_ok=True)

        try:
            # Get all template variables
            template_vars = context.get_all_variables()

            # Process all template files
            self._process_template_files(
                template_metadata.template_path, context.output_path, template_vars
            )

            logger.info(
                f"Code generation completed for '{context.muppet_name}' at {context.output_path}"
            )
            return context.output_path

        except Exception as e:
            logger.error(f"Code generation failed for '{context.muppet_name}': {e}")
            raise CodeGenerationError(f"Code generation failed: {e}")

    def get_template_versions(self) -> Dict[str, str]:
        """
        Get version information for all templates.

        Returns:
            Dictionary mapping template names to versions
        """
        versions = {}
        for name, metadata in self._template_cache.items():
            versions[name] = metadata.template.version
        return versions

    def _load_template_metadata(self, template_dir: Path) -> TemplateMetadata:
        """
        Load template metadata from template.yaml file.

        Args:
            template_dir: Path to template directory

        Returns:
            TemplateMetadata object

        Raises:
            TemplateValidationError: If metadata loading fails
        """
        template_yaml = template_dir / "template.yaml"

        try:
            with open(template_yaml, "r") as f:
                config = yaml.safe_load(f)

            # Create Template object from config
            template = Template(
                name=config["name"],
                version=config["version"],
                description=config["description"],
                language=config["language"],
                framework=config["framework"],
                terraform_modules=config.get("terraform_modules", []),
                required_variables=config.get("required_variables", []),
                supported_features=config.get("supported_features", []),
            )

            # Store additional metadata for template processing
            if hasattr(template, "__dict__"):
                template.__dict__.update(
                    {
                        "port": config.get("port", 3000),
                        "metadata": config.get("metadata", {}),
                        "template_files": config.get("template_files", []),
                    }
                )

            return TemplateMetadata(
                template=template, template_path=template_dir, config_path=template_yaml
            )

        except Exception as e:
            raise TemplateValidationError(
                f"Failed to load template metadata from {template_yaml}: {e}"
            )

    def _process_template_files(
        self, template_path: Path, output_path: Path, variables: Dict[str, Any]
    ) -> None:
        """
        Process all template files and generate output with parameter injection.

        This method handles:
        1. Directory name replacement ({{variable}} in directory names)
        2. File name replacement ({{variable}} in file names)
        3. File content replacement ({{variable}} in file contents)

        Args:
            template_path: Path to template directory
            output_path: Path to output directory
            variables: Template variables for injection
        """
        for item in template_path.rglob("*"):
            if item.is_file():
                # Skip template.yaml and other metadata files
                if item.name in ["template.yaml", ".gitkeep"]:
                    continue

                # Calculate relative path from template root
                rel_path = item.relative_to(template_path)

                # Process path components (directories and filename) for variable replacement
                processed_path_parts = []
                for part in rel_path.parts:
                    processed_part = self._replace_variables_in_string(part, variables)
                    processed_path_parts.append(processed_part)

                # Reconstruct the path with processed components
                processed_rel_path = (
                    Path(*processed_path_parts) if processed_path_parts else Path(".")
                )
                output_file = output_path / processed_rel_path

                # Handle .template files (remove .template extension after processing)
                if item.suffix == ".template":
                    output_file = output_file.with_suffix("")

                # Ensure output directory exists
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # Process file based on content type
                if item.suffix == ".template" or self._contains_template_syntax(item):
                    # Template file - process with variable replacement
                    self._process_template_file(item, output_file, variables)
                else:
                    # Regular file - copy and process for any embedded variables
                    self._copy_and_process_file(item, output_file, variables)

    def _replace_variables_in_string(self, text: str, variables: Dict[str, Any]) -> str:
        """
        Replace all {{variable}} patterns in a string with their values.

        Args:
            text: String that may contain {{variable}} patterns
            variables: Dictionary of variable name -> value mappings

        Returns:
            String with all variables replaced
        """
        result = text
        for key, value in variables.items():
            # Replace {{key}} with value
            pattern = f"{{{{{key}}}}}"
            result = result.replace(pattern, str(value))
        return result

    def _copy_and_process_file(
        self, source_file: Path, output_file: Path, variables: Dict[str, Any]
    ) -> None:
        """
        Copy a file and process any template variables in its content.

        Args:
            source_file: Path to source file
            output_file: Path to output file
            variables: Template variables for injection
        """
        try:
            # Check if this is a binary file that shouldn't be processed
            if self._is_binary_file(source_file):
                # Binary file - copy as-is
                shutil.copy2(source_file, output_file)
                return

            # Text file - read, process variables, and write
            with open(source_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace variables in content
            processed_content = self._replace_variables_in_string(content, variables)

            # Write processed content
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(processed_content)

            # Copy file permissions
            shutil.copystat(source_file, output_file)

        except Exception as e:
            # If processing fails, fall back to copying as-is
            logger.warning(f"Failed to process file {source_file}, copying as-is: {e}")
            shutil.copy2(source_file, output_file)

    def _is_binary_file(self, file_path: Path) -> bool:
        """
        Check if a file is binary and should not be processed for template variables.

        Args:
            file_path: Path to file to check

        Returns:
            True if file is binary
        """
        # Known binary extensions
        binary_extensions = {
            ".jar",
            ".class",
            ".png",
            ".jpg",
            ".jpeg",
            ".gi",
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".pd",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
        }

        if file_path.suffix.lower() in binary_extensions:
            return True

        # Try to read a small portion to detect binary content
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                # If chunk contains null bytes, it's likely binary
                return b"\x00" in chunk
        except (PermissionError, OSError):
            return True  # Assume binary if we can't read it

    def _process_template_file(
        self, template_file: Path, output_file: Path, variables: Dict[str, Any]
    ) -> None:
        """
        Process a single template file with variable replacement.

        Args:
            template_file: Path to template file
            output_file: Path to output file
            variables: Template variables for injection
        """
        try:
            # Read template content
            with open(template_file, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Replace all variables in content
            rendered_content = self._replace_variables_in_string(
                template_content, variables
            )

            # Write rendered content
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(rendered_content)

            # Copy file permissions
            shutil.copystat(template_file, output_file)

        except Exception as e:
            raise CodeGenerationError(
                f"Failed to process template file {template_file}: {e}"
            )

    def _contains_template_syntax(self, file_path: Path) -> bool:
        """
        Check if a file contains Jinja2 template syntax.

        Args:
            file_path: Path to file to check

        Returns:
            True if file contains template syntax
        """
        try:
            # Only check text files
            if file_path.suffix in [".jar", ".class", ".png", ".jpg", ".gi", ".zip"]:
                return False

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Look for Jinja2 template syntax
                return "{{" in content or "{%" in content or "{#" in content
        except (UnicodeDecodeError, PermissionError):
            # If we can't read the file as text, assume it's binary
            return False
