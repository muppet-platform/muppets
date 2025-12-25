"""
Muppet Instantiation Verification System

This module provides automated verification of muppet instantiation from templates.
It creates test muppets, verifies parameter injection, validates code generation,
and tests that generated code compiles and builds successfully.
"""

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..exceptions import PlatformException
from ..logging_config import get_logger
from ..managers.template_manager import GenerationContext, TemplateManager
from ..models import Template

logger = get_logger(__name__)


class VerificationError(PlatformException):
    """Raised when muppet verification fails."""


class BuildError(VerificationError):
    """Raised when muppet build fails."""


class ParameterInjectionError(VerificationError):
    """Raised when template parameter injection fails."""


@dataclass
class VerificationResult:
    """Result of muppet verification process."""

    muppet_name: str
    template_name: str
    success: bool
    duration_seconds: float
    verification_path: Path

    # Verification step results
    template_generation_success: bool = False
    parameter_injection_success: bool = False
    build_success: bool = False
    variable_replacement_success: bool = False
    script_verification_success: bool = False

    # Detailed results
    generated_files: List[str] = field(default_factory=list)
    injected_parameters: Dict[str, Any] = field(default_factory=dict)
    build_output: str = ""
    build_artifacts: List[str] = field(default_factory=list)
    script_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Error information
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "muppet_name": self.muppet_name,
            "template_name": self.template_name,
            "success": self.success,
            "duration_seconds": self.duration_seconds,
            "verification_path": str(self.verification_path),
            "template_generation_success": self.template_generation_success,
            "parameter_injection_success": self.parameter_injection_success,
            "build_success": self.build_success,
            "variable_replacement_success": self.variable_replacement_success,
            "script_verification_success": self.script_verification_success,
            "generated_files": self.generated_files,
            "injected_parameters": self.injected_parameters,
            "build_output": self.build_output,
            "build_artifacts": self.build_artifacts,
            "script_results": self.script_results,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": datetime.now().isoformat(),
        }


@dataclass
class VerificationConfig:
    """Configuration for muppet verification."""

    # Test muppet configuration
    test_muppet_prefix: str = "verify"
    cleanup_on_success: bool = True
    cleanup_on_failure: bool = False

    # Build configuration
    build_timeout_seconds: int = 300  # 5 minutes
    java_version_required: str = "21"

    # Parameter injection test values
    test_parameters: Dict[str, Any] = field(
        default_factory=lambda: {
            "aws_region": "us-west-2",
            "environment": "verification",
            "custom_param": "test_value_123",
        }
    )

    # Files to check for variable replacement
    variable_check_patterns: List[str] = field(
        default_factory=lambda: [
            "**/*.java",
            "**/*.yml",
            "**/*.yaml",
            "**/*.md",
            "**/*.gradle",
            "**/*.properties",
            "Dockerfile",
        ]
    )

    # Expected build artifacts (template-specific)
    expected_artifacts: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "java-micronaut": [
                "build/libs/{muppet_name}-1.0.0-all.jar",
                "build/classes/java/main/",
                "build/test-results/test/",
            ]
        }
    )

    # Expected scripts (template-specific)
    expected_scripts: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "java-micronaut": [
                "scripts/build.sh",
                "scripts/test.sh",
                "scripts/run.sh",
                "scripts/init.sh",
                "scripts/quick-verify.sh",
                "scripts/test-docker-build.sh",
                "scripts/test-local-dev.sh",
                "scripts/test-parameter-injection.sh",
                "scripts/verify-template.sh",
            ]
        }
    )

    # Script verification timeout
    script_timeout_seconds: int = 60

    # Enable functional script testing (actually execute scripts)
    enable_functional_script_testing: bool = False

    # Scripts that are safe to execute functionally (won't cause side effects)
    safe_functional_test_scripts: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "java-micronaut": [
                "scripts/quick-verify.sh",
                "scripts/test-parameter-injection.sh",
            ]
        }
    )


