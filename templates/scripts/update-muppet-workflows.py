#!/usr/bin/env python3
"""
Script to update muppet workflows to use specific shared workflow versions.
This script is used by the platform MCP tools to manage centralized pipeline updates.
"""

import argparse
import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional


class WorkflowUpdater:
    """Manages updating muppet workflows to reference specific shared workflow versions."""
    
    def __init__(self, template_type: str, workflow_version: str):
        self.template_type = template_type
        self.workflow_version = workflow_version
        self.version_tag = f"{template_type}-v{workflow_version}"
        
    def get_workflow_manifest(self) -> Dict:
        """Load the workflow manifest for the specified template and version."""
        manifest_path = Path(f"templates/{self.template_type}/.github/workflows/WORKFLOW_MANIFEST.json")
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"Workflow manifest not found: {manifest_path}")
            
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        if manifest['version'] != self.workflow_version:
            print(f"⚠️  Warning: Manifest version {manifest['version']} doesn't match requested version {self.workflow_version}")
            
        return manifest
        
    def generate_muppet_workflow(self, workflow_type: str, muppet_name: str, 
                                muppet_config: Dict) -> str:
        """Generate a muppet workflow file that references shared workflows."""
        
        manifest = self.get_workflow_manifest()
        
        if workflow_type not in manifest['workflows']:
            raise ValueError(f"Workflow type '{workflow_type}' not found in manifest")
            
        workflow_info = manifest['workflows'][workflow_type]
        
        # Base workflow structure
        workflow = {
            'name': f'{workflow_type.replace("-", " ").title()} - {muppet_name}',
            'on': self._get_workflow_triggers(workflow_type),
            'jobs': {}
        }
        
        # Add workflow-specific jobs
        if workflow_type == 'shared-test':
            workflow['jobs'] = self._generate_test_jobs(muppet_name, muppet_config)
        elif workflow_type == 'shared-build':
            workflow['jobs'] = self._generate_build_jobs(muppet_name, muppet_config)
        elif workflow_type == 'shared-deploy':
            workflow['jobs'] = self._generate_deploy_jobs(muppet_name, muppet_config)
        elif workflow_type == 'shared-security':
            workflow['jobs'] = self._generate_security_jobs(muppet_name, muppet_config)
        else:
            # Generic workflow
            workflow['jobs']['main'] = {
                'uses': f'muppet-platform/templates/.github/workflows/{workflow_info["file"]}@{self.version_tag}',
                'with': self._get_workflow_inputs(workflow_type, muppet_config),
                'secrets': 'inherit'
            }
            
        return yaml.dump(workflow, default_flow_style=False, sort_keys=False)
        
    def _get_workflow_triggers(self, workflow_type: str) -> Dict:
        """Get appropriate triggers for each workflow type."""
        if workflow_type == 'shared-test':
            return {
                'push': {'branches': ['main', 'develop']},
                'pull_request': {'branches': ['main']}
            }
        elif workflow_type == 'shared-build':
            return {
                'push': {'branches': ['main', 'develop']},
                'workflow_run': {
                    'workflows': ['Shared Test'],
                    'types': ['completed'],
                    'branches': ['main', 'develop']
                }
            }
        elif workflow_type == 'shared-deploy':
            return {
                'workflow_run': {
                    'workflows': ['Shared Build'],
                    'types': ['completed'],
                    'branches': ['main', 'develop']
                }
            }
        elif workflow_type == 'shared-security':
            return {
                'push': {'branches': ['main']},
                'schedule': [{'cron': '0 2 * * 1'}]  # Weekly on Monday at 2 AM
            }
        else:
            return {'push': {'branches': ['main']}}
            
    def _generate_test_jobs(self, muppet_name: str, config: Dict) -> Dict:
        """Generate test job configuration."""
        return {
            'test': {
                'uses': f'muppet-platform/templates/.github/workflows/shared-test.yml@{self.version_tag}',
                'with': self._get_test_inputs(config),
                'secrets': 'inherit'
            }
        }
        
    def _generate_build_jobs(self, muppet_name: str, config: Dict) -> Dict:
        """Generate build job configuration."""
        return {
            'build': {
                'needs': 'test',
                'if': "github.event.workflow_run.conclusion == 'success' || github.event_name == 'push'",
                'uses': f'muppet-platform/templates/.github/workflows/shared-build.yml@{self.version_tag}',
                'with': self._get_build_inputs(muppet_name, config),
                'secrets': 'inherit'
            }
        }
        
    def _generate_deploy_jobs(self, muppet_name: str, config: Dict) -> Dict:
        """Generate deploy job configuration."""
        jobs = {}
        
        # Staging deployment
        jobs['deploy-staging'] = {
            'needs': 'build',
            'if': "github.ref == 'refs/heads/develop' && github.event.workflow_run.conclusion == 'success'",
            'uses': f'muppet-platform/templates/.github/workflows/shared-deploy.yml@{self.version_tag}',
            'with': self._get_deploy_inputs(muppet_name, config, 'staging'),
            'secrets': 'inherit'
        }
        
        # Production deployment
        jobs['deploy-production'] = {
            'needs': 'build',
            'if': "github.ref == 'refs/heads/main' && github.event.workflow_run.conclusion == 'success'",
            'uses': f'muppet-platform/templates/.github/workflows/shared-deploy.yml@{self.version_tag}',
            'with': self._get_deploy_inputs(muppet_name, config, 'production'),
            'secrets': 'inherit'
        }
        
        return jobs
        
    def _generate_security_jobs(self, muppet_name: str, config: Dict) -> Dict:
        """Generate security job configuration."""
        return {
            'security-scan': {
                'uses': f'muppet-platform/templates/.github/workflows/shared-security.yml@{self.version_tag}',
                'with': self._get_security_inputs(config),
                'secrets': 'inherit'
            }
        }
        
    def _get_test_inputs(self, config: Dict) -> Dict:
        """Get test workflow inputs based on template type."""
        if self.template_type == 'java-micronaut':
            return {
                'java_version': config.get('java_version', '21'),
                'java_distribution': config.get('java_distribution', 'corretto'),
                'coverage_threshold': config.get('coverage_threshold', 70)
            }
        else:
            return {}
            
    def _get_build_inputs(self, muppet_name: str, config: Dict) -> Dict:
        """Get build workflow inputs based on template type."""
        base_inputs = {
            'ecr_repository': muppet_name,
            'aws_region': config.get('aws_region', 'us-east-1')
        }
        
        if self.template_type == 'java-micronaut':
            base_inputs.update({
                'java_version': config.get('java_version', '21'),
                'java_distribution': config.get('java_distribution', 'corretto')
            })
            
        return base_inputs
        
    def _get_deploy_inputs(self, muppet_name: str, config: Dict, environment: str) -> Dict:
        """Get deploy workflow inputs."""
        return {
            'environment': environment,
            'muppet_name': muppet_name,
            'aws_region': config.get('aws_region', 'us-east-1'),
            'image_uri': '${{ needs.build.outputs.image_uri }}',
            'opentofu_version': config.get('opentofu_version', '1.6.0'),
            'auto_approve': environment == 'staging'
        }
        
    def _get_security_inputs(self, config: Dict) -> Dict:
        """Get security workflow inputs based on template type."""
        if self.template_type == 'java-micronaut':
            return {
                'java_version': config.get('java_version', '21'),
                'java_distribution': config.get('java_distribution', 'corretto'),
                'fail_on_high_severity': config.get('fail_on_high_severity', True)
            }
        else:
            return {}
            
    def _get_workflow_inputs(self, workflow_type: str, config: Dict) -> Dict:
        """Get generic workflow inputs."""
        # This is a fallback for custom workflow types
        return config.get('workflow_inputs', {})


