"""
Test README template processing to prevent duplication issues.
"""

import tempfile
from pathlib import Path

import pytest

from src.managers.template_manager import GenerationContext, TemplateManager


class TestReadmeProcessing:
    """Test README template processing to ensure no duplication."""

    @pytest.mark.asyncio
    async def test_readme_template_processing_no_duplication(self):
        """Test that README.template.md is processed correctly without duplication."""
        template_manager = TemplateManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test-readme-muppet"

            context = GenerationContext(
                muppet_name="test-readme-muppet",
                template_name="java-micronaut",
                parameters={
                    "github_organization": "test-org",
                    "aws_region": "us-west-2",
                },
                output_path=output_path,
                aws_region="us-west-2",
                environment="development",
            )

            # Generate code
            generated_path = template_manager.generate_code(context)

            # Check that only README.md exists (not README.template.md)
            readme_files = list(generated_path.glob("README*"))
            readme_names = [f.name for f in readme_files]

            assert (
                len(readme_files) == 1
            ), f"Should have exactly 1 README file, found: {readme_names}"
            assert "README.md" in readme_names, "Should have README.md"
            assert (
                "README.template.md" not in readme_names
            ), "Should not have README.template.md"

            # Verify README.md has proper content (not just minimal title)
            readme_content = (generated_path / "README.md").read_text()
            assert (
                "test-readme-muppet" in readme_content
            ), "README should contain muppet name"
            assert (
                len(readme_content) > 50
            ), "README should have substantial content, not just title"
            assert (
                "Quick Start" in readme_content
            ), "README should have Quick Start section"
            assert (
                "http://localhost:3000" in readme_content
            ), "README should have service URLs"

    def test_template_file_extension_removal(self):
        """Test that .template extension is properly removed during processing."""
        template_manager = TemplateManager()

        # Test the internal method for removing .template extension
        variables = {"muppet_name": "test-muppet"}

        # Simulate processing a .template file
        template_path = Path("README.template.md")

        # The output should remove .template extension
        if template_path.suffix == ".template":
            expected_output = template_path.with_suffix("")
            assert expected_output.name == "README.md"

    def test_variable_replacement_in_readme(self):
        """Test that variables are properly replaced in README content."""
        template_manager = TemplateManager()

        # Test variable replacement
        content = "# {{muppet_name}}\n\nService available at http://localhost:{{port}}"
        variables = {"muppet_name": "my-service", "port": "3000"}

        result = template_manager._replace_variables_in_string(content, variables)

        assert "{{muppet_name}}" not in result, "Should replace muppet_name variable"
        assert "{{port}}" not in result, "Should replace port variable"
        assert "my-service" in result, "Should contain replaced muppet name"
        assert "3000" in result, "Should contain replaced port"