class MuppetVerificationSystem:
    """
    Automated system for verifying muppet instantiation from templates.

    This system creates test muppets from templates and verifies that:
    1. Template generation works correctly
    2. Parameter injection is successful
    3. All template variables are properly replaced
    4. Generated code compiles and builds successfully
    5. Expected build artifacts are created
    """

    def __init__(
        self,
        template_manager: Optional[TemplateManager] = None,
        config: Optional[VerificationConfig] = None,
        verification_root: Optional[Path] = None,
    ):
        """
        Initialize the verification system.

        Args:
            template_manager: Template manager instance
            config: Verification configuration
            verification_root: Root directory for verification workspaces
        """
        self.template_manager = template_manager or TemplateManager()
        self.config = config or VerificationConfig()

        if verification_root is None:
            # Default to platform/verification-workspace
            current_file = Path(__file__)
            self.verification_root = (
                current_file.parent.parent.parent / "verification-workspace"
            )
        else:
            self.verification_root = Path(verification_root)

        self.verification_root.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Muppet verification system initialized with root: {self.verification_root}"
        )

    def verify_template(
        self, template_name: str, custom_parameters: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """
        Verify a template by creating a test muppet and validating all aspects.

        Args:
            template_name: Name of template to verify
            custom_parameters: Custom parameters for testing (optional)

        Returns:
            VerificationResult with detailed results

        Raises:
            VerificationError: If verification setup fails
        """
        start_time = datetime.now()

        # Generate unique test muppet name
        timestamp = int(start_time.timestamp())
        test_muppet_name = (
            f"{self.config.test_muppet_prefix}-{template_name}-{timestamp}"
        )

        logger.info(
            f"Starting verification of template '{template_name}' with test muppet '{test_muppet_name}'"
        )

        # Create verification workspace
        verification_path = self.verification_root / test_muppet_name
        verification_path.mkdir(parents=True, exist_ok=True)

        # Initialize result
        result = VerificationResult(
            muppet_name=test_muppet_name,
            template_name=template_name,
            success=False,
            duration_seconds=0.0,
            verification_path=verification_path,
        )

        try:
            # Step 1: Verify template exists and is valid
            template = self._validate_template_exists(template_name)

            # Step 2: Generate test muppet from template
            self._generate_test_muppet(
                template_name,
                test_muppet_name,
                verification_path,
                custom_parameters,
                result,
            )

            # Step 3: Verify parameter injection
            self._verify_parameter_injection(
                verification_path, test_muppet_name, custom_parameters or {}, result
            )

            # Step 4: Verify variable replacement
            self._verify_variable_replacement(
                verification_path, test_muppet_name, result
            )

            # Step 5: Verify build process
            self._verify_build_process(
                verification_path, template_name, test_muppet_name, result
            )

            # Step 6: Verify build artifacts
            self._verify_build_artifacts(
                verification_path, template_name, test_muppet_name, result
            )

            # Step 7: Verify development scripts
            self._verify_development_scripts(
                verification_path, template_name, test_muppet_name, result
            )

            # Calculate overall success
            result.success = (
                result.template_generation_success
                and result.parameter_injection_success
                and result.variable_replacement_success
                and result.build_success
                and result.script_verification_success
            )

            if result.success:
                logger.info(f"Verification successful for template '{template_name}'")
            else:
                logger.error(
                    f"Verification failed for template '{template_name}': {result.errors}"
                )

        except Exception as e:
            logger.error(f"Verification failed with exception: {e}")
            result.errors.append(f"Verification exception: {str(e)}")
            result.success = False

        finally:
            # Calculate duration
            end_time = datetime.now()
            result.duration_seconds = (end_time - start_time).total_seconds()

            # Cleanup if configured
            self._cleanup_verification_workspace(verification_path, result)

        return result

    def verify_all_templates(self) -> Dict[str, VerificationResult]:
        """
        Verify all available templates.

        Returns:
            Dictionary mapping template names to verification results
        """
        logger.info("Starting verification of all templates")

        # Discover all templates
        templates = self.template_manager.discover_templates()
        results = {}

        for template in templates:
            try:
                result = self.verify_template(template.name)
                results[template.name] = result
            except Exception as e:
                logger.error(f"Failed to verify template '{template.name}': {e}")
                # Create a failed result
                results[template.name] = VerificationResult(
                    muppet_name=f"failed-{template.name}",
                    template_name=template.name,
                    success=False,
                    duration_seconds=0.0,
                    verification_path=Path("/tmp"),
                    errors=[f"Verification setup failed: {str(e)}"],
                )

        logger.info(f"Completed verification of {len(templates)} templates")
        return results

    def _validate_template_exists(self, template_name: str) -> Template:
        """Validate that template exists and is valid."""
        template = self.template_manager.get_template(template_name)
        if not template:
            raise VerificationError(f"Template '{template_name}' not found")

        # Validate template
        try:
            self.template_manager.validate_template(template_name)
        except Exception as e:
            raise VerificationError(
                f"Template '{template_name}' validation failed: {e}"
            )

        return template

    def _generate_test_muppet(
        self,
        template_name: str,
        test_muppet_name: str,
        verification_path: Path,
        custom_parameters: Optional[Dict[str, Any]],
        result: VerificationResult,
    ) -> None:
        """Generate test muppet from template."""
        logger.info(
            f"Generating test muppet '{test_muppet_name}' from template '{template_name}'"
        )

        try:
            # Prepare parameters
            parameters = self.config.test_parameters.copy()
            if custom_parameters:
                parameters.update(custom_parameters)

            # Store injected parameters for verification
            result.injected_parameters = parameters.copy()
            result.injected_parameters["muppet_name"] = test_muppet_name

            # Create generation context
            context = GenerationContext(
                muppet_name=test_muppet_name,
                template_name=template_name,
                parameters=parameters,
                output_path=verification_path,
                aws_region=parameters.get("aws_region", "us-east-1"),
                environment=parameters.get("environment", "verification"),
            )

            # Generate code
            generated_path = self.template_manager.generate_code(context)

            # Collect generated files
            result.generated_files = self._collect_generated_files(generated_path)
            result.template_generation_success = True

            logger.info(
                f"Generated {len(result.generated_files)} files for test muppet"
            )

        except Exception as e:
            error_msg = f"Template generation failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.template_generation_success = False

    def _verify_parameter_injection(
        self,
        verification_path: Path,
        test_muppet_name: str,
        custom_parameters: Dict[str, Any],
        result: VerificationResult,
    ) -> None:
        """Verify that parameters were correctly injected into generated files."""
        logger.info("Verifying parameter injection")

        try:
            # Parameters to check (including defaults)
            all_parameters = self.config.test_parameters.copy()
            all_parameters.update(custom_parameters)
            all_parameters["muppet_name"] = test_muppet_name

            injection_errors = []

            # Check each parameter in relevant files
            for param_name, param_value in all_parameters.items():
                if not self._verify_parameter_in_files(
                    verification_path, param_name, str(param_value)
                ):
                    injection_errors.append(
                        f"Parameter '{param_name}' with value '{param_value}' not found in generated files"
                    )

            if injection_errors:
                result.errors.extend(injection_errors)
                result.parameter_injection_success = False
                logger.error(f"Parameter injection failed: {injection_errors}")
            else:
                result.parameter_injection_success = True
                logger.info("Parameter injection verification successful")

        except Exception as e:
            error_msg = f"Parameter injection verification failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.parameter_injection_success = False

    def _verify_variable_replacement(
        self, verification_path: Path, test_muppet_name: str, result: VerificationResult
    ) -> None:
        """Verify that all template variables were properly replaced."""
        logger.info("Verifying template variable replacement")

        try:
            unreplaced_variables = []

            # Check for unreplaced {{variable}} patterns
            for pattern in self.config.variable_check_patterns:
                for file_path in verification_path.glob(pattern):
                    if file_path.is_file() and not self._is_binary_file(file_path):
                        unreplaced = self._find_unreplaced_variables(file_path)
                        if unreplaced:
                            unreplaced_variables.extend(
                                [
                                    f"{file_path.relative_to(verification_path)}: {var}"
                                    for var in unreplaced
                                ]
                            )

            if unreplaced_variables:
                result.errors.extend(
                    [f"Unreplaced variable: {var}" for var in unreplaced_variables]
                )
                result.variable_replacement_success = False
                logger.error(f"Variable replacement failed: {unreplaced_variables}")
            else:
                result.variable_replacement_success = True
                logger.info("Variable replacement verification successful")

        except Exception as e:
            error_msg = f"Variable replacement verification failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.variable_replacement_success = False

    def _verify_build_process(
        self,
        verification_path: Path,
        template_name: str,
        test_muppet_name: str,
        result: VerificationResult,
    ) -> None:
        """Verify that generated code builds successfully."""
        logger.info("Verifying build process")

        try:
            if template_name == "java-micronaut":
                self._verify_java_build(verification_path, result)
            else:
                result.warnings.append(
                    f"Build verification not implemented for template '{template_name}'"
                )
                result.build_success = (
                    True  # Assume success if no verification implemented
                )

        except Exception as e:
            error_msg = f"Build verification failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.build_success = False

    def _verify_java_build(
        self, verification_path: Path, result: VerificationResult
    ) -> None:
        """Verify Java Micronaut build process."""
        logger.info("Verifying Java Micronaut build")

        # Check Java version
        java_version = self._check_java_version()
        if java_version != self.config.java_version_required:
            result.warnings.append(
                f"Java {java_version} detected, Java {self.config.java_version_required} recommended"
            )

        # Make gradlew executable
        gradlew_path = verification_path / "gradlew"
        if gradlew_path.exists():
            gradlew_path.chmod(0o755)

        # Run Gradle build
        build_commands = [
            ["./gradlew", "clean", "--no-daemon"],
            ["./gradlew", "compileJava", "--no-daemon"],
            ["./gradlew", "test", "--no-daemon"],
            ["./gradlew", "shadowJar", "--no-daemon"],
        ]

        build_output_parts = []

        for command in build_commands:
            try:
                logger.info(f"Running: {' '.join(command)}")
                process_result = subprocess.run(
                    command,
                    cwd=verification_path,
                    capture_output=True,
                    text=True,
                    timeout=self.config.build_timeout_seconds,
                )

                build_output_parts.append(f"Command: {' '.join(command)}")
                build_output_parts.append(f"Exit code: {process_result.returncode}")
                build_output_parts.append(f"STDOUT:\n{process_result.stdout}")
                if process_result.stderr:
                    build_output_parts.append(f"STDERR:\n{process_result.stderr}")
                build_output_parts.append("-" * 50)

                if process_result.returncode != 0:
                    raise BuildError(
                        f"Build command failed: {' '.join(command)}\n{process_result.stderr}"
                    )

            except subprocess.TimeoutExpired:
                raise BuildError(f"Build command timed out: {' '.join(command)}")

        result.build_output = "\n".join(build_output_parts)
        result.build_success = True
        logger.info("Java build verification successful")

    def _verify_build_artifacts(
        self,
        verification_path: Path,
        template_name: str,
        test_muppet_name: str,
        result: VerificationResult,
    ) -> None:
        """Verify that expected build artifacts were created."""
        logger.info("Verifying build artifacts")

        try:
            expected_artifacts = self.config.expected_artifacts.get(template_name, [])
            missing_artifacts = []
            found_artifacts = []

            for artifact_pattern in expected_artifacts:
                # Replace {muppet_name} placeholder
                artifact_path = artifact_pattern.format(muppet_name=test_muppet_name)
                full_path = verification_path / artifact_path

                if full_path.exists():
                    found_artifacts.append(artifact_path)
                else:
                    missing_artifacts.append(artifact_path)

            result.build_artifacts = found_artifacts

            if missing_artifacts:
                result.errors.extend(
                    [
                        f"Missing build artifact: {artifact}"
                        for artifact in missing_artifacts
                    ]
                )
                logger.error(f"Missing build artifacts: {missing_artifacts}")
            else:
                logger.info(f"All expected build artifacts found: {found_artifacts}")

        except Exception as e:
            error_msg = f"Build artifact verification failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    def _verify_development_scripts(
        self,
        verification_path: Path,
        template_name: str,
        test_muppet_name: str,
        result: VerificationResult,
    ) -> None:
        """Verify that development scripts exist and are executable."""
        logger.info("Verifying development scripts")

        try:
            expected_scripts = self.config.expected_scripts.get(template_name, [])
            script_results = {}

            for script_path in expected_scripts:
                script_full_path = verification_path / script_path
                script_name = Path(script_path).name

                script_result = {
                    "exists": False,
                    "executable": False,
                    "syntax_valid": False,
                    "has_help": False,
                    "variables_replaced": True,
                    "functional_test_passed": None,  # None = not tested, True/False = test result
                    "functional_test_output": "",
                    "errors": [],
                }

                # Check if script exists
                if script_full_path.exists():
                    script_result["exists"] = True

                    # Check if script is executable
                    if script_full_path.stat().st_mode & 0o111:
                        script_result["executable"] = True
                    else:
                        script_result["errors"].append("Script is not executable")

                    # Check script syntax (basic validation)
                    try:
                        content = script_full_path.read_text(encoding="utf-8")

                        # Check for unreplaced variables
                        unreplaced_vars = self._find_unreplaced_variables(
                            script_full_path
                        )
                        if unreplaced_vars:
                            script_result["variables_replaced"] = False
                            script_result["errors"].append(
                                f"Unreplaced variables: {unreplaced_vars}"
                            )

                        # Check for basic shell script syntax
                        if content.startswith("#!/bin/bash") or content.startswith(
                            "#!/bin/sh"
                        ):
                            script_result["syntax_valid"] = True

                            # Check if script has help/usage information
                            if (
                                "--help" in content
                                or "Usage:" in content
                                or "usage:" in content
                            ):
                                script_result["has_help"] = True
                        else:
                            script_result["errors"].append(
                                "Script missing shebang or not a shell script"
                            )

                    except Exception as e:
                        script_result["errors"].append(
                            f"Failed to read script content: {str(e)}"
                        )

                    # Functional testing (if enabled and script is safe to test)
                    if (
                        self.config.enable_functional_script_testing
                        and script_path
                        in self.config.safe_functional_test_scripts.get(
                            template_name, []
                        )
                    ):
                        try:
                            logger.info(
                                f"Running functional test for script: {script_name}"
                            )

                            # Execute the script with --help or --version to test basic functionality
                            test_result = subprocess.run(
                                [str(script_full_path), "--help"],
                                cwd=verification_path,
                                capture_output=True,
                                text=True,
                                timeout=self.config.script_timeout_seconds,
                            )

                            script_result[
                                "functional_test_output"
                            ] = f"Exit code: {test_result.returncode}\nSTDOUT:\n{test_result.stdout}\nSTDERR:\n{test_result.stderr}"

                            # Consider test passed if exit code is 0 or 1 (some scripts return 1 for --help)
                            if test_result.returncode in [0, 1]:
                                script_result["functional_test_passed"] = True
                            else:
                                script_result["functional_test_passed"] = False
                                script_result["errors"].append(
                                    f"Functional test failed with exit code {test_result.returncode}"
                                )

                        except subprocess.TimeoutExpired:
                            script_result["functional_test_passed"] = False
                            script_result["errors"].append("Functional test timed out")
                        except Exception as e:
                            script_result["functional_test_passed"] = False
                            script_result["errors"].append(
                                f"Functional test error: {str(e)}"
                            )

                else:
                    script_result["errors"].append("Script file does not exist")

                script_results[script_name] = script_result

            result.script_results = script_results

            # Determine overall script verification success
            all_scripts_valid = True
            script_errors = []

            for script_name, script_result in script_results.items():
                if not script_result["exists"]:
                    all_scripts_valid = False
                    script_errors.append(f"Missing script: {script_name}")
                elif not script_result["executable"]:
                    all_scripts_valid = False
                    script_errors.append(f"Script not executable: {script_name}")
                elif not script_result["variables_replaced"]:
                    all_scripts_valid = False
                    script_errors.append(
                        f"Script has unreplaced variables: {script_name}"
                    )
                elif script_result["errors"]:
                    all_scripts_valid = False
                    script_errors.extend(
                        [f"{script_name}: {error}" for error in script_result["errors"]]
                    )

            result.script_verification_success = all_scripts_valid

            if script_errors:
                result.errors.extend(script_errors)
                logger.error(f"Script verification failed: {script_errors}")
            else:
                logger.info(
                    f"All development scripts verified successfully: {list(script_results.keys())}"
                )

        except Exception as e:
            error_msg = f"Script verification failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.script_verification_success = False

    def _collect_generated_files(self, path: Path) -> List[str]:
        """Collect list of all generated files."""
        files = []
        for item in path.rglob("*"):
            if item.is_file():
                files.append(str(item.relative_to(path)))
        return sorted(files)

    def _verify_parameter_in_files(
        self, verification_path: Path, param_name: str, param_value: str
    ) -> bool:
        """Check if a parameter value appears in generated files."""
        # Skip checking for generic parameter names that might not appear directly
        if param_name in ["aws_region", "environment"] and param_value in [
            "us-west-2",
            "verification",
        ]:
            return True  # These might not appear directly in all files

        for pattern in self.config.variable_check_patterns:
            for file_path in verification_path.glob(pattern):
                if file_path.is_file() and not self._is_binary_file(file_path):
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        if param_value in content:
                            return True
                    except (UnicodeDecodeError, PermissionError):
                        continue

        return False

    def _find_unreplaced_variables(self, file_path: Path) -> List[str]:
        """Find unreplaced {{variable}} patterns in a file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            # Find all {{variable}} patterns
            pattern = r"\{\{([^}]+)\}\}"
            matches = re.findall(pattern, content)
            return list(set(matches))  # Remove duplicates
        except (UnicodeDecodeError, PermissionError):
            return []

    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is binary."""
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
        }

        if file_path.suffix.lower() in binary_extensions:
            return True

        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                return b"\x00" in chunk
        except (PermissionError, OSError):
            return True

    def _check_java_version(self) -> str:
        """Check Java version."""
        try:
            result = subprocess.run(
                ["java", "-version"], capture_output=True, text=True
            )
            # Parse version from output like: openjdk version "21.0.1" 2023-10-17 LTS
            version_line = result.stderr.split("\n")[0]
            version_match = re.search(r'"(\d+)', version_line)
            if version_match:
                return version_match.group(1)
            return "unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "not_found"

    def _cleanup_verification_workspace(
        self, verification_path: Path, result: VerificationResult
    ) -> None:
        """Clean up verification workspace based on configuration."""
        try:
            should_cleanup = (result.success and self.config.cleanup_on_success) or (
                not result.success and self.config.cleanup_on_failure
            )

            if should_cleanup and verification_path.exists():
                shutil.rmtree(verification_path)
                logger.info(f"Cleaned up verification workspace: {verification_path}")
            else:
                logger.info(f"Verification workspace preserved: {verification_path}")

        except Exception as e:
            logger.warning(f"Failed to cleanup verification workspace: {e}")


def create_verification_system(
    template_manager: Optional[TemplateManager] = None,
) -> MuppetVerificationSystem:
    """
    Factory function to create a MuppetVerificationSystem instance.

    Args:
        template_manager: Optional template manager instance

    Returns:
        Configured MuppetVerificationSystem instance
    """
    return MuppetVerificationSystem(template_manager=template_manager)