def main():
    parser = argparse.ArgumentParser(description='Update muppet workflows to use specific shared workflow versions')
    parser.add_argument('--template-type', required=True, 
                       choices=['java-micronaut'],
                       help='Template type')
    parser.add_argument('--workflow-version', required=True,
                       help='Workflow version to use (e.g., 1.2.3)')
    parser.add_argument('--workflow-type', required=True,
                       choices=['shared-test', 'shared-build', 'shared-deploy', 'shared-security'],
                       help='Type of workflow to generate')
    parser.add_argument('--muppet-name', required=True,
                       help='Name of the muppet')
    parser.add_argument('--config-file', 
                       help='Path to muppet configuration file (JSON)')
    parser.add_argument('--output-file',
                       help='Output file path (default: stdout)')
    
    args = parser.parse_args()
    
    # Load muppet configuration
    muppet_config = {}
    if args.config_file and os.path.exists(args.config_file):
        with open(args.config_file, 'r') as f:
            muppet_config = json.load(f)
    
    try:
        updater = WorkflowUpdater(args.template_type, args.workflow_version)
        workflow_content = updater.generate_muppet_workflow(
            args.workflow_type, 
            args.muppet_name, 
            muppet_config
        )
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(workflow_content)
            print(f"✅ Generated {args.workflow_type} workflow for {args.muppet_name}")
            print(f"   Output: {args.output_file}")
            print(f"   Version: {args.template_type}-v{args.workflow_version}")
        else:
            print(workflow_content)
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()