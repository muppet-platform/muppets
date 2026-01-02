#!/usr/bin/env python3

"""
Test script to verify node-express template validation works
"""

import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up environment
os.environ.setdefault("GITHUB_TOKEN", "test-token")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

def test_node_express_template_validation():
    """Test that node-express template validation passes"""
    from managers.template_manager import TemplateManager
    
    # Initialize template manager with the actual templates directory
    templates_root = Path(__file__).parent.parent / "templates"
    template_manager = TemplateManager(templates_root=templates_root)
    
    # Discover templates
    templates = template_manager.discover_templates()
    template_names = [t.name for t in templates]
    
    print(f"Discovered templates: {template_names}")
    
    # Check if node-express template exists
    assert "node-express" in template_names, f"node-express template not found. Available: {template_names}"
    
    # Validate node-express template
    try:
        result = template_manager.validate_template("node-express")
        print("✅ node-express template validation passed")
        assert result is True
    except Exception as e:
        print(f"❌ node-express template validation failed: {e}")
        raise

def test_node_express_template_generation():
    """Test that node-express template code generation works"""
    from managers.template_manager import TemplateManager, GenerationContext
    
    # Initialize template manager
    templates_root = Path(__file__).parent.parent / "templates"
    template_manager = TemplateManager(templates_root=templates_root)
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test-node-muppet"
        
        # Create generation context
        context = GenerationContext(
            template_name="node-express",
            muppet_name="test-node-muppet",
            output_path=output_path,
            aws_region="us-west-2",
            environment="development"
        )
        
        # Generate code
        try:
            result_path = template_manager.generate_code(context)
            print("✅ node-express template code generation passed")
            
            # Check that some expected files were generated
            expected_files = [
                "package.json",
                "tsconfig.json",
                ".env.local",
                "src/index.ts"
            ]
            
            for expected_file in expected_files:
                file_path = result_path / expected_file
                if file_path.exists():
                    print(f"  ✅ Generated: {expected_file}")
                else:
                    print(f"  ❌ Missing: {expected_file}")
            
            # List all generated files
            print("\nAll generated files:")
            for file in sorted(result_path.rglob("*")):
                if file.is_file():
                    print(f"  {file.relative_to(result_path)}")
                    
        except Exception as e:
            print(f"❌ node-express template code generation failed: {e}")
            raise

if __name__ == "__main__":
    print("🧪 Testing node-express template...")
    
    try:
        test_node_express_template_validation()
        test_node_express_template_generation()
        print("\n✅ All node-express template tests passed!")
    except Exception as e:
        print(f"\n❌ node-express template tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)