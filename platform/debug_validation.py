#!/usr/bin/env python3

"""
Debug script to test the template validation logic
"""

from pathlib import Path
import yaml

def debug_validation():
    print("🔍 Debugging template validation logic...")
    
    # Simulate the validation logic
    template_path = Path("../templates/node-express")
    config_path = template_path / "template.yaml"
    
    print(f"Template path: {template_path}")
    print(f"Template path exists: {template_path.exists()}")
    print(f"Config path: {config_path}")
    print(f"Config path exists: {config_path.exists()}")
    
    if not config_path.exists():
        print("❌ Config file not found")
        return
    
    # Load config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    template_files_config = config.get("template_files", {})
    core_files = template_files_config.get("core", [])
    
    print(f"\nCore files from template.yaml: {core_files}")
    
    # Test the validation logic
    missing_core_files = []
    for file_path in core_files:
        print(f"\n🔍 Checking core file: {file_path}")
        
        full_path = template_path / file_path
        print(f"  Full path: {full_path}")
        print(f"  Full path exists: {full_path.exists()}")
        
        if not full_path.exists():
            print("  ❌ Direct path check failed, trying glob pattern...")
            
            # Test the complex glob logic
            matching_files = []
            for p in template_path.rglob("*"):
                if file_path.rstrip("/") in str(p):
                    matching_files.append(p)
                    print(f"    Found matching file: {p}")
            
            if not matching_files:
                print(f"  ❌ No matching files found for pattern: {file_path}")
                missing_core_files.append(file_path)
            else:
                print(f"  ✅ Found {len(matching_files)} matching files")
        else:
            print("  ✅ Direct path check passed")
    
    print(f"\nMissing core files: {missing_core_files}")
    
    if missing_core_files:
        print(f"❌ Validation would fail with: Missing core template files: {', '.join(missing_core_files)}")
    else:
        print("✅ All core files found, validation would pass")

if __name__ == "__main__":
    debug_validation()