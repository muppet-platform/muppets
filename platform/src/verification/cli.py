#!/usr/bin/env python3
"""
CLI for Muppet Instantiation Verification System

This script provides a command-line interface for verifying muppet templates
by creating test instances and validating all aspects of the generation process.
"""

import argparse
import json
import sys
from pathlib import Path

from ..logging_config import get_logger
from ..managers.template_manager import TemplateManager
from .muppet_verification import MuppetVerificationSystem, VerificationConfig

logger = get_logger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    import logging

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def print_verification_result(result, verbose: bool = False) -> None:
    """Print verification result in a human-readable format."""
    print(f"\n{'='*60}")
    print(f"Verification Result: {result.muppet_name}")
    print(f"{'='*60}")
    print(f"Template: {result.template_name}")
    print(f"Success: {'✅ PASS' if result.success else '❌ FAIL'}")
    print(f"Duration: {result.duration_seconds:.2f} seconds")
    print(f"Workspace: {result.verification_path}")

    print("\nStep Results:")
    print(
        f"  Template Generation: {'✅' if result.template_generation_success else '❌'}"
    )
    print(
        f"  Parameter Injection: {'✅' if result.parameter_injection_success else '❌'}"
    )
    print(
        f"  Variable Replacement: {'✅' if result.variable_replacement_success else '❌'}"
    )
    print(f"  Build Process: {'✅' if result.build_success else '❌'}")
    print(
        f"  Script Verification: {'✅' if result.script_verification_success else '❌'}"
    )

    if result.generated_files:
        print(f"\nGenerated Files ({len(result.generated_files)}):")
        for file_path in sorted(result.generated_files)[:10]:  # Show first 10
            print(f"  - {file_path}")
        if len(result.generated_files) > 10:
            print(f"  ... and {len(result.generated_files) - 10} more files")

    if result.build_artifacts:
        print("\nBuild Artifacts:")
        for artifact in result.build_artifacts:
            print(f"  - {artifact}")

    if result.script_results:
        print("\nScript Verification:")
        for script_name, script_result in result.script_results.items():
            # Basic status
            basic_status = (
                "✅"
                if (
                    script_result["exists"]
                    and script_result["executable"]
                    and script_result["variables_replaced"]
                    and not script_result["errors"]
                )
                else "❌"
            )

            # Functional test status
            func_status = ""
            if script_result["functional_test_passed"] is True:
                func_status = " (✅ functional)"
            elif script_result["functional_test_passed"] is False:
                func_status = " (❌ functional)"
            elif script_result["functional_test_passed"] is None:
                func_status = " (⚪ not tested)"

            print(f"  {basic_status} {script_name}{func_status}")

            if verbose and script_result["errors"]:
                for error in script_result["errors"]:
                    print(f"      Error: {error}")

            if verbose and script_result["functional_test_output"]:
                print("      Functional test output:")
                for line in script_result["functional_test_output"].split("\n")[
                    :5
                ]:  # Show first 5 lines
                    print(f"        {line}")
                if len(script_result["functional_test_output"].split("\n")) > 5:
                    print("        ... (truncated)")

    if result.injected_parameters:
        print("\nInjected Parameters:")
        for param, value in result.injected_parameters.items():
            print(f"  - {param}: {value}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  ❌ {error}")

    if verbose and result.build_output:
        print("\nBuild Output:")
        print("-" * 40)
        print(result.build_output)
        print("-" * 40)


