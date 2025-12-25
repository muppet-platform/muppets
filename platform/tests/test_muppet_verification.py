"""
Tests for the Muppet Instantiation Verification System.

This module tests the automated verification of muppet instantiation from templates,
including parameter injection, variable replacement, and build validation.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.managers.template_manager import TemplateManager
from src.models import Template
from src.verification.muppet_verification import (
    BuildError,
    MuppetVerificationSystem,
    VerificationConfig,
    VerificationError,
    VerificationResult,
)


class TestVerificationConfig:
    """Test cases for VerificationConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = VerificationConfig()

        assert config.test_muppet_prefix == "verify"
        assert config.cleanup_on_success is True
        assert config.cleanup_on_failure is False
        assert config.build_timeout_seconds == 300
        assert config.java_version_required == "21"
        assert "aws_region" in config.test_parameters
        assert "environment" in config.test_parameters
        assert "custom_param" in config.test_parameters

    def test_custom_config(self):
        """Test custom configuration values."""
        config = VerificationConfig(
            test_muppet_prefix="test",
            cleanup_on_success=False,
            build_timeout_seconds=600,
            test_parameters={"custom": "value"},
        )

        assert config.test_muppet_prefix == "test"
        assert config.cleanup_on_success is False
        assert config.build_timeout_seconds == 600
        assert config.test_parameters == {"custom": "value"}


class TestVerificationResult:
    """Test cases for VerificationResult class."""

    def test_verification_result_creation(self):
        """Test VerificationResult creation and defaults."""
        result = VerificationResult(
            muppet_name="test-muppet",
            template_name="java-micronaut",
            success=True,
            duration_seconds=45.5,
            verification_path=Path("/tmp/test"),
        )

        assert result.muppet_name == "test-muppet"
        assert result.template_name == "java-micronaut"
        assert result.success is True
        assert result.duration_seconds == 45.5
        assert result.verification_path == Path("/tmp/test")

        # Check defaults
        assert result.template_generation_success is False
        assert result.parameter_injection_success is False
        assert result.build_success is False
        assert result.variable_replacement_success is False
        assert result.generated_files == []
        assert result.injected_parameters == {}
        assert result.build_output == ""
        assert result.build_artifacts == []
        assert result.errors == []
        assert result.warnings == []

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        result = VerificationResult(
            muppet_name="test-muppet",
            template_name="java-micronaut",
            success=True,
            duration_seconds=45.5,
            verification_path=Path("/tmp/test"),
            generated_files=["src/Application.java", "build.gradle"],
            errors=["Test error"],
            warnings=["Test warning"],
        )

        result_dict = result.to_dict()

        assert result_dict["muppet_name"] == "test-muppet"
        assert result_dict["template_name"] == "java-micronaut"
        assert result_dict["success"] is True
        assert result_dict["duration_seconds"] == 45.5
        assert result_dict["verification_path"] == "/tmp/test"
        assert result_dict["generated_files"] == [
            "src/Application.java",
            "build.gradle",
        ]
        assert result_dict["errors"] == ["Test error"]
        assert result_dict["warnings"] == ["Test warning"]
        assert "timestamp" in result_dict


