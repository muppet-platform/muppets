#!/usr/bin/env python3
"""
Debug script to test .env.local validation for both templates
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from managers.template_manager import TemplateManager

def debug_template_validation(template_name):
    print(f"\n=== Debugging {template_name} template validation ===")
    
    template_manager = TemplateManager()
    
    # Get template metadata
    templates = template_manager.discover_templates()
    template = None
    for t in templates:
        if t.name == template_name:
            template = t
            break
    
    if not template:
        print(f"❌ Template {template_name} not found")
        return
    
    print(f"✅ Template found: {template.name}")
    print(f"📁 Template path: {template.template_path}")
    
    # Check if .env.local exists
    env_local_path = template.template_path / ".env.local"
    print(f"🔍 Checking for .env.local at: {env_local_path}")
    print(f"📄 .env.local exists: {env_local_path.exists()}")
    
    if env_local_path.exists():
        print(f"📏 File size: {env_local_path.stat().st_size} bytes")
        with open(env_local_path, 'r') as f:
            content = f.read()
            print(f"📝 Content preview: {content[:100]}...")
    
    # Check template.yaml core files
    import yaml
    template_yaml_path = template.template_path / "template.yaml"
    if template_yaml_path.exists():
        with open(template_yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        core_files = config.get("template_files", {}).get("core", [])
        print(f"📋 Core files in template.yaml: {len(core_files)} files")
        
        env_files = [f for f in core_files if 'env' in f.lower()]
        print(f"🔧 Environment files in core: {env_files}")
    
    # Test validation
    try:
        template_manager.validate_template(template_name)
        print("✅ Template validation PASSED")
    except Exception as e:
        print(f"❌ Template validation FAILED: {e}")
        
        # Let's manually check the validation logic
        print("\n🔍 Manual validation check:")
        for file_path in core_files:
            if 'env' in file_path.lower():
                full_path = template.template_path / file_path
                print(f"  Checking: {file_path}")
                print(f"    Full path: {full_path}")
                print(f"    Exists: {full_path.exists()}")
                
                # Check if it's a direct file
                if full_path.exists():
                    print(f"    ✅ Direct file match")
                    continue

                # Check if it's a directory
                if full_path.is_dir():
                    print(f"    ✅ Directory match")
                    continue

                # For files, check if any file in the template matches the pattern
                found_match = False
                for template_file in template.template_path.rglob("*"):
                    if template_file.is_file():
                        rel_path = template_file.relative_to(template.template_path)
                        if str(rel_path) == file_path or file_path.rstrip("/") in str(rel_path):
                            found_match = True
                            print(f"    ✅ Pattern match: {rel_path}")
                            break

                if not found_match:
                    print(f"    ❌ No match found")

if __name__ == "__main__":
    debug_template_validation("java-micronaut")
    debug_template_validation("node-express")