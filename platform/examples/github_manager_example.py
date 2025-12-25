#!/usr/bin/env python3
"""
Example usage of the GitHub Manager component.

This script demonstrates how to use the GitHubManager for muppet
repository operations including creation, configuration, and management.

Run from the platform directory:
    cd platform && python examples/github_manager_example.py
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_github_manager():
    """Demonstrate GitHub manager functionality."""
    
    logger.info("=== GitHub Manager Demo ===")
    logger.info("This demo shows the GitHub Manager capabilities in mock mode.")
    logger.info("In production, this would interact with the real GitHub API.")
    
    # Import here to avoid path issues
    from src.managers.github_manager import GitHubManager
    
    # Force mock mode by temporarily clearing GitHub token
    import os
    original_token = os.environ.get('GITHUB_TOKEN')
    if 'GITHUB_TOKEN' in os.environ:
        del os.environ['GITHUB_TOKEN']
    
    # Initialize the GitHub manager
    github_manager = GitHubManager()
    
    try:
        # Example 1: Create a new muppet repository
        logger.info("\n1. Creating a new muppet repository...")
        
        # Sample template files that would come from the template manager
        template_files = {
            "README.md": "# Demo Muppet\n\nThis is a demo muppet created using the Muppet Platform.",
            "src/main/java/Application.java": "public class Application { }",
            "build.gradle": "plugins { id 'java' }"
        }
        
        # Custom team permissions
        team_permissions = {
            "platform-team": "admin",
            "demo-developers": "push"
        }
        
        # Create the repository (in mock mode)
        repo_info = await github_manager.create_muppet_repository(
            muppet_name="demo-muppet",
            template="java-micronaut",
            description="Demo muppet showcasing platform capabilities",
            template_files=template_files,
            team_permissions=team_permissions
        )
        
        logger.info(f"✅ Created repository: {repo_info['name']}")
        logger.info(f"   URL: {repo_info['url']}")
        logger.info(f"   Template: {repo_info['template']}")
        logger.info(f"   Branch protection: {repo_info['configuration']['branch_protection']}")
        
        # Example 2: Update muppet status
        logger.info("\n2. Updating muppet status...")
        success = await github_manager.update_muppet_status("demo-muppet", "running")
        logger.info(f"✅ Updated muppet status: {success}")
        
        # Example 3: List all muppet repositories
        logger.info("\n3. Listing all muppet repositories...")
        repositories = await github_manager.get_muppet_repositories()
        logger.info(f"✅ Found {len(repositories)} muppet repositories:")
        for repo in repositories:
            logger.info(f"   - {repo['name']} ({repo['template']}) - {repo['status']}")
        
        # Example 4: Add a collaborator
        logger.info("\n4. Adding a collaborator...")
        success = await github_manager.add_collaborator("demo-muppet", "new-developer", "push")
        logger.info(f"✅ Added collaborator: {success}")
        
        # Example 5: Test validation
        logger.info("\n5. Testing input validation...")
        try:
            await github_manager.create_muppet_repository(
                muppet_name="invalid@name",  # Invalid characters
                template="java-micronaut"
            )
        except Exception as e:
            logger.info(f"✅ Validation caught invalid input: {type(e).__name__}")
        
        logger.info("\n=== Demo Complete ===")
        logger.info("The GitHub Manager successfully demonstrated:")
        logger.info("  ✓ Repository creation with full configuration")
        logger.info("  ✓ Branch protection and workflow setup")
        logger.info("  ✓ Template code deployment")
        logger.info("  ✓ Team permissions management")
        logger.info("  ✓ Status updates and repository management")
        logger.info("  ✓ Input validation and error handling")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise
    finally:
        # Clean up resources
        await github_manager.close()
        
        # Restore original token if it existed
        if original_token:
            os.environ['GITHUB_TOKEN'] = original_token


def main():
    """Run the GitHub manager demonstration."""
    try:
        asyncio.run(demonstrate_github_manager())
    except KeyboardInterrupt:
        logger.info("\n👋 Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())