#!/usr/bin/env python3
"""
Script to add 'muppet' topic to existing repositories that don't have it
"""

import asyncio
import sys

sys.path.append("src")

from src.integrations.github import GitHubClient


async def main():
    client = GitHubClient()

    if not client._client:
        print("Not in real mode, cannot update repositories")
        return

    try:
        # Get all repositories
        repositories = await client._fetch_repositories()
        print(f"Found {len(repositories)} repositories")

        # Find repositories that need the muppet topic
        repos_to_fix = []
        for repo in repositories:
            topics = repo.get("topics", [])
            name = repo["name"]

            # Skip infrastructure repos
            if name in ["templates", "terraform-modules", "docs", "steering-docs"]:
                continue

            if "muppet" not in topics:
                repos_to_fix.append(repo)
                print(
                    f"Repository '{name}' needs muppet topic (current topics: {topics})"
                )

        if not repos_to_fix:
            print("All repositories already have the muppet topic")
            return

        # Add muppet topic to repositories that need it
        for repo in repos_to_fix:
            name = repo["name"]
            current_topics = repo.get("topics", [])

            # Add muppet topic and status:running (assuming they're operational)
            new_topics = current_topics + ["muppet", "status:running"]
            # Remove duplicates while preserving order
            new_topics = list(dict.fromkeys(new_topics))

            print(f"Setting topics for {name}: {new_topics}")
            success = await client._set_repository_topics(name, new_topics)

            if success:
                print(f"✅ Successfully updated topics for {name}")
            else:
                print(f"❌ Failed to update topics for {name}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
