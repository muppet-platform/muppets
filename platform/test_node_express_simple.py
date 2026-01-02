#!/usr/bin/env python3

"""
Simple test to reproduce the node-express template validation issue
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up environment
os.environ.setdefault("GITHUB_TOKEN", "test-token")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

def test_node_express_validation():
    """Test node-express template validation"""
    print("🔍 Testing node-express template validation...")
    
    try:
        from managers.template_manager import TemplateManager
        
        # Initialize template manager
        template_manager = TemplateManager()
        print(f"Templates root: {template_manager.templates_root}")
        
        # Try to validate node-express template
        print("Attempting to validate node-express template...")
        result = template_manager.validate_template("node-express")
        print(f"✅ Validation result: {result}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_template_generation():
    """Test template code generation"""
    print("\n🔍 Testing template code generation...")
    
    try:
        from managers.template_manager import TemplateManager, GenerationContext
        import tempfile
        
        # Initialize template manager
        template_manager = TemplateManager()
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test-muppet"
            
            # Create generation context
            context = GenerationContext(
                template_name="node-express",
                muppet_name="test-muppet",
                output_path=output_path,
                aws_region="us-west-2",
                environment="development"
            )
            
            # Try to generate code
            print("Attempting to generate code...")
            result_path = template_manager.generate_code(context)
            print(f"✅ Code generation successful: {result_path}")
            
            # List generated files
            print("Generated files:")
            for file in sorted(result_path.rglob("*")):
                if file.is_file():
                    print(f"  {file.relative_to(result_path)}")
        
    except Exception as e:
        print(f"❌ Code generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Running node-express template tests...")
    
    validation_success = test_node_express_validation()
    generation_success = test_template_generation()
    
    if validation_success and generation_success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)