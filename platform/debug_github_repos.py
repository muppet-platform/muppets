#!/usr/bin/env python3
"""
Debug script to check GitHub repositories and muppet discovery.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integrations.github import GitHubClient
from services.muppet_lifecycle_service import MuppetLifecycleService


async def main():
    """Debug GitHub repository discovery."""
    print("=== GitHub Repository Discovery Debug ===\n")
    
    # Check environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN not set - using mock mode")
    else:
        print("✅ GITHUB_TOKEN is set")
    
    try:
        # Initialize GitHub client
        client = GitHubClient()
        print(f"GitHub organization: {client.organization}")
        print(f"Using real client: {client._client is not None}\n")
        
        # Get all repositories
        print("Fetching all repositories...")
        repos = await client._fetch_repositories() if client._client else client._get_mock_repositories()
        print(f"Total repositories found: {len(repos)}\n")
        
        # Show all repositories
        print("All repositories:")
        for i, repo in enumerate(repos, 1):
            topics = repo.get('topics', [])
            print(f"  {i}. {repo['name']} - Topics: {topics}")
        
        print()
        
        # Filter for muppet repositories
        muppet_repos = []
        for repo in repos:
            topics = repo.get('topics', [])
            if 'muppet' in topics:
                muppet_repos.append(repo)
        
        print(f"Muppet repositories (with 'muppet' topic): {len(muppet_repos)}")
        for repo in muppet_repos:
            topics = repo.get('topics', [])
            print(f"  - {repo['name']} - Topics: {topics}")
        
        print()
        
        # Test muppet discovery
        print("Testing muppet discovery...")
        muppets = await client.discover_muppets()
        print(f"Discovered muppets: {len(muppets)}")
        for muppet in muppets:
            print(f"  - {muppet.name} ({muppet.template}) - Status: {muppet.status.value}")
        
        print()
        
        # Test lifecycle service
        print("Testing lifecycle service...")
        lifecycle_service = MuppetLifecycleService()
        muppets_info = await lifecycle_service.list_all_muppets()
        
        print(f"Lifecycle service found: {len(muppets_info['muppets'])} muppets")
        for muppet_data in muppets_info['muppets']:
            print(f"  - {muppet_data['name']} ({muppet_data['template']}) - Status: {muppet_data['status']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'client' in locals() and client._client:
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())