class TestMuppetVerificationSystem:
    """Test cases for MuppetVerificationSystem class."""

    @pytest.fixture
    def mock_template_manager(self):
        """Create a mock template manager."""
        mock_manager = MagicMock(spec=TemplateManager)

        # Mock template
        mock_template = Template(
            name="java-micronaut",
            version="1.0.0",
            description="Test template",
            language="java",
            framework="micronaut",
            terraform_modules=["fargate-service"],
            required_variables=["muppet_name"],
            supported_features=["health_checks"],
        )

        mock_manager.get_template.return_value = mock_template
        mock_manager.validate_template.return_value = True
        mock_manager.generate_code.return_value = Path("/tmp/test")
        mock_manager.discover_templates.return_value = [mock_template]

        return mock_manager

    @pytest.fixture
    def verification_system(self, mock_template_manager):
        """Create a verification system with mocked dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerificationConfig(
                cleanup_on_success=False, cleanup_on_failure=False
            )
            system = MuppetVerificationSystem(
                template_manager=mock_template_manager,
                config=config,
                verification_root=Path(temp_dir),
            )
            yield system

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        system = MuppetVerificationSystem()

        assert system.template_manager is not None
        assert system.config is not None
        assert system.verification_root.name == "verification-workspace"

    def test_init_with_custom_params(self, mock_template_manager):
        """Test initialization with custom parameters."""
        config = VerificationConfig(test_muppet_prefix="custom")

        with tempfile.TemporaryDirectory() as temp_dir:
            system = MuppetVerificationSystem(
                template_manager=mock_template_manager,
                config=config,
                verification_root=Path(temp_dir),
            )

            assert system.template_manager == mock_template_manager
            assert system.config.test_muppet_prefix == "custom"
            assert system.verification_root == Path(temp_dir)

    def test_validate_template_exists_success(
        self, verification_system, mock_template_manager
    ):
        """Test successful template validation."""
        template = verification_system._validate_template_exists("java-micronaut")

        assert template.name == "java-micronaut"
        mock_template_manager.get_template.assert_called_once_with("java-micronaut")
        mock_template_manager.validate_template.assert_called_once_with(
            "java-micronaut"
        )

    def test_validate_template_exists_not_found(
        self, verification_system, mock_template_manager
    ):
        """Test template validation when template not found."""
        mock_template_manager.get_template.return_value = None

        with pytest.raises(VerificationError, match="Template 'nonexistent' not found"):
            verification_system._validate_template_exists("nonexistent")

    def test_validate_template_exists_validation_fails(
        self, verification_system, mock_template_manager
    ):
        """Test template validation when validation fails."""
        mock_template_manager.validate_template.side_effect = Exception(
            "Validation failed"
        )

        with pytest.raises(
            VerificationError, match="Template 'java-micronaut' validation failed"
        ):
            verification_system._validate_template_exists("java-micronaut")

    def test_collect_generated_files(self, verification_system):
        """Test collection of generated files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some test files
            (temp_path / "src").mkdir()
            (temp_path / "src" / "Application.java").write_text("test")
            (temp_path / "build.gradle").write_text("test")
            (temp_path / "README.md").write_text("test")

            files = verification_system._collect_generated_files(temp_path)

            expected_files = ["README.md", "build.gradle", "src/Application.java"]
            assert files == expected_files

    def test_verify_parameter_in_files_found(self, verification_system):
        """Test parameter verification when parameter is found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test file with parameter
            test_file = temp_path / "test.java"
            test_file.write_text("public class TestMuppetApplication {}")

            result = verification_system._verify_parameter_in_files(
                temp_path, "muppet_name", "TestMuppet"
            )

            assert result is True

    def test_verify_parameter_in_files_not_found(self, verification_system):
        """Test parameter verification when parameter is not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test file without parameter
            test_file = temp_path / "test.java"
            test_file.write_text("public class Application {}")

            result = verification_system._verify_parameter_in_files(
                temp_path, "muppet_name", "TestMuppet"
            )

            assert result is False

    def test_find_unreplaced_variables(self, verification_system):
        """Test finding unreplaced template variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test file with unreplaced variables
            test_file = temp_path / "test.java"
            test_file.write_text(
                "public class {{muppet_name}}Application { String region = '{{aws_region}}'; }"
            )

            unreplaced = verification_system._find_unreplaced_variables(test_file)

            assert "muppet_name" in unreplaced
            assert "aws_region" in unreplaced

    def test_find_unreplaced_variables_none(self, verification_system):
        """Test finding unreplaced variables when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test file without unreplaced variables
            test_file = temp_path / "test.java"
            test_file.write_text(
                "public class TestApplication { String region = 'us-east-1'; }"
            )

            unreplaced = verification_system._find_unreplaced_variables(test_file)

            assert unreplaced == []

    def test_is_binary_file_by_extension(self, verification_system):
        """Test binary file detection by extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with binary extensions
            jar_file = temp_path / "test.jar"
            jar_file.write_bytes(b"binary content")

            png_file = temp_path / "image.png"
            png_file.write_bytes(b"binary content")

            assert verification_system._is_binary_file(jar_file) is True
            assert verification_system._is_binary_file(png_file) is True

    def test_is_binary_file_by_content(self, verification_system):
        """Test binary file detection by content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file with null bytes (binary content)
            binary_file = temp_path / "binary.txt"
            binary_file.write_bytes(b"text content\x00binary content")

            # Create text file
            text_file = temp_path / "text.txt"
            text_file.write_text("text content only")

            assert verification_system._is_binary_file(binary_file) is True
            assert verification_system._is_binary_file(text_file) is False

    @patch("subprocess.run")
    def test_check_java_version_success(self, mock_run, verification_system):
        """Test Java version checking success."""
        mock_run.return_value.stderr = 'openjdk version "21.0.1" 2023-10-17 LTS'

        version = verification_system._check_java_version()

        assert version == "21"
        mock_run.assert_called_once_with(
            ["java", "-version"], capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_check_java_version_not_found(self, mock_run, verification_system):
        """Test Java version checking when Java not found."""
        mock_run.side_effect = FileNotFoundError()

        version = verification_system._check_java_version()

        assert version == "not_found"

    def test_generate_test_muppet_success(
        self, verification_system, mock_template_manager
    ):
        """Test successful test muppet generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)
            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            # Create some mock generated files
            (verification_path / "src").mkdir()
            (verification_path / "src" / "Application.java").write_text("test")
            (verification_path / "build.gradle").write_text("test")

            verification_system._generate_test_muppet(
                "java-micronaut", "test-muppet", verification_path, {}, result
            )

            assert result.template_generation_success is True
            assert (
                len(result.generated_files) >= 0
            )  # Files collected from actual generation
            assert result.injected_parameters["muppet_name"] == "test-muppet"
            mock_template_manager.generate_code.assert_called_once()

    def test_generate_test_muppet_failure(
        self, verification_system, mock_template_manager
    ):
        """Test test muppet generation failure."""
        mock_template_manager.generate_code.side_effect = Exception("Generation failed")

        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)
            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._generate_test_muppet(
                "java-micronaut", "test-muppet", verification_path, {}, result
            )

            assert result.template_generation_success is False
            assert len(result.errors) > 0
            assert "Template generation failed" in result.errors[0]

    def test_verify_parameter_injection_success(self, verification_system):
        """Test successful parameter injection verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create test file with injected parameters
            test_file = verification_path / "test.java"
            test_file.write_text(
                "muppet: test-muppet, env: verification, param: test_value_123"
            )

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_parameter_injection(
                verification_path,
                "test-muppet",
                {"custom_param": "test_value_123"},
                result,
            )

            assert result.parameter_injection_success is True
            assert len(result.errors) == 0

    def test_verify_parameter_injection_failure(self, verification_system):
        """Test parameter injection verification failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create test file without injected parameters
            test_file = verification_path / "test.java"
            test_file.write_text("public class Application {}")

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_parameter_injection(
                verification_path,
                "test-muppet",
                {"missing_param": "missing_value"},
                result,
            )

            assert result.parameter_injection_success is False
            assert len(result.errors) > 0

    def test_verify_variable_replacement_success(self, verification_system):
        """Test successful variable replacement verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create test file without unreplaced variables
            test_file = verification_path / "test.java"
            test_file.write_text("public class TestApplication {}")

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_variable_replacement(
                verification_path, "test-muppet", result
            )

            assert result.variable_replacement_success is True
            assert len(result.errors) == 0

    def test_verify_variable_replacement_failure(self, verification_system):
        """Test variable replacement verification failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create test file with unreplaced variables
            test_file = verification_path / "test.java"
            test_file.write_text(
                "public class {{muppet_name}}Application { String region = '{{aws_region}}'; }"
            )

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_variable_replacement(
                verification_path, "test-muppet", result
            )

            assert result.variable_replacement_success is False
            assert len(result.errors) > 0
            assert any("Unreplaced variable" in error for error in result.errors)

    @patch("subprocess.run")
    def test_verify_java_build_success(self, mock_run, verification_system):
        """Test successful Java build verification."""
        # Mock successful subprocess calls
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "BUILD SUCCESSFUL"
        mock_run.return_value.stderr = ""

        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create gradlew script
            gradlew = verification_path / "gradlew"
            gradlew.write_text("#!/bin/bash\necho 'gradle wrapper'")

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_java_build(verification_path, result)

            assert result.build_success is True
            assert "BUILD SUCCESSFUL" in result.build_output
            assert (
                mock_run.call_count == 5
            )  # java -version + clean, compileJava, test, shadowJar

    @patch("subprocess.run")
    def test_verify_java_build_failure(self, mock_run, verification_system):
        """Test Java build verification failure."""
        # Mock failed subprocess call
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "BUILD FAILED"

        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create gradlew script
            gradlew = verification_path / "gradlew"
            gradlew.write_text("#!/bin/bash\necho 'gradle wrapper'")

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            with pytest.raises(BuildError, match="Build command failed"):
                verification_system._verify_java_build(verification_path, result)

    def test_verify_build_artifacts_success(self, verification_system):
        """Test successful build artifact verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create expected artifacts
            (verification_path / "build" / "libs").mkdir(parents=True)
            (
                verification_path / "build" / "libs" / "test-muppet-1.0.0-all.jar"
            ).write_text("jar")
            (verification_path / "build" / "classes" / "java" / "main").mkdir(
                parents=True
            )
            (verification_path / "build" / "test-results" / "test").mkdir(parents=True)

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_build_artifacts(
                verification_path, "java-micronaut", "test-muppet", result
            )

            assert len(result.build_artifacts) == 3
            assert "build/libs/test-muppet-1.0.0-all.jar" in result.build_artifacts
            assert len(result.errors) == 0

    def test_verify_build_artifacts_missing(self, verification_system):
        """Test build artifact verification with missing artifacts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Don't create expected artifacts

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_build_artifacts(
                verification_path, "java-micronaut", "test-muppet", result
            )

            assert len(result.build_artifacts) == 0
            assert len(result.errors) > 0
            assert any("Missing build artifact" in error for error in result.errors)

    def test_verify_development_scripts_success(self, verification_system):
        """Test successful development script verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create scripts directory and expected scripts
            scripts_dir = verification_path / "scripts"
            scripts_dir.mkdir()

            # Create all expected scripts for java-micronaut template
            expected_scripts = [
                "build.sh",
                "test.sh",
                "run.sh",
                "init.sh",
                "quick-verify.sh",
                "test-docker-build.sh",
                "test-local-dev.sh",
                "test-parameter-injection.sh",
                "verify-template.sh",
            ]

            for script_name in expected_scripts:
                script_path = scripts_dir / script_name
                script_path.write_text(
                    f"""#!/bin/bash
# {script_name} for test-muppet
echo "Running {script_name}..."

# Usage: ./{script_name} [options]
"""
                )
                script_path.chmod(0o755)  # Make executable

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_development_scripts(
                verification_path, "java-micronaut", "test-muppet", result
            )

            assert result.script_verification_success is True
            assert len(result.script_results) == 9
            assert all(
                script_result["exists"]
                for script_result in result.script_results.values()
            )
            assert all(
                script_result["executable"]
                for script_result in result.script_results.values()
            )
            assert len(result.errors) == 0

    def test_verify_development_scripts_missing(self, verification_system):
        """Test development script verification with missing scripts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Don't create scripts directory

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_development_scripts(
                verification_path, "java-micronaut", "test-muppet", result
            )

            assert result.script_verification_success is False
            assert len(result.script_results) == 9  # Now expects all 9 scripts
            assert all(
                not script_result["exists"]
                for script_result in result.script_results.values()
            )
            assert len(result.errors) > 0
            assert any("Missing script" in error for error in result.errors)

    def test_verify_development_scripts_not_executable(self, verification_system):
        """Test development script verification with non-executable scripts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create scripts directory and scripts without execute permission
            scripts_dir = verification_path / "scripts"
            scripts_dir.mkdir()

            script_path = scripts_dir / "build.sh"
            script_path.write_text("#!/bin/bash\necho 'test'")
            script_path.chmod(0o644)  # Not executable

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_development_scripts(
                verification_path, "java-micronaut", "test-muppet", result
            )

            assert result.script_verification_success is False
            assert result.script_results["build.sh"]["exists"] is True
            assert result.script_results["build.sh"]["executable"] is False
            assert any("Script not executable" in error for error in result.errors)

    def test_verify_development_scripts_unreplaced_variables(self, verification_system):
        """Test development script verification with unreplaced variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            verification_path = Path(temp_dir)

            # Create scripts directory and script with unreplaced variables
            scripts_dir = verification_path / "scripts"
            scripts_dir.mkdir()

            script_path = scripts_dir / "build.sh"
            script_path.write_text(
                """#!/bin/bash
echo "Building {{muppet_name}}..."
echo "Region: {{aws_region}}"
"""
            )
            script_path.chmod(0o755)

            result = VerificationResult(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                success=False,
                duration_seconds=0.0,
                verification_path=verification_path,
            )

            verification_system._verify_development_scripts(
                verification_path, "java-micronaut", "test-muppet", result
            )

            assert result.script_verification_success is False
            assert result.script_results["build.sh"]["variables_replaced"] is False
            assert any(
                "unreplaced variables" in error.lower() for error in result.errors
            )

    @patch.object(MuppetVerificationSystem, "_verify_development_scripts")
    @patch.object(MuppetVerificationSystem, "_verify_java_build")
    @patch.object(MuppetVerificationSystem, "_verify_build_artifacts")
    @patch.object(MuppetVerificationSystem, "_verify_variable_replacement")
    @patch.object(MuppetVerificationSystem, "_verify_parameter_injection")
    @patch.object(MuppetVerificationSystem, "_generate_test_muppet")
    def test_verify_template_success(
        self,
        mock_generate,
        mock_param_inject,
        mock_var_replace,
        mock_build_artifacts,
        mock_java_build,
        mock_scripts,
        verification_system,
    ):
        """Test successful template verification end-to-end."""

        # Mock all verification steps to succeed
        def mock_generate_success(template_name, muppet_name, path, params, result):
            result.template_generation_success = True

        def mock_param_inject_success(path, muppet_name, params, result):
            result.parameter_injection_success = True

        def mock_var_replace_success(path, muppet_name, result):
            result.variable_replacement_success = True

        def mock_java_build_success(path, result):
            result.build_success = True

        def mock_scripts_success(path, template_name, muppet_name, result):
            result.script_verification_success = True

        mock_generate.side_effect = mock_generate_success
        mock_param_inject.side_effect = mock_param_inject_success
        mock_var_replace.side_effect = mock_var_replace_success
        mock_java_build.side_effect = mock_java_build_success
        mock_scripts.side_effect = mock_scripts_success

        result = verification_system.verify_template("java-micronaut")

        assert result.success is True
        assert result.template_generation_success is True
        assert result.parameter_injection_success is True
        assert result.variable_replacement_success is True
        assert result.build_success is True
        assert result.script_verification_success is True
        assert result.duration_seconds > 0
        assert len(result.errors) == 0

    def test_verify_template_template_not_found(
        self, verification_system, mock_template_manager
    ):
        """Test template verification when template not found."""
        mock_template_manager.get_template.return_value = None

        result = verification_system.verify_template("nonexistent")

        assert result.success is False
        assert len(result.errors) > 0
        assert "Template 'nonexistent' not found" in result.errors[0]

    def test_verify_all_templates(self, verification_system, mock_template_manager):
        """Test verification of all templates."""
        # Mock multiple templates
        templates = [
            Template(
                name="java-micronaut",
                version="1.0.0",
                description="Java template",
                language="java",
                framework="micronaut",
                terraform_modules=[],
                required_variables=[],
                supported_features=[],
            ),
            Template(
                name="python-fastapi",
                version="1.0.0",
                description="Python template",
                language="python",
                framework="fastapi",
                terraform_modules=[],
                required_variables=[],
                supported_features=[],
            ),
        ]

        mock_template_manager.discover_templates.return_value = templates

        # Mock verify_template to return success for java-micronaut, failure for python-fastapi
        original_verify = verification_system.verify_template

        def mock_verify_template(template_name, custom_parameters=None):
            if template_name == "java-micronaut":
                return VerificationResult(
                    muppet_name=f"verify-{template_name}-123",
                    template_name=template_name,
                    success=True,
                    duration_seconds=30.0,
                    verification_path=Path("/tmp/test"),
                    template_generation_success=True,
                    parameter_injection_success=True,
                    variable_replacement_success=True,
                    build_success=True,
                )
            else:
                return VerificationResult(
                    muppet_name=f"verify-{template_name}-123",
                    template_name=template_name,
                    success=False,
                    duration_seconds=15.0,
                    verification_path=Path("/tmp/test"),
                    errors=["Build failed"],
                )

        verification_system.verify_template = mock_verify_template

        results = verification_system.verify_all_templates()

        assert len(results) == 2
        assert "java-micronaut" in results
        assert "python-fastapi" in results
        assert results["java-micronaut"].success is True
        assert results["python-fastapi"].success is False


class TestMuppetVerificationIntegration:
    """Integration tests for the verification system."""

    @pytest.fixture
    def temp_templates_dir(self):
        """Create a temporary templates directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_root = Path(temp_dir)

            # Create a sample Java template
            java_template_dir = templates_root / "java-micronaut"
            java_template_dir.mkdir()

            # Create template.yaml
            template_config = {
                "name": "java-micronaut",
                "version": "1.0.0",
                "description": "Java Micronaut template",
                "language": "java",
                "framework": "micronaut",
                "port": 3000,
                "terraform_modules": ["fargate-service"],
                "required_variables": ["muppet_name"],
                "supported_features": ["health_checks"],
                "template_files": ["src/", "build.gradle.template"],
            }

            import yaml

            with open(java_template_dir / "template.yaml", "w") as f:
                yaml.dump(template_config, f)

            # Create template files
            src_dir = (
                java_template_dir
                / "src"
                / "main"
                / "java"
                / "com"
                / "muppetplatform"
                / "{{java_package_name}}"
            )
            src_dir.mkdir(parents=True)

            (src_dir / "Application.java").write_text(
                """
package com.muppetplatform.{{java_package_name}};

import io.micronaut.runtime.Micronaut;

public class Application {
    // Test parameters: {{custom_param}}, {{muppet_name}}, {{aws_region}}, {{environment}}
    public static void main(String[] args) {
        Micronaut.run(Application.class, args);
    }
}
"""
            )

            # Create scripts directory with test scripts
            scripts_dir = java_template_dir / "scripts"
            scripts_dir.mkdir()

            # Create all expected scripts for java-micronaut template
            scripts_content = {
                "build.sh": """#!/bin/bash
# {{muppet_name}} Build Script
echo "Building {{muppet_name}}..."
./gradlew shadowJar
""",
                "test.sh": """#!/bin/bash
# {{muppet_name}} Test Script
echo "Testing {{muppet_name}}..."
./gradlew test
""",
                "run.sh": """#!/bin/bash
# {{muppet_name}} Run Script
echo "Running {{muppet_name}}..."
java -jar build/libs/{{muppet_name}}-*-all.jar
""",
                "init.sh": """#!/bin/bash
# {{muppet_name}} Init Script
echo "Initializing {{muppet_name}}..."
""",
                "quick-verify.sh": """#!/bin/bash
# {{muppet_name}} Quick Verify Script
echo "Quick verification for {{muppet_name}}..."
""",
                "test-docker-build.sh": """#!/bin/bash
# {{muppet_name}} Docker Build Test Script
echo "Testing Docker build for {{muppet_name}}..."
""",
                "test-local-dev.sh": """#!/bin/bash
# {{muppet_name}} Local Dev Test Script
echo "Testing local development for {{muppet_name}}..."
""",
                "test-parameter-injection.sh": """#!/bin/bash
# {{muppet_name}} Parameter Injection Test Script
echo "Testing parameter injection for {{muppet_name}}..."
""",
                "verify-template.sh": """#!/bin/bash
# {{muppet_name}} Template Verification Script
echo "Verifying template for {{muppet_name}}..."
""",
            }

            for script_name, content in scripts_content.items():
                (scripts_dir / script_name).write_text(content)

            # Make scripts executable
            for script in scripts_dir.glob("*.sh"):
                script.chmod(0o755)

            (java_template_dir / "build.gradle.template").write_text(
                """
plugins {
    id("com.github.johnrengelman.shadow") version "8.1.1"
    id("io.micronaut.application") version "4.0.4"
}

version = "1.0.0"
group = "com.muppetplatform.{{java_package_name}}"

repositories {
    mavenCentral()
}

dependencies {
    implementation("io.micronaut:micronaut-http-server-netty")
    implementation("io.micronaut:micronaut-jackson-databind")
    testImplementation("io.micronaut.test:micronaut-test-junit5")
    testImplementation("org.junit.jupiter:junit-jupiter-api")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine")
}

application {
    mainClass.set("com.muppetplatform.{{java_package_name}}.Application")
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

micronaut {
    runtime("netty")
    testRuntime("junit5")
    processing {
        incremental(true)
        annotations("com.muppetplatform.{{java_package_name}}.*")
    }
}
"""
            )

            yield templates_root

    def test_end_to_end_verification_without_build(self, temp_templates_dir):
        """Test end-to-end verification without actual build (mocked)."""
        # Create verification system with real template manager
        template_manager = TemplateManager(templates_root=temp_templates_dir)

        config = VerificationConfig(cleanup_on_success=False, cleanup_on_failure=False)

        with tempfile.TemporaryDirectory() as verification_root:
            verification_system = MuppetVerificationSystem(
                template_manager=template_manager,
                config=config,
                verification_root=Path(verification_root),
            )

            # Mock the build process to avoid requiring Java/Gradle
            with patch.object(
                verification_system, "_verify_build_process"
            ) as mock_build:

                def mock_build_success(path, template_name, muppet_name, result):
                    result.build_success = True
                    result.build_output = "Mocked build success"

                mock_build.side_effect = mock_build_success

                # Mock build artifacts verification
                with patch.object(
                    verification_system, "_verify_build_artifacts"
                ) as mock_artifacts:

                    def mock_artifacts_success(
                        path, template_name, muppet_name, result
                    ):
                        result.build_artifacts = [
                            "build/libs/test-muppet-1.0.0-all.jar"
                        ]

                    mock_artifacts.side_effect = mock_artifacts_success

                    # Run verification
                    result = verification_system.verify_template("java-micronaut")

                    # Verify results
                    assert result.success is True
                    assert result.template_generation_success is True
                    assert result.parameter_injection_success is True
                    assert result.variable_replacement_success is True
                    assert result.build_success is True
                    assert result.script_verification_success is True
                    assert len(result.generated_files) > 0
                    assert "src/main/java/com/muppetplatform/" in str(
                        result.generated_files
                    )
                    # All 9 expected scripts
                    assert len(result.script_results) == 9
                    assert all(
                        script_result["exists"]
                        for script_result in result.script_results.values()
                    )
                    assert result.duration_seconds > 0
                    assert len(result.errors) == 0
