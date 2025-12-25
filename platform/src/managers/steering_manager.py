"""
Steering Management System

Manages centralized steering documentation distribution and updates
across all muppets in the platform.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
from pydantic import BaseModel

from ..config import get_settings
from ..integrations.github import GitHubClient
from ..models import Muppet

logger = logging.getLogger(__name__)


class SteeringDocument(BaseModel):
    """Represents a steering document with metadata"""

    name: str
    path: str
    content: str
    version: str
    last_updated: datetime
    category: str  # 'shared', 'template-specific', 'muppet-specific'
    template_type: Optional[str] = None


class SteeringVersion(BaseModel):
    """Tracks steering document versions for a muppet"""

    muppet_name: str
    shared_version: str
    template_version: Optional[str] = None
    last_updated: datetime


class SteeringManager:
    """Manages centralized steering documentation"""

    def __init__(self, github_client: GitHubClient):
        self.github_client = github_client
        self.settings = get_settings()
        self.steering_repo_url = "https://github.com/muppet-platform/steering-docs.git"
        # Use tempfile for secure temp directory instead of hardcoded /tmp
        import tempfile
        self.local_steering_path = Path(tempfile.gettempdir()) / "steering-docs"
        self._version_cache: Dict[str, SteeringVersion] = {}

    async def initialize(self):
        """Initialize the steering management system"""
        logger.info("Initializing steering management system")
        await self._ensure_steering_repo()
        await self._load_version_cache()

    async def _ensure_steering_repo(self):
        """Ensure local copy of steering docs repository exists"""
        if not self.local_steering_path.exists():
            logger.info(
                f"Cloning steering docs repository to {self.local_steering_path}"
            )
            # In production, this would use git clone
            # For now, we'll create the structure
            self.local_steering_path.mkdir(parents=True, exist_ok=True)
            (self.local_steering_path / "shared").mkdir(exist_ok=True)
            (self.local_steering_path / "templates").mkdir(exist_ok=True)

    async def _load_version_cache(self):
        """Load steering version information for all muppets"""
        # In production, this would query GitHub repositories or Parameter Store
        # For now, initialize empty cache
        self._version_cache = {}

    async def get_shared_steering_documents(self) -> List[SteeringDocument]:
        """Get all shared steering documents"""
        await self._ensure_steering_repo()
        shared_path = self.local_steering_path / "shared"
        documents = []

        if shared_path.exists():
            for doc_path in shared_path.glob("*.md"):
                try:
                    async with aiofiles.open(doc_path, "r") as f:
                        content = await f.read()

                    documents.append(
                        SteeringDocument(
                            name=doc_path.stem,
                            path=str(doc_path.relative_to(self.local_steering_path)),
                            content=content,
                            version=await self._get_document_version(doc_path),
                            last_updated=datetime.fromtimestamp(
                                doc_path.stat().st_mtime
                            ),
                            category="shared",
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to load steering document {doc_path}: {e}")

        return documents

    async def get_template_steering_documents(
        self, template_type: str
    ) -> List[SteeringDocument]:
        """Get template-specific steering documents"""
        await self._ensure_steering_repo()
        template_path = self.local_steering_path / "templates" / template_type
        documents = []

        if template_path.exists():
            for doc_path in template_path.glob("*.md"):
                try:
                    async with aiofiles.open(doc_path, "r") as f:
                        content = await f.read()

                    documents.append(
                        SteeringDocument(
                            name=doc_path.stem,
                            path=str(doc_path.relative_to(self.local_steering_path)),
                            content=content,
                            version=await self._get_document_version(doc_path),
                            last_updated=datetime.fromtimestamp(
                                doc_path.stat().st_mtime
                            ),
                            category="template-specific",
                            template_type=template_type,
                        )
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to load template steering document {doc_path}: {e}"
                    )

        return documents

    async def _get_document_version(self, doc_path: Path) -> str:
        """Get version information for a steering document"""
        # In production, this would use git to get the commit hash or tag
        # For now, use file modification time as version
        mtime = doc_path.stat().st_mtime
        return f"v{int(mtime)}"

    async def distribute_steering_to_muppet(self, muppet: Muppet) -> bool:
        """Distribute steering documents to a specific muppet"""
        try:
            logger.info(f"Distributing steering documents to muppet: {muppet.name}")

            # Get shared steering documents
            shared_docs = await self.get_shared_steering_documents()

            # Get template-specific steering documents
            template_docs = await self.get_template_steering_documents(muppet.template)

            # Create steering structure in muppet repository
            await self._create_muppet_steering_structure(
                muppet, shared_docs, template_docs
            )

            # Update version tracking
            await self._update_muppet_steering_version(
                muppet, shared_docs, template_docs
            )

            logger.info(f"Successfully distributed steering documents to {muppet.name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to distribute steering documents to {muppet.name}: {e}"
            )
            return False

    async def _create_muppet_steering_structure(
        self,
        muppet: Muppet,
        shared_docs: List[SteeringDocument],
        template_docs: List[SteeringDocument],
    ):
        """Create the .kiro/steering/ structure in a muppet repository"""
        # In production, this would interact with the GitHub API to create files
        # For now, we'll simulate the structure creation

        steering_structure = {
            "shared": {doc.name + ".md": doc.content for doc in shared_docs},
            "template-specific": {
                doc.name + ".md": doc.content for doc in template_docs
            },
            "muppet-specific": {
                "README.md": self._generate_muppet_specific_readme(muppet)
            },
        }

        logger.info(
            f"Created steering structure for {muppet.name}: {list(steering_structure.keys())}"
        )

    def _generate_muppet_specific_readme(self, muppet: Muppet) -> str:
        """Generate README for muppet-specific steering directory"""
        return """# {muppet.name} Specific Steering Documentation

