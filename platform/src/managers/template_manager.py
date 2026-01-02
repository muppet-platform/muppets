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
from .auto_generator import AutoGenerator, GenerationConfig
from .auto_generator import TemplateMetadata as AutoGenTemplateMetadata

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
        """Get all template variables with proper precedence: user parameters override defaults."""
        # Start with context values (these should be used as defaults)
        variables = {
            "muppet_name": self.muppet_name,
            "template_name": self.template_name,
            "aws_region": self.aws_region,  # Use context aws_region, not hardcoded default
            "environment": self.environment,  # Use context environment, not hardcoded default
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

        # User parameters override everything (CRITICAL: this must come last)
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

    # Error messages
    TEMPLATE_FORMAT_ERROR = (
        "Template files configuration must be a dictionary with 'core' and 'optional' sections. "
        "Found: {type_name}. Please update template.yaml to use the new format."
    )

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
        self.auto_generator = AutoGenerator()

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
        Validate a template's structure and configuration for dual-path architecture.

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

        # Load template config to check structure
        config_path = template_metadata.config_path
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            errors.append(f"Could not load template config: {e}")
            template_metadata.validation_errors = errors
            if errors:
                error_msg = (
                    f"Template validation failed for '{name}': {'; '.join(errors)}"
                )
                logger.error(error_msg)
                raise TemplateValidationError(error_msg)
            return True

        # Validate dual-path architecture configuration
        auto_generate = config.get("auto_generate", {})
        if not isinstance(auto_generate, dict):
            errors.append("auto_generate section must be a dictionary")

        # Validate template files structure (enforce new dictionary format)
        template_files_config = config.get("template_files", {})
        if template_files_config:
            # Enforce new dictionary format with core/optional sections
            if not isinstance(template_files_config, dict):
                raise TemplateValidationError(
                    self.TEMPLATE_FORMAT_ERROR.format(
                        type_name=type(template_files_config).__name__
                    )
                )

            core_files = template_files_config.get("core", [])
            # optional_files = template_files_config.get("optional", [])  # Not used currently

            # Validate core files exist (these are always processed)
            missing_core_files = []
            for file_path in core_files:
                full_path = template_metadata.template_path / file_path
                
                # Check if it's a direct file
                if full_path.exists():
                    continue
                    
                # Check if it's a directory
                if full_path.is_dir():
                    continue
                    
                # For files, check if any file in the template matches the pattern
                found_match = False
                for template_file in template_metadata.template_path.rglob("*"):
                    if template_file.is_file():
                        rel_path = template_file.relative_to(template_metadata.template_path)
                        if str(rel_path) == file_path or file_path.rstrip("/") in str(rel_path):
                            found_match = True
                            break
                
                if not found_match:
                    missing_core_files.append(file_path)

            if missing_core_files:
                errors.append(
                    f"Missing core template files: {', '.join(missing_core_files)}"
                )

            # Optional files are only validated if auto-generation is disabled
            # We don't validate them here since they might be auto-generated

        # Validate Java 21 LTS requirement for Java templates
        if template_metadata.template.language == "java":
            metadata = config.get("metadata", {})
            java_version = metadata.get("java_version")
            if java_version and java_version != "21":
                errors.append(
                    f"Java templates must use Java 21 LTS, found: {java_version}"
                )

        # Validate required variables are specified (for non-auto-generated templates)
        if not auto_generate.get("infrastructure", True):
            # Only validate terraform modules if infrastructure is not auto-generated
            terraform_modules = config.get("terraform_modules", [])
            if not terraform_modules:
                errors.append(
                    "No Terraform modules specified (required when auto_generate.infrastructure = false)"
                )

        template_metadata.validation_errors = errors

        if errors:
            error_msg = f"Template validation failed for '{name}': {'; '.join(errors)}"
            logger.error(error_msg)
            raise TemplateValidationError(error_msg)

        logger.info(f"Template '{name}' validation successful")
        return True

    def generate_code(self, context: GenerationContext) -> Path:
        """
        Generate code from a template with parameter injection and auto-generation.

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

        # Ensure templates are discovered and cached
        if context.template_name not in self._template_cache:
            self.discover_templates()

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
            logger.info(f"Template variables: {list(template_vars.keys())}")

            # Process template files (application code and tests only)
            logger.info("Processing template files...")
            self._process_simplified_template_files(
                template_metadata.template_path, context.output_path, template_vars
            )
            logger.info("Template files processing completed")

            # Auto-generate infrastructure, CI/CD, and Kiro configurations
            logger.info("Starting auto-generation of configurations...")
            self._auto_generate_configurations(
                template_metadata, context.muppet_name, context.output_path
            )
            logger.info("Auto-generation of configurations completed")

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
                        "template_files": config.get("template_files", {}),
                    }
                )

            return TemplateMetadata(
                template=template, template_path=template_dir, config_path=template_yaml
            )

        except Exception as e:
            raise TemplateValidationError(
                f"Failed to load template metadata from {template_yaml}: {e}"
            )

    def _process_simplified_template_files(
        self, template_path: Path, output_path: Path, variables: Dict[str, Any]
    ) -> None:
        """
        Process template files for simplified (auto-generation) mode.
        Only processes core application files, skips infrastructure/CI/CD files.

        Args:
            template_path: Path to template directory
            output_path: Path to output directory
            variables: Template variables for injection
        """
        # Get template metadata to check auto-generation settings
        template_name = variables.get("template_name", "")
        template_metadata = self._template_cache.get(template_name)

        if not template_metadata:
            # Fallback to processing all files
            self._process_template_files(template_path, output_path, variables)
            return

        # Load template config to check auto-generation settings
        config_path = template_metadata.config_path
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load template config: {e}")
            # Process all files if config can't be loaded
            for item in template_path.rglob("*"):
                if item.is_file() and item.name not in ["template.yaml", ".gitkeep"]:
                    self._process_single_template_file(
                        item, output_path, variables, template_path
                    )
            return

        # Determine which files to process based on auto-generation settings
        auto_generate = config.get("auto_generate", {})
        template_files_config = config.get("template_files", {})

        # Enforce new dictionary format (core/optional sections)
        if not isinstance(template_files_config, dict):
            raise CodeGenerationError(
                self.TEMPLATE_FORMAT_ERROR.format(
                    type_name=type(template_files_config).__name__
                )
            )

        # Always process core application files
        core_files = template_files_config.get("core", [])
        files_to_process = set(core_files)

        # Only process optional files if auto-generation is disabled
        optional_files = template_files_config.get("optional", [])
        for optional_file in optional_files:
            # Check if this file type should be auto-generated
            should_auto_generate = self._should_auto_generate_file(
                optional_file, auto_generate
            )
            if not should_auto_generate:
                files_to_process.add(optional_file)

        # Process only the determined files
        for item in template_path.rglob("*"):
            if item.is_file():
                # Skip template.yaml and other metadata files
                if item.name in ["template.yaml", ".gitkeep"]:
                    continue

                # Calculate relative path from template root
                rel_path = item.relative_to(template_path)

                # Check if this file should be processed
                should_process = False
                for file_pattern in files_to_process:
                    if self._matches_file_pattern(rel_path, file_pattern):
                        should_process = True
                        break

                if not should_process:
                    logger.debug(f"Skipping auto-generated file: {rel_path}")
                    continue

                # Process the file
                self._process_single_template_file(
                    item, output_path, variables, template_path
                )

    def _auto_generate_configurations(
        self, template_metadata: TemplateMetadata, muppet_name: str, output_path: Path
    ) -> None:
        """
        Auto-generate infrastructure, CI/CD, and Kiro configurations.

        Args:
            template_metadata: Template metadata
            muppet_name: Name of the muppet
            output_path: Output directory path
        """
        print(f"🔍 DEBUG: _auto_generate_configurations called for {muppet_name}")
        logger.info(f"🔍 DEBUG: _auto_generate_configurations called for {muppet_name}")

        # Load template config to check auto-generation settings
        config_path = template_metadata.config_path
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load template config for auto-generation: {e}")
            return

        auto_generate = config.get("auto_generate", {})
        print(f"🔍 DEBUG: auto_generate config: {auto_generate}")
        logger.info(f"🔍 DEBUG: auto_generate config: {auto_generate}")

        # Convert template metadata to auto-generator format
        auto_gen_metadata = AutoGenTemplateMetadata(
            name=template_metadata.template.name,
            version=template_metadata.template.version,
            description=template_metadata.template.description,
            language=template_metadata.template.language,
            framework=template_metadata.template.framework,
            port=getattr(template_metadata.template, "port", 3000),
            java_version=config.get("metadata", {}).get("java_version"),
            java_distribution=config.get("metadata", {}).get("java_distribution"),
            framework_version=config.get("metadata", {}).get("micronaut_version"),
            build_tool="gradle",
            features=template_metadata.template.supported_features or [],
        )

        # Create generation configuration
        generation_config = GenerationConfig(
            generate_infrastructure=auto_generate.get("infrastructure", True),
            generate_cicd=auto_generate.get("cicd", True),
            generate_kiro=auto_generate.get("kiro", True),
            enable_tls=auto_generate.get("tls", True),
        )

        print(f"🔍 DEBUG: generation_config: {generation_config}")
        logger.info(f"🔍 DEBUG: generation_config: {generation_config}")

        # Generate configurations
        try:
            logger.info(
                f"Starting auto-generation for {muppet_name} with config: {generation_config}"
            )

            if generation_config.generate_infrastructure:
                logger.info("Generating infrastructure...")
                self.auto_generator.generate_infrastructure(
                    auto_gen_metadata, muppet_name, output_path, generation_config
                )
                logger.info("Infrastructure generation completed")

            if generation_config.generate_cicd:
                print(f"🔍 DEBUG: About to generate CI/CD workflows for {muppet_name}")
                logger.info("Generating CI/CD workflows...")
                self.auto_generator.generate_cicd(
                    auto_gen_metadata, muppet_name, output_path, generation_config
                )
                logger.info("CI/CD workflows generation completed")
                print(
                    f"🔍 DEBUG: CI/CD workflows generation completed for {muppet_name}"
                )

            if generation_config.generate_kiro:
                logger.info("Generating Kiro configuration...")
                self.auto_generator.generate_kiro_config(
                    auto_gen_metadata, muppet_name, output_path, generation_config
                )
                logger.info("Kiro configuration generation completed")

            logger.info(f"Auto-generation completed for {muppet_name}")
            print(f"🔍 DEBUG: Auto-generation completed for {muppet_name}")

        except Exception as e:
            logger.error(f"Auto-generation failed for {muppet_name}: {e}")
            logger.exception("Full auto-generation error traceback:")
            print(f"🔍 DEBUG: Auto-generation failed for {muppet_name}: {e}")
            raise CodeGenerationError(f"Auto-generation failed: {e}")

    def _should_auto_generate_file(
        self, file_path: str, auto_generate: Dict[str, bool]
    ) -> bool:
        """
        Determine if a file should be auto-generated based on settings.

        Args:
            file_path: Relative file path
            auto_generate: Auto-generation settings

        Returns:
            True if file should be auto-generated (and thus skipped from template)
        """
        # Map file patterns to auto-generation settings
        file_mappings = {
            "Dockerfile.template": "infrastructure",
            "terraform/": "infrastructure",
            ".github/workflows/": "cicd",
            ".kiro/": "kiro",
        }

        for pattern, setting_key in file_mappings.items():
            if pattern in file_path:
                return auto_generate.get(setting_key, True)

        # Default to not auto-generating (include in template processing)
        return False

    def _matches_file_pattern(self, file_path: Path, pattern: str) -> bool:
        """
        Check if a file path matches a pattern.

        Args:
            file_path: File path to check
            pattern: Pattern to match against

        Returns:
            True if file matches pattern
        """
        file_str = str(file_path)

        # Handle directory patterns
        if pattern.endswith("/"):
            return file_str.startswith(pattern) or f"/{pattern}" in file_str

        # Handle exact file matches
        if pattern in file_str:
            return True

        # Handle parent directory matches
        return any(part == pattern.rstrip("/") for part in file_path.parts)

    def _process_single_template_file(
        self,
        template_file: Path,
        output_path: Path,
        variables: Dict[str, Any],
        template_root: Path,
    ) -> None:
        """
        Process a single template file with variable replacement.

        Args:
            template_file: Path to template file
            output_path: Base output directory
            variables: Template variables for injection
            template_root: Root template directory
        """
        # Calculate relative path and process variables in path
        rel_path = template_file.relative_to(template_root)

        # Process path components for variable replacement
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
        if ".template" in template_file.name:
            # Remove .template from the filename
            # e.g., README.template.md -> README.md
            name_parts = template_file.name.split(".template")
            if len(name_parts) == 2:
                new_name = name_parts[0] + name_parts[1]  # Join parts without .template
                output_file = output_file.parent / new_name

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Process file based on content type
        if ".template" in template_file.name or self._contains_template_syntax(
            template_file
        ):
            # Template file - process with variable replacement
            self._process_template_file(template_file, output_file, variables)
        else:
            # Regular file - copy and process for any embedded variables
            self._copy_and_process_file(template_file, output_file, variables)

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
