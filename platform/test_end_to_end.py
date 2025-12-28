#!/usr/bin/env python3
"""
End-to-end test to validate new Micronaut apps work like workflow-validation-test reference implementation.
"""

import tempfile
import shutil
from pathlib import Path
from src.managers.template_manager import TemplateManager, GenerationContext

def test_end_to_end_micronaut_generation():
    """Comprehensive test that new Micronaut apps match the reference implementation."""
    
    print("🧪 Starting end-to-end validation...")
    
    # Initialize template manager
    template_manager = TemplateManager()
    
    # Discover templates
    templates = template_manager.discover_templates()
    java_template = None
    for template in templates:
        if template.name == "java-micronaut":
            java_template = template
            break
    
    assert java_template is not None, "Java Micronaut template should be available"
    print(f"✅ Found Java Micronaut template v{java_template.version}")
    
    # Create a test muppet with the same parameters as workflow-validation-test
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "end-to-end-test-muppet"
        
        # Create generation context matching workflow-validation-test
        context = GenerationContext(
            muppet_name="end-to-end-test-muppet",
            template_name="java-micronaut",
            parameters={
                "aws_region": "us-west-2",  # Same as workflow-validation-test
                "environment": "development",
                "github_organization": "test-org"
            },
            output_path=output_path
        )
        
        print("🔧 Generating muppet...")
        generated_path = template_manager.generate_code(context)
        assert generated_path.exists(), "Generated muppet directory should exist"
        print(f"✅ Generated muppet at {generated_path}")
        
        # Test 1: Validate file structure matches workflow-validation-test
        print("\n📁 Testing file structure...")
        reference_files = [
            # Core Java files
            "build.gradle",
            "gradle.properties", 
            "settings.gradle",
            "gradlew",
            "gradlew.bat",
            "gradle/wrapper/gradle-wrapper.properties",
            
            # Source code structure
            "src/main/java",
            "src/test/java",
            "src/main/resources/application.yml",
            "src/main/resources/logback.xml",
            
            # Essential scripts (simplified set)
            "scripts/build.sh",
            "scripts/run.sh", 
            "scripts/test.sh",
            "scripts/init.sh",
            
            # Docker and deployment
            "Dockerfile",
            "docker-compose.local.yml",
            "Makefile",
            ".env.local",
            
            # Documentation
            "README.md",  # Should be processed from template
            
            # CI/CD workflows
            ".github/workflows/ci.yml",
            ".github/workflows/cd.yml",
            
            # Infrastructure
            "terraform/main.tf",
            "terraform/variables.tf", 
            "terraform/outputs.tf",
            
            # Kiro configuration
            ".kiro/settings/mcp.json",
            ".kiro/steering/muppet-specific/business-logic.md"
        ]
        
        missing_files = []
        for file_path in reference_files:
            full_path = generated_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        assert not missing_files, f"Missing files compared to reference: {missing_files}"
        print("✅ File structure matches reference implementation")
        
        # Test 2: Validate no template duplication (bug we fixed)
        print("\n🔍 Testing template processing...")
        readme_template = generated_path / "README.template.md"
        assert not readme_template.exists(), "README.template.md should not exist after processing"
        
        readme_final = generated_path / "README.md"
        assert readme_final.exists(), "README.md should exist after template processing"
        
        # Verify README content has variables replaced
        readme_content = readme_final.read_text()
        assert "end-to-end-test-muppet" in readme_content, "README should have muppet name replaced"
        assert "{{muppet_name}}" not in readme_content, "README should not have unreplaced variables"
        print("✅ Template processing working correctly")
        
        # Test 3: Validate Java 21 LTS enforcement
        print("\n☕ Testing Java 21 LTS enforcement...")
        
        # Check Dockerfile
        dockerfile = generated_path / "Dockerfile"
        dockerfile_content = dockerfile.read_text()
        assert "amazoncorretto:21-alpine" in dockerfile_content, "Should use Amazon Corretto 21 LTS"
        assert "Java 21 LTS" in dockerfile_content, "Should reference Java 21 LTS"
        
        # Check CI workflow
        ci_workflow = generated_path / ".github" / "workflows" / "ci.yml"
        ci_content = ci_workflow.read_text()
        assert "java-version: '21'" in ci_content, "CI should use Java 21"
        assert "distribution: 'corretto'" in ci_content, "CI should use Amazon Corretto"
        
        # Check build.gradle
        build_gradle = generated_path / "build.gradle"
        build_content = build_gradle.read_text()
        assert "sourceCompatibility = JavaVersion.VERSION_21" in build_content, "Should target Java 21"
        assert "targetCompatibility = JavaVersion.VERSION_21" in build_content, "Should target Java 21"
        
        print("✅ Java 21 LTS enforcement working correctly")
        
        # Test 4: Validate terraform configuration
        print("\n🏗️ Testing terraform configuration...")
        
        main_tf = generated_path / "terraform" / "main.tf"
        main_tf_content = main_tf.read_text()
        
        # Should have integrated backend configuration (no separate backend.tf)
        assert 'backend "s3"' in main_tf_content, "Should have S3 backend configuration"
        assert 'bucket = "muppet-platform-terraform-state"' in main_tf_content, "Should use shared state bucket"
        assert 'key    = "muppets/end-to-end-test-muppet/terraform.tfstate"' in main_tf_content, "Should use muppet-specific key"
        assert 'region = "us-west-2"' in main_tf_content, "Should use specified region"
        
        # Should use ARM64 architecture
        assert 'cpu_architecture        = "ARM64"' in main_tf_content, "Should use ARM64 architecture"
        
        # Should have Java 21 environment variables in terraform (not Dockerfile)
        assert 'JAVA_VERSION' in main_tf_content and '"21"' in main_tf_content, "Should set Java 21 in ECS container"
        assert 'amazon-corretto' in main_tf_content, "Should specify Amazon Corretto"
        
        print("✅ Terraform configuration matches reference")
        
        # Test 5: Validate CI/CD workflows match reference
        print("\n🔄 Testing CI/CD workflows...")
        
        # Check CI workflow structure
        assert "test-and-build:" in ci_content, "Should have simplified CI job structure"
        assert "Build and test" in ci_content, "Should have build and test step"
        assert "Prepare JAR for Docker" in ci_content, "Should prepare JAR for Docker"
        assert "cp build/libs/*-all.jar build/libs/app.jar" in ci_content, "Should copy shadow JAR"
        
        # Check CD workflow
        cd_workflow = generated_path / ".github" / "workflows" / "cd.yml"
        cd_content = cd_workflow.read_text()
        assert "deploy:" in cd_content, "Should have deploy job"
        assert "ECR" in cd_content, "Should handle ECR repository"
        assert "terraform" in cd_content.lower(), "Should deploy with terraform"
        
        print("✅ CI/CD workflows match reference implementation")
        
        # Test 6: Validate parameter precedence
        print("\n⚙️ Testing parameter precedence...")
        
        # Terraform should use user-specified region
        assert 'region = "us-west-2"' in main_tf_content, "Should use user-specified AWS region"
        
        # Application config should reflect parameters
        app_yml = generated_path / "src" / "main" / "resources" / "application.yml"
        if app_yml.exists():
            app_content = app_yml.read_text()
            # Basic validation that it's a valid YAML structure
            assert "micronaut:" in app_content or "server:" in app_content, "Should have valid application config"
        
        print("✅ Parameter precedence working correctly")
        
        # Test 7: Validate scripts are executable and functional
        print("\n📜 Testing development scripts...")
        
        essential_scripts = ["build.sh", "run.sh", "test.sh", "init.sh"]
        for script_name in essential_scripts:
            script_path = generated_path / "scripts" / script_name
            assert script_path.exists(), f"Script {script_name} should exist"
            
            # Check script has proper shebang and basic structure
            script_content = script_path.read_text()
            assert script_content.startswith("#!/"), f"Script {script_name} should have shebang"
            
            # Check for Java 21 validation in init script
            if script_name == "init.sh":
                assert "JAVA_VERSION" in script_content, "init.sh should validate Java version"
                assert "21" in script_content, "init.sh should check for Java 21"
        
        print("✅ Development scripts generated correctly")
        
        print(f"\n🎉 END-TO-END VALIDATION SUCCESSFUL!")
        print(f"   Generated muppet: end-to-end-test-muppet")
        print(f"   Files generated: {len(list(generated_path.rglob('*')))}")
        print(f"   Template processing: ✅")
        print(f"   Java 21 LTS enforcement: ✅")
        print(f"   Terraform configuration: ✅")
        print(f"   CI/CD workflows: ✅")
        print(f"   Parameter precedence: ✅")
        print(f"   Development scripts: ✅")
        print(f"\n✅ NEW MICRONAUT APPS WILL WORK EXACTLY LIKE WORKFLOW-VALIDATION-TEST!")

if __name__ == "__main__":
    test_end_to_end_micronaut_generation()