#!/usr/bin/env python3
"""
Debug script to check what repositories exist in the muppet-platform organization
"""

import asyncio
import os
import sys
sys.path.append('src')

from src.integrations.github import GitHubClient

async def main():
    client = GitHubClient()
    
    print(f"Organization: {client.organization}")
    print(f"Integration mode: {client.integration_mode}")
    print(f"Has client: {client._client is not None}")
    
    if client._client:
        try:
            repositories = await client._fetch_repositories()
            print(f"\nFound {len(repositories)} repositories:")
            
            for repo in repositories:
                print(f"- {repo['name']}")
                print(f"  Topics: {repo.get('topics', [])}")
                print(f"  Description: {repo.get('description', 'No description')}")
                print()
                
        except Exception as e:
            print(f"Error fetching repositories: {e}")
    else:
        print("No HTTP client available (mock mode)")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())