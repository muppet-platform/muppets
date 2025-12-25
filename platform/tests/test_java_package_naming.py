"""
Tests for Java package name validation and conversion.

This module tests the _to_java_package_name method in GenerationContext
to ensure muppet names are correctly converted to valid Java package names.
"""

from pathlib import Path

import pytest

from src.managers.template_manager import GenerationContext


class TestJavaPackageNaming:
    """Test Java package name conversion functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a GenerationContext to test the method
        self.context = GenerationContext(
            muppet_name="test",
            template_name="java-micronaut",
            parameters={},
            output_path=Path("/tmp/test"),
        )

    def test_basic_name_conversion(self):
        """Test basic muppet name to Java package name conversion."""
        # Simple lowercase name
        assert self.context._to_java_package_name("myservice") == "myservice"

        # Mixed case conversion
        assert self.context._to_java_package_name("MyService") == "myservice"
        assert self.context._to_java_package_name("MY_SERVICE") == "my_service"

    def test_hyphen_replacement(self):
        """Test that hyphens are replaced with underscores."""
        assert self.context._to_java_package_name("my-service") == "my_service"
        assert (
            self.context._to_java_package_name("user-auth-service")
            == "user_auth_service"
        )
        assert self.context._to_java_package_name("api-gateway-v2") == "api_gateway_v2"

    def test_special_character_removal(self):
        """Test that special characters are replaced with underscores."""
        assert self.context._to_java_package_name("my@service") == "my_service"
        assert self.context._to_java_package_name("service#1") == "service_1"
        assert self.context._to_java_package_name("api.gateway") == "api_gateway"
        assert (
            self.context._to_java_package_name("user$auth%service")
            == "user_auth_service"
        )
        assert self.context._to_java_package_name("service(v1)") == "service_v1"

    def test_multiple_consecutive_underscores(self):
        """Test that multiple consecutive underscores are cleaned up."""
        assert self.context._to_java_package_name("my--service") == "my_service"
        assert self.context._to_java_package_name("api___gateway") == "api_gateway"
        assert self.context._to_java_package_name("service@#$%auth") == "service_auth"

    def test_leading_trailing_underscores(self):
        """Test that leading and trailing underscores are removed."""
        assert self.context._to_java_package_name("-service-") == "service"
        assert self.context._to_java_package_name("@service#") == "service"
        assert self.context._to_java_package_name("___service___") == "service"

    def test_digit_prefix_handling(self):
        """Test that names starting with digits get 'pkg_' prefix."""
        assert self.context._to_java_package_name("123service") == "pkg_123service"
        assert self.context._to_java_package_name("2fa-auth") == "pkg_2fa_auth"
        assert (
            self.context._to_java_package_name("9-api-gateway") == "pkg_9_api_gateway"
        )

    def test_java_keyword_handling(self):
        """Test that Java keywords get underscore suffix."""
        # Test some common Java keywords
        assert self.context._to_java_package_name("class") == "class_"
        assert self.context._to_java_package_name("interface") == "interface_"
        assert self.context._to_java_package_name("public") == "public_"
        assert self.context._to_java_package_name("private") == "private_"
        assert self.context._to_java_package_name("static") == "static_"
        assert self.context._to_java_package_name("final") == "final_"
        assert self.context._to_java_package_name("return") == "return_"
        assert self.context._to_java_package_name("void") == "void_"
        assert self.context._to_java_package_name("new") == "new_"
        assert self.context._to_java_package_name("import") == "import_"

    def test_empty_and_whitespace_handling(self):
        """Test handling of empty strings and whitespace."""
        # Empty string should raise ValueError
        with pytest.raises(ValueError, match="Muppet name cannot be empty"):
            self.context._to_java_package_name("")

        # Whitespace-only should raise ValueError
        with pytest.raises(ValueError, match="Muppet name cannot be empty"):
            self.context._to_java_package_name("   ")

        # Leading/trailing whitespace should be stripped
        assert self.context._to_java_package_name("  myservice  ") == "myservice"

    def test_all_special_characters_fallback(self):
        """Test fallback when name becomes empty after cleaning."""
        # All special characters should result in 'muppet'
        assert self.context._to_java_package_name("@#$%^&*()") == "muppet"
        assert self.context._to_java_package_name("---") == "muppet"
        assert self.context._to_java_package_name("!!!") == "muppet"

    def test_length_validation(self):
        """Test that excessively long names are truncated."""
        # Create a very long name
        long_name = "a" * 60
        result = self.context._to_java_package_name(long_name)
        assert len(result) <= 50
        assert result == "a" * 50

        # Test truncation with underscores at the end
        long_name_with_underscores = "a" * 45 + "_____"
        result = self.context._to_java_package_name(long_name_with_underscores)
        assert len(result) <= 50
        assert not result.endswith("_")

    def test_complex_real_world_examples(self):
        """Test complex real-world muppet name examples."""
        # Common service naming patterns
        assert (
            self.context._to_java_package_name("user-authentication-service")
            == "user_authentication_service"
        )
        assert self.context._to_java_package_name("api-gateway-v2") == "api_gateway_v2"
        assert (
            self.context._to_java_package_name("payment-processor-3.0")
            == "payment_processor_3_0"
        )
        assert (
            self.context._to_java_package_name("data-sync-worker") == "data_sync_worker"
        )

        # Names with mixed issues
        assert (
            self.context._to_java_package_name("2FA-Auth@Service!")
            == "pkg_2fa_auth_service"
        )
        assert (
            self.context._to_java_package_name("My-Super#Cool$Service")
            == "my_super_cool_service"
        )

        # Edge cases
        assert (
            self.context._to_java_package_name("class-service") == "class_service"
        )  # Not a keyword after transformation
        assert (
            self.context._to_java_package_name("new-api") == "new_api"
        )  # Not a keyword after transformation

    def test_generation_context_integration(self):
        """Test that Java package names are correctly integrated in GenerationContext."""
        context = GenerationContext(
            muppet_name="my-test-service",
            template_name="java-micronaut",
            parameters={},
            output_path=Path("/tmp/test"),
        )

        variables = context.get_all_variables()
        assert "java_package_name" in variables
        assert variables["java_package_name"] == "my_test_service"

    def test_non_java_template_no_package_name(self):
        """Test that non-Java templates don't get java_package_name variable."""
        context = GenerationContext(
            muppet_name="my-test-service",
            template_name="python-fastapi",  # Not java-micronaut
            parameters={},
            output_path=Path("/tmp/test"),
        )

        variables = context.get_all_variables()
        assert "java_package_name" not in variables

    def test_unicode_and_international_characters(self):
        """Test handling of Unicode and international characters."""
        # Unicode characters should be replaced with underscores
        assert self.context._to_java_package_name("café-service") == "caf_service"
        assert self.context._to_java_package_name("naïve-api") == "na_ve_api"
        assert self.context._to_java_package_name("résumé-parser") == "r_sum_parser"

        # Emoji and other Unicode
        assert self.context._to_java_package_name("🚀rocket-service") == "rocket_service"
        assert self.context._to_java_package_name("service-✨") == "service"

    def test_case_sensitivity_edge_cases(self):
        """Test case sensitivity edge cases."""
        # Mixed case with special characters
        assert self.context._to_java_package_name("MyAPI-Service") == "myapi_service"
        assert self.context._to_java_package_name("HTTPSProxy") == "httpsproxy"
        assert self.context._to_java_package_name("XMLParser2.0") == "xmlparser2_0"

    def test_keyword_with_modifications(self):
        """Test keywords that become non-keywords after modification."""
        # These should NOT get underscore suffix because they're not keywords after processing
        assert self.context._to_java_package_name("class-service") == "class_service"
        assert self.context._to_java_package_name("new-api") == "new_api"
        assert self.context._to_java_package_name("import-tool") == "import_tool"

        # But pure keywords should still get suffix
        assert self.context._to_java_package_name("class") == "class_"
        assert self.context._to_java_package_name("new") == "new_"
        assert self.context._to_java_package_name("import") == "import_"


