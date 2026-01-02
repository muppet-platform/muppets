#!/usr/bin/env python3

"""
Debug script to test node-express template validation
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from managers.template_manager import TemplateManager

def main():
    print("🔍 Debugging node-express template validation...")
    
    # Initialize template manager
    template_manager = TemplateManager()
    
    print(f"Templates root: {template_manager.templates_root}")
    print(f"Templates root exists: {template_manager.templates_root.exists()}")
    
    # Check node-express template directory
    node_template_dir = template_manager.templates_root / "node-express"
    print(f"Node template dir: {node_template_dir}")
    print(f"Node template dir exists: {node_template_dir.exists()}")
    
    if node_template_dir.exists():
        print("\nFiles in node-express template:")
        for file in sorted(node_template_dir.rglob("*")):
            if file.is_file():
                print(f"  {file.relative_to(node_template_dir)}")
    
    # Try to discover templates
    print("\n🔍 Discovering templates...")
    try:
        templates = template_manager.discover_templates()
        print(f"Found {len(templates)} templates:")
        for template in templates:
            print(f"  - {template.name} v{template.version}")
    except Exception as e:
        print(f"❌ Template discovery failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Try to get node-express template specifically
    print("\n🔍 Getting node-express template...")
    try:
        node_template = template_manager.get_template("node-express")
        if node_template:
            print(f"✅ Found node-express template: {node_template.name}")
        else:
            print("❌ node-express template not found")
    except Exception as e:
        print(f"❌ Failed to get node-express template: {e}")
        import traceback
        traceback.print_exc()
    
    # Try to validate template
    print("\n🔍 Testing template validation...")
    try:
        # This should trigger the validation that's failing
        result = template_manager.generate_code(
            template_name="node-express",
            context={
                "muppet_name": "test-muppet",
                "aws_region": "us-west-2",
                "environment": "development"
            }
        )
        print("✅ Template validation passed")
    except Exception as e:
        print(f"❌ Template validation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()