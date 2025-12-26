#!/usr/bin/env python3
"""
Debug script to check template discovery
"""

import sys

sys.path.append("src")

from src.managers.template_manager import TemplateManager


def main():
    manager = TemplateManager()

    print(f"Templates root: {manager.templates_root}")
    print(f"Templates root exists: {manager.templates_root.exists()}")

    if manager.templates_root.exists():
        print("Contents of templates root:")
        for item in manager.templates_root.iterdir():
            print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

    print("\nDiscovering templates...")
    templates = manager.discover_templates()
    print(f"Found {len(templates)} templates:")

    for template in templates:
        print(f"  - {template.name} v{template.version}")


if __name__ == "__main__":
    main()