class TestJavaPackageNamingPropertyBased:
    """Property-based tests for Java package naming."""

    def setup_method(self):
        """Set up test fixtures."""
        self.context = GenerationContext(
            muppet_name="test",
            template_name="java-micronaut",
            parameters={},
            output_path=Path("/tmp/test"),
        )

    def test_result_always_valid_java_identifier(self):
        """Property: Result should always be a valid Java package identifier."""
        test_names = [
            "simple",
            "with-hyphens",
            "with_underscores",
            "MixedCase",
            "123numeric",
            "special@chars#here",
            "class",
            "interface",
            "very-long-name-that-exceeds-reasonable-limits-for-package-names",
            "@#$%^&*()",
            "",
            "   ",
            "café-service",
            "🚀rocket",
        ]

        for name in test_names:
            try:
                if not name.strip():
                    # Empty names should raise ValueError
                    with pytest.raises(ValueError):
                        self.context._to_java_package_name(name)
                    continue

                result = self.context._to_java_package_name(name)

                # Validate result properties
                assert result, f"Result should not be empty for input: {name}"
                assert result[
                    0
                ].isalpha(), (
                    f"Result should start with letter for input: {name}, got: {result}"
                )
                assert all(
                    c.isalnum() or c == "_" for c in result
                ), f"Result should only contain alphanumeric and underscore for input: {name}, got: {result}"
                assert not result.startswith(
                    "_"
                ), f"Result should not start with underscore for input: {name}, got: {result}"
                assert not result.endswith("_") or result in [
                    "class_",
                    "interface_",
                    "public_",
                    "private_",
                    "static_",
                    "final_",
                    "return_",
                    "void_",
                    "new_",
                    "import_",
                    "package_",
                    "abstract_",
                    "assert_",
                    "boolean_",
                    "break_",
                    "byte_",
                    "case_",
                    "catch_",
                    "char_",
                    "const_",
                    "continue_",
                    "default_",
                    "do_",
                    "double_",
                    "else_",
                    "enum_",
                    "extends_",
                    "finally_",
                    "float_",
                    "for_",
                    "goto_",
                    "if_",
                    "implements_",
                    "instanceof_",
                    "int_",
                    "long_",
                    "native_",
                    "protected_",
                    "short_",
                    "strictfp_",
                    "super_",
                    "switch_",
                    "synchronized_",
                    "this_",
                    "throw_",
                    "throws_",
                    "transient_",
                    "try_",
                    "volatile_",
                    "while_",
                ], f"Result should not end with underscore unless it's a keyword for input: {name}, got: {result}"
                assert (
                    len(result) <= 50
                ), f"Result should not exceed 50 characters for input: {name}, got: {result}"
                assert (
                    result.islower()
                ), f"Result should be lowercase for input: {name}, got: {result}"

            except ValueError as e:
                # Only empty/whitespace names should raise ValueError
                assert (
                    not name.strip()
                ), f"Only empty names should raise ValueError, but got error for: {name}, error: {e}"
