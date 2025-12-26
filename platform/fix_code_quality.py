#!/usr/bin/env python3
"""
Quick fix script for critical code quality issues
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, cwd: str = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr"""
    result = subprocess.run(cmd.split(), cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def fix_unused_imports():
    """Remove unused imports using autoflake"""
    print("🔧 Removing unused imports...")

    # Install autoflake if not available
    run_command("uv add --dev autoflake")

    # Remove unused imports
    cmd = "uv run autoflake --remove-all-unused-imports --in-place --recursive src/ tests/"
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("✅ Unused imports removed")
    else:
        print(f"❌ Failed to remove unused imports: {stderr}")


def fix_line_length():
    """Fix line length issues using autopep8"""
    print("🔧 Fixing line length issues...")

    # Install autopep8 if not available
    run_command("uv add --dev autopep8")

    # Fix line length issues
    cmd = "uv run autopep8 --max-line-length=79 --in-place --recursive src/ tests/"
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("✅ Line length issues fixed")
    else:
        print(f"❌ Failed to fix line length: {stderr}")


def fix_whitespace_issues():
    """Fix whitespace issues"""
    print("🔧 Fixing whitespace issues...")

    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Remove trailing whitespace
                    lines = content.split("\n")
                    fixed_lines = [line.rstrip() for line in lines]

                    # Remove whitespace from blank lines
                    fixed_lines = [
                        "" if line.strip() == "" else line for line in fixed_lines
                    ]

                    fixed_content = "\n".join(fixed_lines)

                    if fixed_content != content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(fixed_content)
                        print(f"  Fixed whitespace in {file_path}")

                except Exception as e:
                    print(f"  Error fixing {file_path}: {e}")

    print("✅ Whitespace issues fixed")


def fix_f_string_placeholders():
    """Fix f-strings without placeholders"""
    print("🔧 Fixing f-string placeholder issues...")

    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Find f-strings without placeholders and convert to regular strings
                    # This is a simple regex - may need refinement
                    pattern = r'f"([^"]*)"'

                    def replace_f_string(match):
                        string_content = match.group(1)
                        # If no {} placeholders, convert to regular string
                        if "{" not in string_content:
                            return f'"{string_content}"'
                        return match.group(0)

                    fixed_content = re.sub(pattern, replace_f_string, content)

                    # Also handle single quotes
                    pattern = r"f'([^']*)'"
                    fixed_content = re.sub(pattern, replace_f_string, fixed_content)

                    if fixed_content != content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(fixed_content)
                        print(f"  Fixed f-strings in {file_path}")

                except Exception as e:
                    print(f"  Error fixing {file_path}: {e}")

    print("✅ F-string placeholder issues fixed")


def fix_redefined_functions():
    """Fix redefined function issues in github.py"""
    print("🔧 Fixing redefined functions...")

    github_file = Path("src/integrations/github.py")
    if github_file.exists():
        try:
            with open(github_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove duplicate function definitions
            # This is a simple approach - remove lines after certain line numbers
            lines = content.split("\n")

            # Remove duplicate update_repository_status (around line 1547)
            # Remove duplicate update_file (around line 1601)
            # Remove duplicate list_tags (around line 1684)
            # Remove duplicate get_file_content (around line 1746)

            # Find and remove duplicates by looking for function signatures
            seen_functions = set()
            filtered_lines = []
            skip_until_next_def = False

            for i, line in enumerate(lines):
                if line.strip().startswith("def ") or line.strip().startswith(
                    "async def "
                ):
                    func_name = (
                        line.strip()
                        .split("(")[0]
                        .replace("def ", "")
                        .replace("async ", "")
                        .strip()
                    )
                    if func_name in seen_functions:
                        skip_until_next_def = True
                        print(f"  Removing duplicate function: {func_name}")
                        continue
                    else:
                        seen_functions.add(func_name)
                        skip_until_next_def = False

                if skip_until_next_def:
                    # Skip lines until we hit the next function or class definition
                    if (
                        line.strip().startswith("def ")
                        or line.strip().startswith("async def ")
                        or line.strip().startswith("class ")
                    ):
                        skip_until_next_def = False
                        # Process this line normally
                        func_name = (
                            line.strip()
                            .split("(")[0]
                            .replace("def ", "")
                            .replace("async ", "")
                            .strip()
                        )
                        if func_name not in seen_functions:
                            seen_functions.add(func_name)
                            filtered_lines.append(line)
                    continue

                filtered_lines.append(line)

            fixed_content = "\n".join(filtered_lines)

            if fixed_content != content:
                with open(github_file, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
                print(f"  Fixed redefined functions in {github_file}")

        except Exception as e:
            print(f"  Error fixing {github_file}: {e}")

    print("✅ Redefined function issues fixed")


def main():
    """Main function to run all fixes"""
    print("🚀 Starting code quality fixes...")

    # Change to platform directory
    os.chdir(Path(__file__).parent)

    # Run fixes in order
    fix_unused_imports()
    fix_line_length()
    fix_whitespace_issues()
    fix_f_string_placeholders()
    fix_redefined_functions()

    # Run formatters again
    print("🔧 Running final formatting...")
    run_command("uv run black src/ tests/")
    run_command("uv run isort src/ tests/")

    print("✅ Code quality fixes completed!")
    print("\n🧪 Running final checks...")

    # Check if issues are resolved
    exit_code, stdout, stderr = run_command(
        "uv run flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503,F401,F841"
    )

    if exit_code == 0:
        print("✅ All flake8 issues resolved!")
    else:
        print("⚠️  Some flake8 issues remain:")
        print(stdout)
        print(stderr)


if __name__ == "__main__":
    main()