def verify_single_template(args) -> int:
    """Verify a single template."""
    print(f"🧪 Verifying template: {args.template}")

    try:
        # Create verification system
        template_manager = TemplateManager()

        config = VerificationConfig()
        if args.no_cleanup:
            config.cleanup_on_success = False
            config.cleanup_on_failure = False

        if hasattr(args, "functional_tests") and args.functional_tests:
            config.enable_functional_script_testing = True

        if args.custom_params:
            try:
                custom_params = json.loads(args.custom_params)
                config.test_parameters.update(custom_params)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in custom parameters: {e}")
                return 1

        verification_system = MuppetVerificationSystem(
            template_manager=template_manager, config=config
        )

        # Run verification
        result = verification_system.verify_template(args.template)

        # Print results
        print_verification_result(result, verbose=args.verbose)

        # Save results if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            print(f"\n📄 Results saved to: {output_path}")

        return 0 if result.success else 1

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def verify_all_templates(args) -> int:
    """Verify all available templates."""
    print("🧪 Verifying all templates...")

    try:
        # Create verification system
        template_manager = TemplateManager()

        config = VerificationConfig()
        if args.no_cleanup:
            config.cleanup_on_success = False
            config.cleanup_on_failure = False

        if hasattr(args, "functional_tests") and args.functional_tests:
            config.enable_functional_script_testing = True

        verification_system = MuppetVerificationSystem(
            template_manager=template_manager, config=config
        )

        # Run verification for all templates
        results = verification_system.verify_all_templates()

        # Print summary
        print(f"\n{'='*60}")
        print("Verification Summary")
        print(f"{'='*60}")

        total_templates = len(results)
        successful_templates = sum(1 for result in results.values() if result.success)
        failed_templates = total_templates - successful_templates

        print(f"Total Templates: {total_templates}")
        print(f"Successful: {successful_templates} ✅")
        print(f"Failed: {failed_templates} ❌")

        # Print individual results
        for template_name, result in results.items():
            status = "✅ PASS" if result.success else "❌ FAIL"
            duration = f"{result.duration_seconds:.2f}s"
            print(f"  {template_name}: {status} ({duration})")

            if not result.success and not args.verbose:
                # Show first error for failed templates
                if result.errors:
                    print(f"    Error: {result.errors[0]}")

        # Print detailed results if verbose
        if args.verbose:
            for template_name, result in results.items():
                print_verification_result(result, verbose=True)

        # Save results if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            summary_data = {
                "summary": {
                    "total_templates": total_templates,
                    "successful_templates": successful_templates,
                    "failed_templates": failed_templates,
                    "timestamp": results[list(results.keys())[0]].to_dict()["timestamp"]
                    if results
                    else None,
                },
                "results": {name: result.to_dict() for name, result in results.items()},
            }

            with open(output_path, "w") as f:
                json.dump(summary_data, f, indent=2)
            print(f"\n📄 Results saved to: {output_path}")

        return 0 if failed_templates == 0 else 1

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def list_templates(args) -> int:
    """List available templates."""
    try:
        template_manager = TemplateManager()
        templates = template_manager.discover_templates()

        if not templates:
            print("No templates found.")
            return 0

        print(f"Available Templates ({len(templates)}):")
        print("-" * 40)

        for template in templates:
            print(f"Name: {template.name}")
            print(f"  Version: {template.version}")
            print(f"  Language: {template.language}")
            print(f"  Framework: {template.framework}")
            print(f"  Description: {template.description}")
            if args.verbose:
                print(f"  Required Variables: {', '.join(template.required_variables)}")
                print(f"  Terraform Modules: {', '.join(template.terraform_modules)}")
                print(f"  Supported Features: {', '.join(template.supported_features)}")
            print()

        return 0

    except Exception as e:
        print(f"❌ Failed to list templates: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Muppet Instantiation Verification System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify a specific template
  python -m src.verification.cli verify java-micronaut

  # Verify all templates
  python -m src.verification.cli verify-all

  # Verify with functional script testing enabled
  python -m src.verification.cli verify java-micronaut --functional-tests

  # Verify with custom parameters
  python -m src.verification.cli verify java-micronaut --custom-params '{"environment": "test"}'

  # List available templates
  python -m src.verification.cli list

  # Verify and save results to file
  python -m src.verification.cli verify java-micronaut --output results.json
        """,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Verify single template command
    verify_parser = subparsers.add_parser("verify", help="Verify a specific template")
    verify_parser.add_argument("template", help="Template name to verify")
    verify_parser.add_argument(
        "--custom-params", help="Custom parameters as JSON string"
    )
    verify_parser.add_argument(
        "--output", "-o", help="Output file for results (JSON format)"
    )
    verify_parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Do not cleanup verification workspace",
    )
    verify_parser.add_argument(
        "--functional-tests",
        action="store_true",
        help="Enable functional testing of scripts (executes safe scripts)",
    )

    # Verify all templates command
    verify_all_parser = subparsers.add_parser(
        "verify-all", help="Verify all available templates"
    )
    verify_all_parser.add_argument(
        "--output", "-o", help="Output file for results (JSON format)"
    )
    verify_all_parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Do not cleanup verification workspaces",
    )
    verify_all_parser.add_argument(
        "--functional-tests",
        action="store_true",
        help="Enable functional testing of scripts (executes safe scripts)",
    )

    # List templates command
    list_parser = subparsers.add_parser("list", help="List available templates")

    args = parser.parse_args()

    # Set up logging
    setup_logging(verbose=args.verbose)

    # Execute command
    if args.command == "verify":
        return verify_single_template(args)
    elif args.command == "verify-all":
        return verify_all_templates(args)
    elif args.command == "list":
        return list_templates(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