This directory contains steering documentation specific to the {muppet.name} muppet.

## Guidelines

- Add muppet-specific development guidelines here
- Document any custom patterns or practices for this muppet
- Include integration-specific documentation
- Reference shared and template-specific docs when appropriate

## Shared Documentation

Shared platform standards are available in `../shared/`:
- HTTP response standards
- Test coverage requirements (70% minimum)
- Security guidelines
- Logging standards
- Performance guidelines

## Template Documentation

{muppet.template.title()} specific guidelines are available in `../template-specific/`:
- Framework-specific best practices
- Build and deployment patterns
- Testing strategies
- Performance optimization

## Contributing

1. Add new muppet-specific guidelines as needed
2. Keep documentation up to date with code changes
3. Reference shared standards rather than duplicating them
4. Follow the platform's documentation standards
"""

    async def _update_muppet_steering_version(
        self,
        muppet: Muppet,
        shared_docs: List[SteeringDocument],
        template_docs: List[SteeringDocument],
    ):
        """Update version tracking for muppet steering documents"""
        shared_version = max((doc.version for doc in shared_docs), default="v0")
        template_version = (
            max((doc.version for doc in template_docs), default="v0")
            if template_docs
            else None
        )

        version_info = SteeringVersion(
            muppet_name=muppet.name,
            shared_version=shared_version,
            template_version=template_version,
            last_updated=datetime.utcnow(),
        )

        self._version_cache[muppet.name] = version_info
        logger.info(
            f"Updated steering version for {muppet.name}: shared={shared_version}, template={template_version}"
        )

    async def update_shared_steering_across_muppets(
        self, muppet_names: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Update shared steering documents across all or specified muppets"""
        logger.info("Starting shared steering update across muppets")

        # Refresh local steering repository
        await self._refresh_steering_repo()

        # Get current shared documents
        shared_docs = await self.get_shared_steering_documents()

        # Determine which muppets to update
        if muppet_names is None:
            # Get all muppets from state manager
            # For now, use cached muppet names
            muppet_names = list(self._version_cache.keys())

        results = {}

        for muppet_name in muppet_names:
            try:
                # Check if update is needed
                current_version = self._version_cache.get(muppet_name)
                latest_version = max((doc.version for doc in shared_docs), default="v0")

                if current_version and current_version.shared_version == latest_version:
                    logger.info(
                        f"Muppet {muppet_name} already has latest shared steering version"
                    )
                    results[muppet_name] = True
                    continue

                # Perform update
                success = await self._update_muppet_shared_steering(
                    muppet_name, shared_docs
                )
                results[muppet_name] = success

            except Exception as e:
                logger.error(f"Failed to update shared steering for {muppet_name}: {e}")
                results[muppet_name] = False

        logger.info(f"Shared steering update completed. Results: {results}")
        return results

    async def _refresh_steering_repo(self):
        """Refresh local copy of steering repository"""
        # In production, this would do a git pull
        logger.info("Refreshing steering repository")

    async def _update_muppet_shared_steering(
        self, muppet_name: str, shared_docs: List[SteeringDocument]
    ) -> bool:
        """Update shared steering documents for a specific muppet"""
        try:
            # In production, this would update files in the muppet's GitHub repository
            logger.info(f"Updating shared steering documents for {muppet_name}")

            # Simulate updating shared documents
            for doc in shared_docs:
                logger.debug(f"Updating {doc.name} for {muppet_name}")

            # Update version tracking
            if muppet_name in self._version_cache:
                self._version_cache[muppet_name].shared_version = max(
                    (doc.version for doc in shared_docs), default="v0"
                )
                self._version_cache[muppet_name].last_updated = datetime.utcnow()

            return True

        except Exception as e:
            logger.error(f"Failed to update shared steering for {muppet_name}: {e}")
            return False

    async def list_steering_documents(
        self, muppet_name: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """List available steering documents"""
        result = {"shared": [], "template-specific": [], "muppet-specific": []}

        # Get shared documents
        shared_docs = await self.get_shared_steering_documents()
        result["shared"] = [
            {
                "name": doc.name,
                "path": doc.path,
                "version": doc.version,
                "last_updated": doc.last_updated.isoformat(),
                "category": doc.category,
            }
            for doc in shared_docs
        ]

        # If specific muppet requested, get template and muppet-specific docs
        if muppet_name:
            # Get muppet info to determine template type
            # For now, assume java-micronaut
            template_type = "java-micronaut"  # This would come from muppet metadata

            template_docs = await self.get_template_steering_documents(template_type)
            result["template-specific"] = [
                {
                    "name": doc.name,
                    "path": doc.path,
                    "version": doc.version,
                    "last_updated": doc.last_updated.isoformat(),
                    "category": doc.category,
                    "template_type": doc.template_type,
                }
                for doc in template_docs
            ]

            # Muppet-specific documents would be retrieved from the muppet's repository
            result["muppet-specific"] = [
                {
                    "name": "README",
                    "path": "muppet-specific/README.md",
                    "version": "v1",
                    "last_updated": datetime.utcnow().isoformat(),
                    "category": "muppet-specific",
                }
            ]

        return result

    async def get_muppet_steering_status(self, muppet_name: str) -> Dict:
        """Get steering document status for a specific muppet"""
        version_info = self._version_cache.get(muppet_name)

        if not version_info:
            return {
                "muppet_name": muppet_name,
                "status": "not_initialized",
                "shared_version": None,
                "template_version": None,
                "last_updated": None,
            }

        # Check if updates are available
        shared_docs = await self.get_shared_steering_documents()
        latest_shared_version = max((doc.version for doc in shared_docs), default="v0")

        updates_available = version_info.shared_version != latest_shared_version

        return {
            "muppet_name": muppet_name,
            "status": "up_to_date" if not updates_available else "updates_available",
            "shared_version": version_info.shared_version,
            "template_version": version_info.template_version,
            "last_updated": version_info.last_updated.isoformat(),
            "latest_shared_version": latest_shared_version,
            "updates_available": updates_available,
        }

    async def close(self):
        """Clean up resources"""
        logger.info("Closing steering manager")
        # Clean up temporary files if needed
