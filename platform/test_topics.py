#!/usr/bin/env python3
"""
Test script to debug GitHub topic setting
"""

import asyncio
import sys
sys.path.append('src')

from src.integrations.github import GitHubClient

async def main():
    client = GitHubClient()
    
    if not client._client:
        print("Not in real mode")
        return
    
    try:
        # Test setting topics on the topic-test repository
        topics = ['muppet', 'template-java-micronaut', 'status-creating']
        print(f"Attempting to set topics: {topics}")
        
        success = await client._set_repository_topics('topic-test', topics)
        print(f"Success: {success}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())