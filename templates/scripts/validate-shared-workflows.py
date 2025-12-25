#!/usr/bin/env python3
"""
Script to validate shared workflow files for consistency and correctness.
This ensures all shared workflows follow the required patterns and standards.
"""

import argparse
import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set


class WorkflowValidator:
    """Validates shared workflow files for consistency and correctness."""
    
    def __init__(self, template_type: str):
        self.template_type = template_type
        self.template_path = Path(f"templates/{template_type}")
        self.workflows_path = self.template_path / ".github" / "workflows"
        self.errors = []
        self.warnings = []
        
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print(f"🔍 Validating shared workflows for {self.template_type}...")
        
        # Check if template directory exists
        if not self.template_path.exists():
            self.errors.append(f"Template directory not found: {self.template_path}")
            return False
            
        # Check if workflows directory exists
        if not self.workflows_path.exists():
            self.errors.append(f"Workflows directory not found: {self.workflows_path}")
            return False
            
        # Validate individual workflows
        self._validate_workflow_files()
        self._validate_workflow_manifest()
        self._validate_workflow_consistency()
        self._validate_template_specific_requirements()
        
        # Report results
        self._report_results()
        
        return len(self.errors) == 0
        
    def _validate_workflow_files(self):
        """Validate individual workflow files."""
        required_workflows = ['shared-test.yml', 'shared-build.yml', 'shared-deploy.yml', 'shared-security.yml']
        
        for workflow_file in required_workflows:
            workflow_path = self.workflows_path / workflow_file
            
            if not workflow_path.exists():
                self.errors.append(f"Required workflow file missing: {workflow_file}")
                continue
                
            try:
                with open(workflow_path, 'r') as f:
                    workflow = yaml.safe_load(f)
                    
                self._validate_workflow_structure(workflow_file, workflow)
                
            except yaml.YAMLError as e:
                self.errors.append(f"Invalid YAML in {workflow_file}: {e}")
            except Exception as e:
                self.errors.append(f"Error reading {workflow_file}: {e}")
                
    def _validate_workflow_structure(self, filename: str, workflow: Dict):
        """Validate the structure of a workflow file."""
        # Check required top-level keys
        required_keys = ['name', 'on', 'jobs']
        for key in required_keys:
            if key not in workflow:
                self.errors.append(f"{filename}: Missing required key '{key}'")
                
        # Validate workflow_call trigger
        if 'on' in workflow:
            if 'workflow_call' not in workflow['on']:
                self.errors.append(f"{filename}: Must include 'workflow_call' trigger")
            else:
                self._validate_workflow_call(filename, workflow['on']['workflow_call'])
                
        # Validate jobs
        if 'jobs' in workflow:
            for job_name, job in workflow['jobs'].items():
                self._validate_job(filename, job_name, job)
                
    def _validate_workflow_call(self, filename: str, workflow_call: Dict):
        """Validate workflow_call configuration."""
        if 'inputs' in workflow_call:
            for input_name, input_config in workflow_call['inputs'].items():
                if not isinstance(input_config, dict):
                    self.errors.append(f"{filename}: Input '{input_name}' must be an object")
                    continue
                    
                # Check required input properties
                if 'description' not in input_config:
                    self.warnings.append(f"{filename}: Input '{input_name}' missing description")
                    
                if 'type' not in input_config:
                    self.errors.append(f"{filename}: Input '{input_name}' missing type")
                    
        if 'outputs' in workflow_call:
            for output_name, output_config in workflow_call['outputs'].items():
                if not isinstance(output_config, dict):
                    self.errors.append(f"{filename}: Output '{output_name}' must be an object")
                    continue
                    
                if 'description' not in output_config:
                    self.warnings.append(f"{filename}: Output '{output_name}' missing description")
                    
                if 'value' not in output_config:
                    self.errors.append(f"{filename}: Output '{output_name}' missing value")
                    
    def _validate_job(self, filename: str, job_name: str, job: Dict):
        """Validate individual job configuration."""
        if 'runs-on' not in job:
            self.errors.append(f"{filename}: Job '{job_name}' missing 'runs-on'")
            
        if 'steps' not in job:
            self.errors.append(f"{filename}: Job '{job_name}' missing 'steps'")
            return
            
        # Validate steps
        for i, step in enumerate(job['steps']):
            if not isinstance(step, dict):
                self.errors.append(f"{filename}: Job '{job_name}' step {i} must be an object")
                continue
                
            if 'name' not in step:
                self.warnings.append(f"{filename}: Job '{job_name}' step {i} missing name")
                
            # Check for required actions
            if 'uses' in step:
                self._validate_action_usage(filename, job_name, i, step)
                
    def _validate_action_usage(self, filename: str, job_name: str, step_index: int, step: Dict):
        """Validate usage of GitHub Actions."""
        action = step['uses']
        
        # Check for pinned versions
        if '@' not in action:
            self.warnings.append(f"{filename}: Job '{job_name}' step {step_index} should pin action version: {action}")
        elif action.endswith('@main') or action.endswith('@master'):
            self.warnings.append(f"{filename}: Job '{job_name}' step {step_index} should use specific version instead of branch: {action}")
            
        # Check for common security issues
        if 'github-script' in action and 'script' in step.get('with', {}):
            script = step['with']['script']
            if 'github.event.pull_request.head.repo.full_name' in script:
                self.warnings.append(f"{filename}: Job '{job_name}' step {step_index} may be vulnerable to script injection")
                
    def _validate_workflow_manifest(self):
        """Validate the workflow manifest file."""
        manifest_path = self.workflows_path / "WORKFLOW_MANIFEST.json"
        
        if not manifest_path.exists():
            self.errors.append("Workflow manifest file missing: WORKFLOW_MANIFEST.json")
            return
            
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            self._validate_manifest_structure(manifest)
            
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in WORKFLOW_MANIFEST.json: {e}")
        except Exception as e:
            self.errors.append(f"Error reading WORKFLOW_MANIFEST.json: {e}")
            
    def _validate_manifest_structure(self, manifest: Dict):
        """Validate the structure of the workflow manifest."""
        required_keys = ['template_type', 'version', 'version_tag', 'workflows']
        
        for key in required_keys:
            if key not in manifest:
                self.errors.append(f"Manifest missing required key: {key}")
                
        if 'template_type' in manifest and manifest['template_type'] != self.template_type:
            self.errors.append(f"Manifest template_type '{manifest['template_type']}' doesn't match expected '{self.template_type}'")
            
        if 'workflows' in manifest:
            for workflow_name, workflow_info in manifest['workflows'].items():
                self._validate_manifest_workflow(workflow_name, workflow_info)
                
    def _validate_manifest_workflow(self, workflow_name: str, workflow_info: Dict):
        """Validate individual workflow info in manifest."""
        required_keys = ['file', 'description']
        
        for key in required_keys:
            if key not in workflow_info:
                self.errors.append(f"Manifest workflow '{workflow_name}' missing key: {key}")
                
        # Check if workflow file exists
        if 'file' in workflow_info:
            workflow_file = self.workflows_path / workflow_info['file']
            if not workflow_file.exists():
                self.errors.append(f"Manifest references non-existent workflow file: {workflow_info['file']}")
                
    def _validate_workflow_consistency(self):
        """Validate consistency across workflows."""
        # Check that all workflows use consistent action versions
        action_versions = {}
        
        for workflow_file in self.workflows_path.glob("shared-*.yml"):
            try:
                with open(workflow_file, 'r') as f:
                    workflow = yaml.safe_load(f)
                    
                self._collect_action_versions(workflow_file.name, workflow, action_versions)
                
            except Exception:
                continue  # Already reported in _validate_workflow_files
                
        # Report inconsistent versions
        for action, versions in action_versions.items():
            if len(versions) > 1:
                self.warnings.append(f"Inconsistent versions for action '{action}': {', '.join(versions)}")
                
    def _collect_action_versions(self, filename: str, workflow: Dict, action_versions: Dict):
        """Collect action versions from a workflow."""
        if 'jobs' not in workflow:
            return
            
        for job in workflow['jobs'].values():
            if 'steps' not in job:
                continue
                
            for step in job['steps']:
                if 'uses' not in step:
                    continue
                    
                action = step['uses']
                if '@' in action:
                    action_name, version = action.rsplit('@', 1)
                    if action_name not in action_versions:
                        action_versions[action_name] = set()
                    action_versions[action_name].add(version)
                    
    def _validate_template_specific_requirements(self):
        """Validate template-specific requirements."""
        if self.template_type == 'java-micronaut':
            self._validate_java_requirements()
            
    def _validate_java_requirements(self):
        """Validate Java-specific workflow requirements."""
        # Check that Java 21 LTS is enforced
        test_workflow = self.workflows_path / "shared-test.yml"
        if test_workflow.exists():
            try:
                with open(test_workflow, 'r') as f:
                    content = f.read()
                    
                if 'Java 21 LTS' not in content:
                    self.warnings.append("Java test workflow should enforce Java 21 LTS")
                    
                if 'corretto' not in content:
                    self.warnings.append("Java workflows should use Amazon Corretto distribution")
                    
            except Exception:
                pass
                
    def _report_results(self):
        """Report validation results."""
        if self.errors:
            print(f"\n❌ {len(self.errors)} error(s) found:")
            for error in self.errors:
                print(f"   • {error}")
                
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} warning(s) found:")
            for warning in self.warnings:
                print(f"   • {warning}")
                
        if not self.errors and not self.warnings:
            print("✅ All validations passed!")
        elif not self.errors:
            print("✅ No errors found (warnings can be addressed)")


def main():
    parser = argparse.ArgumentParser(description='Validate shared workflow files')
    parser.add_argument('--template-type', required=True,
                       choices=['java-micronaut'],
                       help='Template type to validate')
    parser.add_argument('--strict', action='store_true',
                       help='Treat warnings as errors')
    
    args = parser.parse_args()
    
    validator = WorkflowValidator(args.template_type)
    success = validator.validate_all()
    
    if args.strict and validator.warnings:
        success = False
        
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()