"""
Infrastructure Template Processor

This module processes infrastructure templates with variable substitution,
maintaining proper separation between Python logic and infrastructure code.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..exceptions import PlatformException
from ..logging_config import get_logger

logger = get_logger(__name__)


class TemplateProcessingError(PlatformException):
    """Raised when template processing fails."""


class InfrastructureTemplateProcessor:
    """
    Processes infrastructure templates with variable substitution.
    Maintains separation between Python logic and infrastructure code.
    """

    def __init__(self, templates_root: Optional[Path] = None):
        """
        Initialize the template processor.

        Args:
            templates_root: Root directory containing infrastructure templates.
                          Defaults to platform/infrastructure-templates
        """
        if templates_root is None:
            current_file = Path(__file__)
            self.templates_root = (
                current_file.parent.parent.parent / "infrastructure-templates"
            )
        else:
            self.templates_root = Path(templates_root)

        self.config = self._load_config()
        logger.info(
            f"Infrastructure template processor initialized with root: {self.templates_root}"
        )

    def generate_infrastructure(
        self,
        template_metadata: Dict[str, Any],
        muppet_name: str,
        output_path: Path,
        variables: Dict[str, Any],
    ) -> None:
        """
        Generate infrastructure by processing templates.

        Args:
            template_metadata: Template metadata including language, framework
            muppet_name: Name of the muppet
            output_path: Output directory path
            variables: Template variables for substitution
        """
        logger.info(f"Generating infrastructure for {muppet_name} using templates")

        # Ensure terraform output directory exists
        terraform_dir = output_path / "terraform"
        terraform_dir.mkdir(parents=True, exist_ok=True)

        # Select appropriate template set based on language/framework
        template_set = self._select_template_set(template_metadata)

        # Prepare template variables
        template_vars = self._prepare_template_variables(
            template_metadata, muppet_name, variables
        )

        # Process each template file
        for template_file in template_set:
            try:
                self._process_template_file(template_file, terraform_dir, template_vars)
            except Exception as e:
                logger.error(f"Failed to process template {template_file}: {e}")
                raise TemplateProcessingError(f"Template processing failed: {e}")

        logger.info(f"Infrastructure generation completed for {muppet_name}")

    def _load_config(self) -> Dict[str, Any]:
        """Load template configuration."""
        config_path = self.templates_root / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Could not load template config: {e}")

        # Return default configuration
        return {
            "templates": {
                "java": {
                    "base_templates": [
                        "base/main.tf.template",
                        "base/variables.tf.template",
                        "base/outputs.tf.template",
                        "base/versions.tf.template",
                    ],
                    "language_templates": [
                        "java/fargate-java.tf.template",
                        "java/monitoring-java.tf.template",
                    ],
                    "variables": {
                        "java_cpu": 1024,
                        "java_memory": 2048,
                        "enable_jvm_metrics": True,
                    },
                }
            },
            "module_versions": {
                "tls_module_version": "v1.0.0",
                "networking_module_version": "v1.0.0",
                "fargate_module_version": "v1.0.0",
                "monitoring_module_version": "v1.0.0",
                "security_module_version": "v1.0.0",
                "ecr_module_version": "v1.0.0",
                "alb_module_version": "v1.0.0",
            },
            "defaults": {
                "terraform_modules_repo": "git::https://github.com/muppet-platform/terraform-modules.git",
                "terraform_state_bucket": "muppet-platform-terraform-state",
                "terraform_locks_table": "muppet-platform-terraform-locks",
                "domain_suffix": "muppet-platform.internal",
            },
        }

    def _select_template_set(self, template_metadata: Dict[str, Any]) -> List[Path]:
        """
        Select appropriate templates based on metadata.
        Returns base templates only - platform and language-specific templates are handled in main.tf processing.

        Args:
            template_metadata: Template metadata

        Returns:
            List of base template file paths to process
        """
        language = template_metadata.get("language", "").lower()

        # Get template configuration for the language
        lang_config = self.config.get("templates", {}).get(language, {})

        if not lang_config:
            logger.warning(f"No template configuration found for language: {language}")
            # Fall back to base templates only
            lang_config = {
                "base_templates": [
                    "base/main.tf.template",
                    "base/variables.tf.template",
                    "base/outputs.tf.template",
                    "base/versions.tf.template",
                ]
            }

        # Only collect base template files (platform and language-specific templates are handled in main.tf processing)
        template_files = []

        # Add base templates
        for template_name in lang_config.get("base_templates", []):
            template_path = self.templates_root / template_name
            if template_path.exists():
                template_files.append(template_path)
            else:
                logger.warning(f"Base template not found: {template_path}")

        logger.info(f"Selected {len(template_files)} base templates for {language}")
        return template_files

    def _prepare_template_variables(
        self,
        template_metadata: Dict[str, Any],
        muppet_name: str,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare variables for template substitution.

        Args:
            template_metadata: Template metadata
            muppet_name: Name of the muppet
            variables: Additional variables

        Returns:
            Dictionary of template variables
        """
        language = template_metadata.get("language", "").lower()

        # Start with default variables
        template_vars = self.config.get("defaults", {}).copy()
        template_vars.update(self.config.get("module_versions", {}))

        # Add language-specific variables
        lang_config = self.config.get("templates", {}).get(language, {})
        template_vars.update(lang_config.get("variables", {}))

        # Add template metadata
        template_vars.update(
            {
                "muppet_name": muppet_name,
                "template_name": template_metadata.get("name", ""),
                "template_version": template_metadata.get("version", ""),
                "language": template_metadata.get("language", ""),
                "framework": template_metadata.get("framework", ""),
                "port": template_metadata.get("port", 3000),
                "java_version": template_metadata.get("java_version", "21"),
                "enable_tls": True,  # Always enable TLS
                "aws_region": variables.get("aws_region", "us-west-2"),
            }
        )

        # Add user-provided variables (these can override defaults)
        template_vars.update(variables)

        return template_vars

    def _process_template_file(
        self, template_file: Path, output_dir: Path, variables: Dict[str, Any]
    ) -> None:
        """
        Process a single template file with variable substitution.

        Args:
            template_file: Path to template file
            output_dir: Output directory
            variables: Template variables
        """
        logger.debug(f"Processing template: {template_file}")

        # Read template content
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                template_content = f.read()
        except Exception as e:
            raise TemplateProcessingError(
                f"Could not read template {template_file}: {e}"
            )

        # Process template with variable substitution
        processed_content = self._substitute_variables(template_content, variables)

        # Determine output filename (remove .template extension)
        output_filename = template_file.name.replace(".template", "")
        output_file = output_dir / output_filename

        # Special handling for main.tf - append language-specific content
        if output_filename == "main.tf":
            processed_content = self._append_language_specific_content(
                processed_content, variables
            )

        # Write processed content
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(processed_content)
            logger.debug(f"Generated: {output_file}")
        except Exception as e:
            raise TemplateProcessingError(f"Could not write output {output_file}: {e}")

    def _append_language_specific_content(
        self, base_content: str, variables: Dict[str, Any]
    ) -> str:
        """
        Append platform standards and language-specific infrastructure content to main.tf.
        Implements layered template architecture: base + platform + language.

        Args:
            base_content: Base main.tf content
            variables: Template variables

        Returns:
            Combined content with platform standards and language-specific additions
        """
        language = variables.get("language", "").lower()

        # Get language configuration
        lang_config = self.config.get("templates", {}).get(language, {})

        # Extract locals block from base content to append at the end
        locals_pattern = r"\n# Common tags and local values\nlocals \{.*?\n\}"
        locals_match = re.search(locals_pattern, base_content, re.DOTALL)

        if locals_match:
            locals_block = locals_match.group(0)
            # Remove locals block from base content
            base_content = base_content.replace(locals_block, "")
        else:
            locals_block = ""

        combined_content = base_content

        # 1. Add platform standards templates (security, TLS, monitoring, compliance)
        platform_templates = lang_config.get("platform_templates", [])
        for template_name in platform_templates:
            template_path = self.templates_root / template_name
            if template_path.exists():
                logger.debug(f"Appending platform standards template: {template_path}")

                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        platform_content = f.read()

                    # Process variables in platform content
                    processed_platform_content = self._substitute_variables(
                        platform_content, variables
                    )

                    # Append to main content with separator
                    combined_content += (
                        f"\n\n# Platform standards from {template_path.name}\n"
                    )
                    combined_content += processed_platform_content

                except Exception as e:
                    logger.warning(
                        f"Could not process platform template {template_path}: {e}"
                    )
            else:
                logger.warning(f"Platform template not found: {template_path}")

        # 2. Add language-specific templates
        language_templates = lang_config.get("language_templates", [])
        for template_name in language_templates:
            template_path = self.templates_root / template_name
            if template_path.exists():
                logger.debug(f"Appending language-specific template: {template_path}")

                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        lang_content = f.read()

                    # Process variables in language-specific content
                    processed_lang_content = self._substitute_variables(
                        lang_content, variables
                    )

                    # Append to main content with separator
                    combined_content += f"\n\n# Language-specific infrastructure from {template_path.name}\n"
                    combined_content += processed_lang_content

                except Exception as e:
                    logger.warning(
                        f"Could not process language template {template_path}: {e}"
                    )
            else:
                logger.warning(f"Language template not found: {template_path}")

        # 3. Append locals block at the very end
        if locals_block:
            processed_locals = self._substitute_variables(locals_block, variables)
            combined_content += f"\n{processed_locals}"

        return combined_content

    def _substitute_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables in template content.

        Supports:
        - Simple substitution: {{variable_name}}
        - Conditional blocks: {{#if condition}}...{{/if}}
        - Equality conditions: {{#if_eq var "value"}}...{{/if_eq}}

        Args:
            content: Template content
            variables: Variables for substitution

        Returns:
            Processed content with variables substituted
        """

        # Simple variable substitution: {{variable_name}}
        def replace_simple_var(match):
            var_name = match.group(1).strip()
            value = variables.get(var_name, f"{{{{UNDEFINED:{var_name}}}}}")
            return str(value)

        content = re.sub(r"\{\{([^#/][^}]*)\}\}", replace_simple_var, content)

        # Conditional blocks: {{#if variable}}...{{/if}}
        def replace_if_block(match):
            condition = match.group(1).strip()
            block_content = match.group(2)

            # Evaluate condition
            if condition in variables and variables[condition]:
                return self._substitute_variables(block_content, variables)
            else:
                return ""

        content = re.sub(
            r"\{\{#if\s+([^}]+)\}\}(.*?)\{\{/if\}\}",
            replace_if_block,
            content,
            flags=re.DOTALL,
        )

        # Equality conditions: {{#if_eq var "value"}}...{{/if_eq}}
        def replace_if_eq_block(match):
            var_name = match.group(1).strip()
            expected_value = match.group(2).strip().strip("\"'")
            block_content = match.group(3)

            # Evaluate equality condition
            actual_value = str(variables.get(var_name, ""))
            if actual_value == expected_value:
                return self._substitute_variables(block_content, variables)
            else:
                return ""

        content = re.sub(
            r"\{\{#if_eq\s+([^\s}]+)\s+([^}]+)\}\}(.*?)\{\{/if_eq\}\}",
            replace_if_eq_block,
            content,
            flags=re.DOTALL,
        )

        return content

    def validate_templates(self) -> bool:
        """
        Validate all infrastructure templates.

        Returns:
            True if all templates are valid
        """
        logger.info("Validating infrastructure templates")

        errors = []

        # Check if templates directory exists
        if not self.templates_root.exists():
            errors.append(f"Templates directory not found: {self.templates_root}")
            return False

        # Validate each language configuration
        for language, config in self.config.get("templates", {}).items():
            # Check base templates
            for template_name in config.get("base_templates", []):
                template_path = self.templates_root / template_name
                if not template_path.exists():
                    errors.append(f"Base template not found: {template_path}")

            # Check platform templates
            for template_name in config.get("platform_templates", []):
                template_path = self.templates_root / template_name
                if not template_path.exists():
                    errors.append(f"Platform template not found: {template_path}")

            # Check language templates
            for template_name in config.get("language_templates", []):
                template_path = self.templates_root / template_name
                if not template_path.exists():
                    errors.append(f"Language template not found: {template_path}")

        if errors:
            for error in errors:
                logger.error(error)
            return False

        logger.info("All infrastructure templates validated successfully")
        return True
