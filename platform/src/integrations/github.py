"""
GitHub API integration for the Muppet Platform.

This module provides functionality to interact with GitHub repositories,
discover muppets, and manage repository metadata.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from ..config import get_settings
from ..exceptions import GitHubError
from ..logging_config import get_logger
from ..models import Muppet

logger = get_logger(__name__)


class GitHubClient:
    """
    GitHub API client for muppet discovery and repository management.

    This client handles authentication, API calls, and error handling
    for all GitHub operations.
    """

    def __init__(self):
        self.settings = get_settings()
        self.organization = self.settings.github.organization
        self.token = self.settings.github.token
        self.base_url = "https://api.github.com"
        self.integration_mode = self.settings.integration_mode

        # Initialize HTTP client based on integration mode
        self._client = None
        if self.integration_mode == "real" and HTTPX_AVAILABLE and self.token:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "muppet-platform/1.0",
                },
                timeout=30.0,
            )
            logger.info(
                f"Initialized GitHub client in REAL mode for organization: {self.organization}"
            )
        else:
            logger.info(
                f"GitHub client initialized in MOCK mode for organization: {self.organization}. "
                f"Integration mode: {self.integration_mode}, HTTPX available: {HTTPX_AVAILABLE}, Token configured: {bool(self.token)}"
            )

    async def discover_muppets(self) -> List[Muppet]:
        """
        Discover all muppets by scanning GitHub repositories.

        Returns:
            List of muppets found in the GitHub organization

        Raises:
            GitHubError: If GitHub API calls fail
        """
        try:
            logger.info(f"Discovering muppets in organization: {self.organization}")

            if self._client:
                # Real GitHub API implementation
                repositories = await self._fetch_repositories()
            else:
                # Mock implementation for development/testing
                repositories = self._get_mock_repositories()

            muppets = []
            for repo_data in repositories:
                try:
                    # Only process repositories that are marked as muppets
                    topics = repo_data.get("topics", [])
                    if "muppet" in topics:
                        muppet = Muppet.from_github_repo(repo_data)
                        muppets.append(muppet)
                        logger.debug(f"Discovered muppet: {muppet.name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to parse muppet from repo {repo_data.get('name', 'unknown')}: {e}"
                    )

            logger.info(f"Discovered {len(muppets)} muppets")
            return muppets

        except Exception as e:
            logger.error(f"Failed to discover muppets from GitHub: {e}")
            raise GitHubError(
                message=f"Failed to discover muppets: {str(e)}",
                details={"organization": self.organization},
            )

    async def _fetch_repositories(self) -> List[Dict[str, Any]]:
        """
        Fetch repositories from GitHub API.

        Returns:
            List of repository data from GitHub API

        Raises:
            GitHubError: If API request fails
        """
        try:
            repositories = []
            page = 1
            per_page = 100

            while True:
                url = f"{self.base_url}/orgs/{self.organization}/repos"
                params = {
                    "type": "all",
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": per_page,
                    "page": page,
                }

                logger.debug(f"Fetching repositories page {page}")
                response = await self._client.get(url, params=params)

                if response.status_code == 404:
                    logger.warning(f"Organization not found: {self.organization}")
                    break
                elif response.status_code != 200:
                    raise GitHubError(
                        message=f"GitHub API error: {response.status_code} - {response.text}",
                        details={
                            "status_code": response.status_code,
                            "response": response.text,
                        },
                    )

                page_repos = response.json()
                if not page_repos:
                    break

                repositories.extend(page_repos)

                # If we got fewer than per_page results, we're done
                if len(page_repos) < per_page:
                    break

                page += 1

            logger.debug(f"Fetched {len(repositories)} repositories from GitHub API")
            return repositories

        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch repositories from GitHub API: {e}")
            raise GitHubError(
                message=f"Failed to fetch repositories: {str(e)}",
                details={"organization": self.organization},
            )

    async def update_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main",
    ) -> bool:
        """
        Update a file in a GitHub repository.

        Args:
            repo_name: Repository name (e.g., "muppet-platform/test-muppet")
            file_path: Path to the file in the repository
            content: New file content
            commit_message: Commit message
            branch: Branch name (default: "main")

        Returns:
            True if successful

        Raises:
            GitHubError: If GitHub API calls fail
        """
        try:
            logger.debug(f"Updating file {file_path} in {repo_name}")

            if self._client:
                # Real GitHub API implementation
                # First, get the current file to get its SHA
                url = f"{self.base_url}/repos/{repo_name}/contents/{file_path}"
                response = await self._client.get(url, params={"re": branch})

                file_sha = None
                if response.status_code == 200:
                    file_data = response.json()
                    file_sha = file_data.get("sha")
                elif response.status_code != 404:
                    raise GitHubError(
                        message=f"Failed to get file info: {response.status_code} - {response.text}",
                        details={"repository": repo_name, "file_path": file_path},
                    )

                # Update or create the file
                import base64

                encoded_content = base64.b64encode(content.encode()).decode()

                data = {
                    "message": commit_message,
                    "content": encoded_content,
                    "branch": branch,
                }

                if file_sha:
                    data["sha"] = file_sha

                response = await self._client.put(url, json=data)

                if response.status_code not in [200, 201]:
                    raise GitHubError(
                        message=f"Failed to update file: {response.status_code} - {response.text}",
                        details={"repository": repo_name, "file_path": file_path},
                    )

                logger.info(f"Successfully updated {file_path} in {repo_name}")
                return True
            else:
                # Mock implementation
                logger.info(f"MOCK: Would update file {file_path} in {repo_name}")
                return True

        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"Failed to update file {file_path} in {repo_name}: {e}")
            raise GitHubError(
                message=f"Failed to update file: {str(e)}",
                details={"repository": repo_name, "file_path": file_path},
            )

    async def list_tags(self, repo_name: str) -> List[Dict[str, Any]]:
        """
        List tags for a repository.

        Args:
            repo_name: Repository name (e.g., "muppet-platform/templates")

        Returns:
            List of tag data

        Raises:
            GitHubError: If GitHub API calls fail
        """
        try:
            logger.debug(f"Listing tags for {repo_name}")

            if self._client:
                # Real GitHub API implementation
                url = f"{self.base_url}/repos/{repo_name}/tags"
                response = await self._client.get(url)

                if response.status_code == 404:
                    logger.warning(f"Repository not found: {repo_name}")
                    return []
                elif response.status_code != 200:
                    raise GitHubError(
                        message=f"Failed to list tags: {response.status_code} - {response.text}",
                        details={"repository": repo_name},
                    )

                tags = response.json()
                logger.debug(f"Found {len(tags)} tags for {repo_name}")
                return tags
            else:
                # Mock implementation
                logger.info(f"MOCK: Would list tags for {repo_name}")
                return [
                    {
                        "name": "java-micronaut-v1.2.3",
                        "commit": {"sha": "abc123"},
                        "created_at": "2024-01-15T10:00:00Z",
                    },
                    {
                        "name": "java-micronaut-v1.2.2",
                        "commit": {"sha": "def456"},
                        "created_at": "2024-01-10T10:00:00Z",
                    },
                ]

        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"Failed to list tags for {repo_name}: {e}")
            raise GitHubError(
                message=f"Failed to list tags: {str(e)}",
                details={"repository": repo_name},
            )

    async def get_file_content(
        self, repo_name: str, file_path: str, ref: str = "main"
    ) -> str:
        """
        Get file content from a repository.

        Args:
            repo_name: Repository name (e.g., "muppet-platform/templates")
            file_path: Path to the file in the repository
            ref: Git reference (branch, tag, or commit SHA)

        Returns:
            File content as string

        Raises:
            GitHubError: If GitHub API calls fail
        """
        try:
            logger.debug(f"Getting file content {file_path} from {repo_name} at {ref}")

            if self._client:
                # Real GitHub API implementation
                url = f"{self.base_url}/repos/{repo_name}/contents/{file_path}"
                response = await self._client.get(url, params={"re": ref})

                if response.status_code == 404:
                    raise GitHubError(
                        message=f"File not found: {file_path}",
                        details={
                            "repository": repo_name,
                            "file_path": file_path,
                            "re": ref,
                        },
                    )
                elif response.status_code != 200:
                    raise GitHubError(
                        message=f"Failed to get file content: {response.status_code} - {response.text}",
                        details={"repository": repo_name, "file_path": file_path},
                    )

                file_data = response.json()

                # Decode base64 content
                import base64

                content = base64.b64decode(file_data["content"]).decode()

                logger.debug(f"Retrieved {len(content)} characters from {file_path}")
                return content
            else:
                # Mock implementation
                logger.info(
                    f"MOCK: Would get file content {file_path} from {repo_name}"
                )
                if "WORKFLOW_MANIFEST.json" in file_path:
                    return '{"workflows": {"ci": "v1.0.0"}, "requirements": {"java": "21"}}'
                elif file_path.endswith(".yml"):
                    return f"# Mock workflow content for {file_path}\nname: Mock Workflow\n"
                else:
                    return f"# Mock content for {file_path}\n"

        except GitHubError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to get file content {file_path} from {repo_name}: {e}"
            )
            raise GitHubError(
                message=f"Failed to get file content: {str(e)}",
                details={"repository": repo_name, "file_path": file_path},
            )

    async def update_repository_status(self, muppet_name: str, status: str) -> bool:
        """
        Update repository status (typically via topics or description).

        Args:
            muppet_name: Name of the muppet
            status: New status

        Returns:
            True if successful

        Raises:
            GitHubError: If GitHub API calls fail
        """
        try:
            logger.debug(f"Updating repository status for {muppet_name} to {status}")

            if self._client:
                # Real GitHub API implementation
                repo_name = f"{self.organization}/{muppet_name}"
                url = f"{self.base_url}/repos/{repo_name}"

                # Update repository description to include status
                data = {"description": f"Muppet: {muppet_name} (Status: {status})"}

                response = await self._client.patch(url, json=data)

                if response.status_code != 200:
                    raise GitHubError(
                        message=f"Failed to update repository status: {response.status_code} - {response.text}",
                        details={"repository": repo_name, "status": status},
                    )

                logger.info(
                    f"Successfully updated status for {muppet_name} to {status}"
                )
                return True
            else:
                # Mock implementation
                logger.info(f"MOCK: Would update status for {muppet_name} to {status}")
                return True

        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"Failed to update repository status for {muppet_name}: {e}")
            raise GitHubError(
                message=f"Failed to update repository status: {str(e)}",
                details={"muppet_name": muppet_name, "status": status},
            )

    async def get_repository(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """
        Get repository information by name.

        Args:
            repo_name: Name of the repository

        Returns:
            Repository data or None if not found

        Raises:
            GitHubError: If GitHub API calls fail
        """
        try:
            logger.debug(f"Getting repository: {repo_name}")

            if self._client:
                # Real GitHub API implementation
                url = f"{self.base_url}/repos/{self.organization}/{repo_name}"
                response = await self._client.get(url)

                if response.status_code == 404:
                    return None
                elif response.status_code != 200:
                    raise GitHubError(
                        message=f"GitHub API error: {response.status_code} - {response.text}",
                        details={
                            "status_code": response.status_code,
                            "repository": repo_name,
                        },
                    )

                return response.json()
            else:
                # Mock implementation
                mock_repos = self._get_mock_repositories()
                for repo in mock_repos:
                    if repo["name"] == repo_name:
                        return repo
                return None

        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"Failed to get repository {repo_name}: {e}")
            raise GitHubError(
                message=f"Failed to get repository: {str(e)}",
                details={"repository": repo_name},
            )

    async def create_repository(
        self, name: str, template: str, description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a new repository for a muppet with full configuration.

        Args:
            name: Repository name
            template: Template type used
            description: Repository description

        Returns:
            Created repository data

        Raises:
            GitHubError: If repository creation fails
        """
        try:
            logger.info(f"Creating repository: {name} with template: {template}")

            if self._client:
                # Real GitHub API implementation
                url = f"{self.base_url}/orgs/{self.organization}/repos"
                payload = {
                    "name": name,
                    "description": description,
                    "private": self.settings.github.visibility == "private",
                    "auto_init": True,
                    "gitignore_template": self._get_gitignore_template(template),
                    "license_template": "mit",
                    "allow_squash_merge": True,
                    "allow_merge_commit": False,
                    "allow_rebase_merge": False,
                    "delete_branch_on_merge": True,
                }

                response = await self._client.post(url, json=payload)

                if response.status_code == 422:
                    raise GitHubError(
                        message=f"Repository '{name}' already exists",
                        details={"repository": name, "status_code": 422},
                    )
                elif response.status_code != 201:
                    raise GitHubError(
                        message=f"GitHub API error: {response.status_code} - {response.text}",
                        details={
                            "status_code": response.status_code,
                            "repository": name,
                        },
                    )

                repo_data = response.json()

                # Set repository topics
                await self._set_repository_topics(
                    name, ["muppet", f"template-{template}", "status-creating"]
                )

                # Configure branch protection and workflows
                await self._setup_repository_configuration(name, template)

                return repo_data
            else:
                # Mock implementation
                repo_data = {
                    "name": name,
                    "full_name": f"{self.organization}/{name}",
                    "html_url": f"https://github.com/{self.organization}/{name}",
                    "description": description,
                    "private": self.settings.github.visibility == "private",
                    "topics": ["muppet", f"template-{template}", "status-creating"],
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                }

                logger.info(f"Created repository (mock): {name}")
                return repo_data

        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"Failed to create repository {name}: {e}")
            raise GitHubError(
                message=f"Failed to create repository: {str(e)}",
                details={"repository": name, "template": template},
            )

    async def _setup_repository_configuration(
        self, repo_name: str, template: str
    ) -> None:
        """
        Set up complete repository configuration including branch protection and workflows.

        Args:
            repo_name: Repository name
            template: Template type used for workflow configuration
        """
        try:
            logger.info(f"Setting up repository configuration for: {repo_name}")

            if not self._client:
                logger.info(f"Repository configuration setup (mock): {repo_name}")
                return

            # Set up branch protection rules
            await self._setup_branch_protection(repo_name)

            # Set up CI/CD workflows
            await self._setup_workflows(repo_name, template)

            # Set up issue and PR templates
            await self._setup_templates(repo_name)

            logger.info(f"Completed repository configuration for: {repo_name}")

        except Exception as e:
            logger.error(
                f"Failed to setup repository configuration for {repo_name}: {e}"
            )
            # Don't raise here - repository creation should succeed even if configuration fails

    async def _setup_branch_protection(self, repo_name: str) -> bool:
        """
        Set up branch protection rules for the main branch.

        Args:
            repo_name: Repository name

        Returns:
            True if successful
        """
        try:
            if not self.settings.github.branch_protection:
                logger.debug(f"Branch protection disabled for {repo_name}")
                return True

            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/branches/main/protection"
            payload = {
                "required_status_checks": {
                    "strict": True,
                    "contexts": ["build", "test"],
                },
                "enforce_admins": False,
                "required_pull_request_reviews": {
                    "required_approving_review_count": self.settings.github.required_reviews,
                    "dismiss_stale_reviews": self.settings.github.dismiss_stale_reviews,
                    "require_code_owner_reviews": True,
                    "require_last_push_approval": True,
                },
                "restrictions": None,
                "allow_force_pushes": False,
                "allow_deletions": False,
                "block_creations": False,
                "required_conversation_resolution": True,
            }

            response = await self._client.put(url, json=payload)

            if response.status_code == 200:
                logger.info(f"Set up branch protection for {repo_name}")
                return True
            else:
                logger.warning(
                    f"Failed to set up branch protection for {repo_name}: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.warning(f"Failed to set up branch protection for {repo_name}: {e}")
            return False

    async def _setup_workflows(self, repo_name: str, template: str) -> bool:
        """
        Set up CI/CD workflows for the repository.

        Args:
            repo_name: Repository name
            template: Template type for workflow configuration

        Returns:
            True if successful
        """
        try:
            # Create .github/workflows directory and workflow files
            workflows = self._get_workflow_templates(template)

            for workflow_name, workflow_content in workflows.items():
                success = await self._create_file(
                    repo_name,
                    f".github/workflows/{workflow_name}",
                    workflow_content,
                    f"Add {workflow_name} workflow",
                )
                if success:
                    logger.debug(f"Created workflow {workflow_name} for {repo_name}")
                else:
                    logger.warning(
                        f"Failed to create workflow {workflow_name} for {repo_name}"
                    )

            logger.info(f"Set up workflows for {repo_name}")
            return True

        except Exception as e:
            logger.warning(f"Failed to set up workflows for {repo_name}: {e}")
            return False

    async def _setup_templates(self, repo_name: str) -> bool:
        """
        Set up issue and PR templates for the repository.

        Args:
            repo_name: Repository name

        Returns:
            True if successful
        """
        try:
            # Create issue template
            issue_template = self._get_issue_template()
            await self._create_file(
                repo_name,
                ".github/ISSUE_TEMPLATE/bug_report.md",
                issue_template,
                "Add issue template",
            )

            # Create PR template
            pr_template = self._get_pr_template()
            await self._create_file(
                repo_name,
                ".github/pull_request_template.md",
                pr_template,
                "Add PR template",
            )

            # Create CODEOWNERS file
            codeowners = self._get_codeowners_template()
            await self._create_file(
                repo_name, ".github/CODEOWNERS", codeowners, "Add CODEOWNERS file"
            )

            logger.info(f"Set up templates for {repo_name}")
            return True

        except Exception as e:
            logger.warning(f"Failed to set up templates for {repo_name}: {e}")
            return False

    async def _create_file(
        self, repo_name: str, path: str, content: str, commit_message: str
    ) -> bool:
        """
        Create a file in the repository.

        Args:
            repo_name: Repository name
            path: File path in repository
            content: File content
            commit_message: Commit message

        Returns:
            True if successful
        """
        try:
            import base64

            url = (
                f"{self.base_url}/repos/{self.organization}/{repo_name}/contents/{path}"
            )
            payload = {
                "message": commit_message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": "main",
            }

            response = await self._client.put(url, json=payload)

            if response.status_code == 201:
                logger.debug(f"Created file {path} in {repo_name}")
                return True
            else:
                logger.warning(
                    f"Failed to create file {path} in {repo_name}: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.warning(f"Failed to create file {path} in {repo_name}: {e}")
            return False

    async def push_template_code(
        self, repo_name: str, template: str, template_files: Dict[str, str]
    ) -> bool:
        """
        Push template code to the repository using GitHub Git Data API batch operations.
        Falls back to individual file creation if batch operations fail.

        Args:
            repo_name: Repository name
            template: Template type
            template_files: Dictionary of file paths to content (str or bytes)

        Returns:
            True if successful

        Raises:
            GitHubError: If code push fails
        """
        try:
            logger.info(f"Pushing template code to repository: {repo_name}")

            if not self._client:
                logger.info(f"Template code push (mock): {repo_name}")
                return True

            # Try batch operations first for better performance
            logger.info(f"Attempting batch push of {len(template_files)} files")
            success = await self._push_files_batch(
                repo_name, template_files, f"Add {template} template files"
            )

            if success:
                logger.info(f"Batch push successful for {repo_name}")
            else:
                # Fallback to individual file creation
                logger.warning(
                    f"Batch push failed for {repo_name}, falling back to individual file creation"
                )
                success = await self._push_files_individual(
                    repo_name, template_files, template
                )

            if success:
                # Update repository status to indicate code has been pushed
                await self.update_repository_status(repo_name, "ready")
                logger.info(f"Successfully pushed template code to {repo_name}")
                return True
            else:
                logger.error(
                    f"Both batch and individual push methods failed for {repo_name}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to push template code to {repo_name}: {e}")
            raise GitHubError(
                message=f"Failed to push template code: {str(e)}",
                details={"repository": repo_name, "template": template},
            )

    async def _push_files_batch(
        self, repo_name: str, files: Dict[str, any], commit_message: str
    ) -> bool:
        """
        Push multiple files in a single commit using GitHub Git Data API with comprehensive validation.

        This approach is much more efficient and reliable than individual file creation,
        especially for nested directories like .github/workflows.

        Args:
            repo_name: Repository name
            files: Dictionary of file paths to content (str or bytes)
            commit_message: Commit message

        Returns:
            True if successful
        """
        try:
            logger.info(f"Starting batch push of {len(files)} files to {repo_name}")

            # For newly created repositories, wait a moment for GitHub to initialize
            import asyncio

            await asyncio.sleep(2)

            # Step 1: Get the current branch reference (main)
            branch_ref = await self._get_branch_ref(repo_name, "main")
            if not branch_ref:
                logger.error(f"Failed to get branch reference for {repo_name}")
                return False

            parent_commit_sha = branch_ref["object"]["sha"]
            logger.debug(f"Parent commit SHA: {parent_commit_sha}")

            # Step 2: Get the current tree SHA
            base_tree_sha = await self._get_commit_tree_sha(
                repo_name, parent_commit_sha
            )
            if not base_tree_sha:
                logger.error(f"Failed to get base tree SHA for {repo_name}")
                return False

            logger.debug(f"Base tree SHA: {base_tree_sha}")

            # Step 3: Validate and create blobs for all files with comprehensive validation
            tree_entries = []
            blob_failures = []
            large_files = []
            invalid_paths = []

            for file_path, content in files.items():
                try:
                    # Validate file path
                    if not self._is_valid_file_path(file_path):
                        logger.warning(f"Invalid file path: {file_path}")
                        invalid_paths.append(file_path)
                        continue

                    # Check file size limits
                    content_size = (
                        len(content) if isinstance(content, (str, bytes)) else 0
                    )
                    if content_size > 100 * 1024 * 1024:  # 100MB GitHub limit
                        logger.warning(
                            f"File too large: {file_path} ({content_size} bytes)"
                        )
                        large_files.append(file_path)
                        continue

                    # Create blob with validation
                    blob_sha = await self._create_blob_validated(
                        repo_name, content, file_path
                    )
                    if not blob_sha:
                        logger.error(f"Failed to create blob for {file_path}")
                        blob_failures.append(file_path)
                        continue

                    # Validate blob SHA format
                    if not self._is_valid_sha(blob_sha):
                        logger.error(f"Invalid blob SHA for {file_path}: {blob_sha}")
                        blob_failures.append(file_path)
                        continue

                    # Determine file mode with validation
                    mode = self._get_file_mode(file_path)
                    if not mode:
                        logger.error(f"Could not determine file mode for {file_path}")
                        blob_failures.append(file_path)
                        continue

                    # Create validated tree entry
                    tree_entry = {
                        "path": file_path,
                        "mode": mode,
                        "type": "blob",
                        "sha": blob_sha,
                    }

                    # Validate tree entry structure
                    if self._validate_tree_entry(tree_entry):
                        tree_entries.append(tree_entry)
                    else:
                        logger.error(
                            f"Invalid tree entry for {file_path}: {tree_entry}"
                        )
                        blob_failures.append(file_path)

                except Exception as e:
                    logger.error(f"Exception processing {file_path}: {e}")
                    blob_failures.append(file_path)

            # Report validation results
            if blob_failures:
                logger.warning(
                    f"Failed to process {len(blob_failures)} files: {blob_failures}"
                )
            if large_files:
                logger.warning(f"Skipped {len(large_files)} large files: {large_files}")
            if invalid_paths:
                logger.warning(
                    f"Skipped {len(invalid_paths)} invalid paths: {invalid_paths}"
                )

            if not tree_entries:
                logger.error("No valid files to create tree with")
                return False

            logger.info(
                f"Successfully validated {len(tree_entries)} files for tree creation"
            )

            # Step 4: Create tree with batch size limits and retry logic
            success = await self._create_tree_with_retry(
                repo_name,
                tree_entries,
                base_tree_sha,
                parent_commit_sha,
                commit_message,
            )

            if success:
                logger.info(
                    f"Successfully pushed {len(tree_entries)} files to {repo_name} in batch"
                )
                return True
            else:
                logger.error("Failed to create tree after all retry attempts")
                return False

        except Exception as e:
            logger.error(f"Batch push failed for {repo_name}: {e}")
            return False

    async def _push_files_individual(
        self, repo_name: str, files: Dict[str, any], template: str
    ) -> bool:
        """
        Push files individually using Contents API as fallback.

        Args:
            repo_name: Repository name
            files: Dictionary of file paths to content (str or bytes)
            template: Template name for commit messages

        Returns:
            True if successful
        """
        try:
            logger.info(
                f"Starting individual push of {len(files)} files to {repo_name}"
            )

            success_count = 0
            failed_files = []

            for file_path, content in files.items():
                try:
                    # Handle binary files properly
                    if isinstance(content, bytes):
                        # For binary files, we need to use base64 encoding
                        import base64

                        encoded_content = base64.b64encode(content).decode()

                        # Create the file using raw API call for binary content
                        success = await self._create_file_binary(
                            repo_name,
                            file_path,
                            encoded_content,
                            f"Add {file_path} from {template} template",
                        )
                    else:
                        # For text files, use the existing method
                        success = await self._create_file(
                            repo_name,
                            file_path,
                            content,
                            f"Add {file_path} from {template} template",
                        )

                    if success:
                        success_count += 1
                        logger.debug(f"Successfully pushed {file_path}")
                    else:
                        failed_files.append(file_path)
                        logger.warning(f"Failed to push {file_path}")

                except Exception as e:
                    failed_files.append(file_path)
                    logger.warning(f"Error pushing {file_path}: {e}")

            logger.info(
                f"Individual push completed: {success_count}/{len(files)} files successful"
            )

            if failed_files:
                logger.warning(
                    f"Failed to push {len(failed_files)} files: {failed_files}"
                )

            # Consider it successful if we pushed most files (allow some failures for non-critical files)
            success_rate = success_count / len(files)
            return success_rate >= 0.8  # 80% success rate threshold

        except Exception as e:
            logger.error(f"Individual push failed for {repo_name}: {e}")
            return False

    async def _create_file_binary(
        self, repo_name: str, path: str, base64_content: str, commit_message: str
    ) -> bool:
        """
        Create a binary file in the repository using base64 content.

        Args:
            repo_name: Repository name
            path: File path in repository
            base64_content: Base64 encoded file content
            commit_message: Commit message

        Returns:
            True if successful
        """
        try:
            url = (
                f"{self.base_url}/repos/{self.organization}/{repo_name}/contents/{path}"
            )
            payload = {
                "message": commit_message,
                "content": base64_content,
                "branch": "main",
            }

            response = await self._client.put(url, json=payload)

            if response.status_code == 201:
                logger.debug(f"Created binary file {path} in {repo_name}")
                return True
            else:
                logger.warning(
                    f"Failed to create binary file {path} in {repo_name}: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.warning(f"Failed to create binary file {path} in {repo_name}: {e}")
            return False

    def _is_valid_file_path(self, file_path: str) -> bool:
        """Validate that a file path is acceptable for GitHub tree API."""
        if not file_path or not isinstance(file_path, str):
            return False

        # Check for invalid characters
        invalid_chars = ["\\", "\0", "\r", "\n"]
        if any(char in file_path for char in invalid_chars):
            return False

        # Check path length (GitHub has limits)
        if len(file_path) > 4096:
            return False

        # Check for relative path components
        if ".." in file_path or file_path.startswith("/"):
            return False

        # Check for empty path components
        if "//" in file_path or file_path.endswith("/"):
            return False

        return True

    def _is_valid_sha(self, sha: str) -> bool:
        """Validate that a SHA is properly formatted."""
        if not sha or not isinstance(sha, str):
            return False

        if len(sha) != 40:
            return False

        # Check if all characters are valid hex
        try:
            int(sha, 16)
            return True
        except ValueError:
            return False

    def _get_file_mode(self, file_path: str) -> Optional[str]:
        """Get the appropriate Git file mode for a file path."""
        if not file_path:
            return None

        # Executable files
        if file_path.endswith((".sh", "gradlew")) or "/bin/" in file_path:
            return "100755"

        # Regular files
        return "100644"

    def _validate_tree_entry(self, entry: Dict[str, str]) -> bool:
        """Validate a tree entry structure."""
        required_fields = ["path", "mode", "type", "sha"]

        # Check all required fields are present
        for field in required_fields:
            if field not in entry:
                return False

        # Validate field values
        if not self._is_valid_file_path(entry["path"]):
            return False

        if entry["mode"] not in ["100644", "100755", "040000", "120000", "160000"]:
            return False

        if entry["type"] not in ["blob", "tree", "commit"]:
            return False

        if not self._is_valid_sha(entry["sha"]):
            return False

        return True

    async def _create_blob_validated(
        self, repo_name: str, content: any, file_path: str
    ) -> Optional[str]:
        """Create a blob with enhanced validation and error handling."""
        try:
            import base64

            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/git/blobs"

            # Handle both string and bytes content with size validation
            if isinstance(content, bytes):
                # Check size limits for binary files
                if len(content) > 50 * 1024 * 1024:  # 50MB limit for binary
                    logger.warning(
                        f"Binary file too large: {file_path} ({len(content)} bytes)"
                    )
                    return None

                encoded_content = base64.b64encode(content).decode()
                encoding = "base64"
            else:
                # For text files, validate encoding
                try:
                    content_bytes = content.encode("utf-8")
                    if len(content_bytes) > 100 * 1024 * 1024:  # 100MB limit for text
                        logger.warning(
                            f"Text file too large: {file_path} ({len(content_bytes)} bytes)"
                        )
                        return None

                    encoded_content = base64.b64encode(content_bytes).decode()
                    encoding = "base64"
                except UnicodeEncodeError as e:
                    logger.error(f"Failed to encode text file {file_path}: {e}")
                    return None

            payload = {"content": encoded_content, "encoding": encoding}

            response = await self._client.post(url, json=payload)

            if response.status_code == 201:
                blob_data = response.json()
                blob_sha = blob_data["sha"]

                # Validate returned SHA
                if not self._is_valid_sha(blob_sha):
                    logger.error(
                        f"GitHub returned invalid SHA for {file_path}: {blob_sha}"
                    )
                    return None

                logger.debug(
                    f"Created blob for {file_path}: {blob_sha[:8]}... (size: {len(encoded_content)} chars)"
                )
                return blob_sha
            else:
                logger.error(
                    f"Failed to create blob for {file_path}: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error creating blob for {file_path}: {e}")
            return None

    async def _create_tree_with_retry(
        self,
        repo_name: str,
        tree_entries: List[Dict[str, str]],
        base_tree_sha: str,
        parent_commit_sha: str,
        commit_message: str,
    ) -> bool:
        """Create tree with comprehensive retry logic and batch size management."""

        # Try full batch first
        logger.info(f"Attempting to create tree with {len(tree_entries)} entries")

        # Log sample entries for debugging
        logger.debug(f"Sample tree entries: {tree_entries[:3]}")

        # Attempt 1: Full tree with base_tree
        new_tree_sha = await self._create_tree(repo_name, tree_entries, base_tree_sha)

        if new_tree_sha:
            return await self._complete_commit(
                repo_name, new_tree_sha, parent_commit_sha, commit_message
            )

        # Attempt 2: Full tree without base_tree
        logger.warning("Retrying tree creation without base_tree")
        new_tree_sha = await self._create_tree(repo_name, tree_entries, None)

        if new_tree_sha:
            return await self._complete_commit(
                repo_name, new_tree_sha, parent_commit_sha, commit_message
            )

        # Attempt 3: Split into smaller batches
        logger.warning("Attempting tree creation with smaller batches")
        return await self._create_tree_in_batches(
            repo_name, tree_entries, base_tree_sha, parent_commit_sha, commit_message
        )

    async def _complete_commit(
        self, repo_name: str, tree_sha: str, parent_commit_sha: str, commit_message: str
    ) -> bool:
        """Complete the commit process with the given tree."""

        # Create commit
        new_commit_sha = await self._create_commit(
            repo_name, tree_sha, parent_commit_sha, commit_message
        )
        if not new_commit_sha:
            logger.error(f"Failed to create commit for {repo_name}")
            return False

        logger.debug(f"Created commit: {new_commit_sha}")

        # Update branch reference
        success = await self._update_branch_ref(repo_name, "main", new_commit_sha)
        if not success:
            logger.error(f"Failed to update branch reference for {repo_name}")
            return False

        return True

    async def _create_tree_in_batches(
        self,
        repo_name: str,
        tree_entries: List[Dict[str, str]],
        base_tree_sha: str,
        parent_commit_sha: str,
        commit_message: str,
    ) -> bool:
        """Create tree in smaller batches if full tree creation fails."""

        batch_size = 20  # Start with smaller batches
        current_tree_sha = base_tree_sha
        current_commit_sha = parent_commit_sha

        # Split entries into batches
        for i in range(0, len(tree_entries), batch_size):
            batch = tree_entries[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(tree_entries) + batch_size - 1) // batch_size

            logger.info(
                f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)"
            )

            # Create tree for this batch
            new_tree_sha = await self._create_tree(repo_name, batch, current_tree_sha)

            if not new_tree_sha:
                logger.error(f"Failed to create tree for batch {batch_num}")

                # Try without base_tree for this batch
                new_tree_sha = await self._create_tree(repo_name, batch, None)

                if not new_tree_sha:
                    logger.error(
                        f"Failed to create tree for batch {batch_num} even without base_tree"
                    )
                    return False

            # Create commit for this batch
            batch_commit_message = (
                f"{commit_message} (batch {batch_num}/{total_batches})"
            )
            new_commit_sha = await self._create_commit(
                repo_name, new_tree_sha, current_commit_sha, batch_commit_message
            )

            if not new_commit_sha:
                logger.error(f"Failed to create commit for batch {batch_num}")
                return False

            # Update for next iteration
            current_tree_sha = new_tree_sha
            current_commit_sha = new_commit_sha

            logger.debug(f"Completed batch {batch_num}: commit {new_commit_sha[:8]}...")

        # Update branch reference to final commit
        success = await self._update_branch_ref(repo_name, "main", current_commit_sha)
        if not success:
            logger.error("Failed to update branch reference after batch processing")
            return False

        logger.info(f"Successfully created tree in {total_batches} batches")
        return True

    async def _get_branch_ref(
        self, repo_name: str, branch: str
    ) -> Optional[Dict[str, Any]]:
        """Get branch reference information."""
        try:
            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/git/refs/heads/{branch}"
            response = await self._client.get(url)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # Branch doesn't exist yet, try to get the default branch
                logger.warning(
                    f"Branch {branch} not found, checking repository default branch"
                )
                repo_url = f"{self.base_url}/repos/{self.organization}/{repo_name}"
                repo_response = await self._client.get(repo_url)

                if repo_response.status_code == 200:
                    repo_data = repo_response.json()
                    default_branch = repo_data.get("default_branch")

                    if default_branch and default_branch != branch:
                        # Try the default branch
                        default_url = f"{self.base_url}/repos/{self.organization}/{repo_name}/git/refs/heads/{default_branch}"
                        default_response = await self._client.get(default_url)

                        if default_response.status_code == 200:
                            logger.info(
                                f"Using default branch {default_branch} instead of {branch}"
                            )
                            return default_response.json()

                logger.error(f"No valid branch found for {repo_name}")
                return None
            else:
                logger.error(
                    f"Failed to get branch ref: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error getting branch ref: {e}")
            return None

    async def _get_commit_tree_sha(
        self, repo_name: str, commit_sha: str
    ) -> Optional[str]:
        """Get tree SHA from commit."""
        try:
            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/git/commits/{commit_sha}"
            response = await self._client.get(url)

            if response.status_code == 200:
                commit_data = response.json()
                return commit_data["tree"]["sha"]
            else:
                logger.error(
                    f"Failed to get commit tree: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error getting commit tree: {e}")
            return None

    async def _create_blob(self, repo_name: str, content: any) -> Optional[str]:
        """Create a blob for file content."""
        try:
            import base64

            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/git/blobs"

            # Handle both string and bytes content
            if isinstance(content, bytes):
                # For binary files, encode as base64
                encoded_content = base64.b64encode(content).decode()
                encoding = "base64"
            else:
                # For text files, use UTF-8
                encoded_content = base64.b64encode(content.encode("utf-8")).decode()
                encoding = "base64"

            payload = {"content": encoded_content, "encoding": encoding}

            response = await self._client.post(url, json=payload)

            if response.status_code == 201:
                blob_data = response.json()
                blob_sha = blob_data["sha"]
                logger.debug(
                    f"Created blob: {blob_sha[:8]}... (size: {len(encoded_content)} chars)"
                )
                return blob_sha
            else:
                logger.error(
                    f"Failed to create blob: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error creating blob: {e}")
            return None

    async def _create_tree(
        self,
        repo_name: str,
        tree_entries: List[Dict[str, str]],
        base_tree_sha: Optional[str],
    ) -> Optional[str]:
        """Create a new tree with the given entries."""
        try:
            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/git/trees"

            # Build payload - only include base_tree if it's valid
            payload = {"tree": tree_entries}
            if base_tree_sha and self._is_valid_sha(base_tree_sha):
                payload["base_tree"] = base_tree_sha

            # Enhanced debug logging
            logger.info(f"Creating tree for {repo_name}")
            logger.info(
                f"Base tree SHA: {base_tree_sha} (valid: {self._is_valid_sha(base_tree_sha) if base_tree_sha else False})"
            )
            logger.info(f"Tree entries count: {len(tree_entries)}")
            logger.debug(
                f"Sample tree entries: {tree_entries[:3] if tree_entries else []}"
            )

            # Validate all tree entries before sending
            invalid_entries = []
            for i, entry in enumerate(tree_entries):
                if not self._validate_tree_entry(entry):
                    invalid_entries.append(f"Entry {i}: {entry}")

            if invalid_entries:
                logger.error(f"Invalid tree entries found: {invalid_entries}")
                return None

            logger.debug(f"Tree creation payload: {payload}")

            response = await self._client.post(url, json=payload)

            if response.status_code == 201:
                tree_data = response.json()
                logger.info(f"Successfully created tree: {tree_data['sha']}")
                return tree_data["sha"]
            else:
                logger.error(
                    f"Failed to create tree: {response.status_code} - {response.text}"
                )
                logger.error(f"Request URL: {url}")
                logger.error(f"Payload was: {payload}")

                # If we used base_tree, try without it
                if "base_tree" in payload:
                    logger.warning("Retrying tree creation without base_tree")
                    payload_no_base = {"tree": tree_entries}
                    retry_response = await self._client.post(url, json=payload_no_base)

                    if retry_response.status_code == 201:
                        tree_data = retry_response.json()
                        logger.info(
                            f"Successfully created tree without base_tree: {tree_data['sha']}"
                        )
                        return tree_data["sha"]
                    else:
                        logger.error(
                            f"Retry without base_tree also failed: {retry_response.status_code} - {retry_response.text}"
                        )

                return None

        except Exception as e:
            logger.error(f"Exception creating tree: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def _create_commit(
        self, repo_name: str, tree_sha: str, parent_sha: str, message: str
    ) -> Optional[str]:
        """Create a new commit."""
        try:
            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/git/commits"

            payload = {"message": message, "tree": tree_sha, "parents": [parent_sha]}

            response = await self._client.post(url, json=payload)

            if response.status_code == 201:
                commit_data = response.json()
                return commit_data["sha"]
            else:
                logger.error(
                    f"Failed to create commit: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error creating commit: {e}")
            return None

    async def _update_branch_ref(
        self, repo_name: str, branch: str, commit_sha: str
    ) -> bool:
        """Update branch reference to point to new commit."""
        try:
            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/git/refs/heads/{branch}"

            payload = {"sha": commit_sha}

            response = await self._client.patch(url, json=payload)

            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Failed to update branch ref: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error updating branch ref: {e}")
            return False

    def _get_workflow_templates(self, template: str) -> Dict[str, str]:
        """
        Get CI/CD workflow templates based on the muppet template.

        Args:
            template: Template type

        Returns:
            Dictionary of workflow filename to content
        """
        if template == "java-micronaut":
            return {
                "ci.yml": self._get_java_ci_workflow(),
                "cd.yml": self._get_java_cd_workflow(),
                "security.yml": self._get_security_workflow(),
            }
        else:
            # Default to Java Micronaut workflows for all templates
            return {
                "ci.yml": self._get_java_ci_workflow(),
                "cd.yml": self._get_java_cd_workflow(),
                "security.yml": self._get_security_workflow(),
            }

    def _get_security_workflow(self) -> str:
        """Get security scanning workflow."""
        return """name: Security Scan

on:
  schedule:
    - cron: '0 2 * * *'  # Run daily at 2 AM UTC
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'
"""

    def _get_java_ci_workflow(self) -> str:
        """Get Java Micronaut CI workflow."""
        return """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Amazon Corretto JDK 21
      uses: actions/setup-java@v4
      with:
        java-version: '21'
        distribution: 'corretto'

    - name: Cache Gradle packages
      uses: actions/cache@v3
      with:
        path: |
          ~/.gradle/caches
          ~/.gradle/wrapper
        key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
        restore-keys: |
          ${{ runner.os }}-gradle-

    - name: Grant execute permission for gradlew
      run: chmod +x gradlew

    - name: Run tests
      run: ./gradlew test

    - name: Generate test report
      uses: dorny/test-reporter@v1
      if: success() || failure()
      with:
        name: Test Results
        path: build/test-results/test/*.xml
        reporter: java-junit

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: build/reports/jacoco/test/jacocoTestReport.xml

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Amazon Corretto JDK 21
      uses: actions/setup-java@v4
      with:
        java-version: '21'
        distribution: 'corretto'

    - name: Cache Gradle packages
      uses: actions/cache@v3
      with:
        path: |
          ~/.gradle/caches
          ~/.gradle/wrapper
        key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
        restore-keys: |
          ${{ runner.os }}-gradle-

    - name: Grant execute permission for gradlew
      run: chmod +x gradlew

    - name: Build application
      run: ./gradlew build -x test

    - name: Build Docker image
      run: docker build -t muppet-app .
"""

    def _get_java_cd_workflow(self) -> str:
        """Get Java Micronaut CD workflow."""
        return """name: CD

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
    - uses: actions/checkout@v4

    - name: Set up Amazon Corretto JDK 21
      uses: actions/setup-java@v4
      with:
        java-version: '21'
        distribution: 'corretto'

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2

    - name: Cache Gradle packages
      uses: actions/cache@v3
      with:
        path: |
          ~/.gradle/caches
          ~/.gradle/wrapper
        key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
        restore-keys: |
          ${{ runner.os }}-gradle-

    - name: Grant execute permission for gradlew
      run: chmod +x gradlew

    - name: Build application
      run: ./gradlew build

    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: muppet-platform-registry
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

    - name: Deploy to ECS
      run: |
        # Update ECS service with new image
        aws ecs update-service --cluster muppet-platform-cluster --service ${{ github.event.repository.name }} --force-new-deployment
"""

    def _get_python_ci_workflow(self) -> str:
        """Get Python FastAPI CI workflow."""
        return """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Install dependencies
      run: |
        uv venv
        source .venv/bin/activate
        uv pip install -r requirements.txt
        uv pip install pytest pytest-cov

    - name: Run tests
      run: |
        source .venv/bin/activate
        pytest --cov=src --cov-report=xml

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Build Docker image
      run: docker build -t muppet-app .
"""

    def _get_python_cd_workflow(self) -> str:
        """Get Python FastAPI CD workflow."""
        return """name: CD

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
    - uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2

    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: muppet-platform-registry
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

    - name: Deploy to ECS
      run: |
        aws ecs update-service --cluster muppet-platform-cluster --service ${{ github.event.repository.name }} --force-new-deployment
"""

    def _get_generic_ci_workflow(self) -> str:
        """Get generic CI workflow."""
        return """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Run tests
      run: |
        if [ -f "scripts/test.sh" ]; then
          chmod +x scripts/test.sh
          ./scripts/test.sh
        else
          echo "No test script found"
        fi

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Build Docker image
      run: docker build -t muppet-app .
"""

    def _get_generic_cd_workflow(self) -> str:
        """Get generic CD workflow."""
        return """name: CD

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
    - uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2

    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: muppet-platform-registry
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

    - name: Deploy to ECS
      run: |
        aws ecs update-service --cluster muppet-platform-cluster --service ${{ github.event.repository.name }} --force-new-deployment
"""

    def _get_issue_template(self) -> str:
        """Get issue template content."""
        return """---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. macOS, Linux, Windows]
 - Version: [e.g. 1.0.0]
 - Java Version: [e.g. Amazon Corretto 21]

**Additional context**
Add any other context about the problem here.
"""

    def _get_pr_template(self) -> str:
        """Get PR template content."""
        return """## Description
Brief description of the changes in this PR.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Related Issues
Closes #(issue number)
"""

    def _get_codeowners_template(self) -> str:
        """Get CODEOWNERS template content."""
        return """# Global owners
* @muppet-platform/platform-team

# Specific file patterns
*.md @muppet-platform/docs-team
.github/ @muppet-platform/platform-team
terraform/ @muppet-platform/infrastructure-team
"""

    async def _set_repository_topics(self, repo_name: str, topics: List[str]) -> bool:
        """
        Set topics for a repository.

        Args:
            repo_name: Repository name
            topics: List of topics to set

        Returns:
            True if successful

        Raises:
            GitHubError: If API request fails
        """
        try:
            if not self._client:
                return True  # Mock mode

            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/topics"
            payload = {"names": topics}

            response = await self._client.put(url, json=payload)

            if response.status_code != 200:
                logger.warning(
                    f"Failed to set topics for {repo_name}: {response.status_code} - {response.text}"
                )
                return False

            logger.debug(f"Set topics for repository {repo_name}: {topics}")
            return True

        except Exception as e:
            logger.warning(f"Failed to set repository topics: {e}")
            return False

    async def setup_repository_permissions(
        self, repo_name: str, team_permissions: Dict[str, str] = None
    ) -> bool:
        """
        Set up repository permissions for teams and users.

        Args:
            repo_name: Repository name
            team_permissions: Dictionary of team names to permission levels

        Returns:
            True if successful
        """
        try:
            logger.info(f"Setting up repository permissions for: {repo_name}")

            if not self._client:
                logger.info(f"Repository permissions setup (mock): {repo_name}")
                return True

            # Default team permissions
            default_permissions = {
                "platform-team": "admin",
                "developers": "push",
                "reviewers": "pull",
            }

            permissions = team_permissions or default_permissions

            for team_name, permission in permissions.items():
                success = await self._set_team_permission(
                    repo_name, team_name, permission
                )
                if success:
                    logger.debug(
                        f"Set {permission} permission for team {team_name} on {repo_name}"
                    )
                else:
                    logger.warning(
                        f"Failed to set permission for team {team_name} on {repo_name}"
                    )

            logger.info(f"Completed repository permissions setup for: {repo_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to setup repository permissions for {repo_name}: {e}")
            return False

    async def _set_team_permission(
        self, repo_name: str, team_name: str, permission: str
    ) -> bool:
        """
        Set permission for a team on a repository.

        Args:
            repo_name: Repository name
            team_name: Team name
            permission: Permission level (pull, push, admin)

        Returns:
            True if successful
        """
        try:
            url = f"{self.base_url}/orgs/{self.organization}/teams/{team_name}/repos/{self.organization}/{repo_name}"
            payload = {"permission": permission}

            response = await self._client.put(url, json=payload)

            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                logger.warning(
                    f"Team {team_name} not found in organization {self.organization}"
                )
                return False
            else:
                logger.warning(f"Failed to set team permission: {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"Failed to set team permission for {team_name}: {e}")
            return False

    async def add_repository_collaborator(
        self, repo_name: str, username: str, permission: str = "push"
    ) -> bool:
        """
        Add a collaborator to a repository.

        Args:
            repo_name: Repository name
            username: GitHub username
            permission: Permission level (pull, push, admin)

        Returns:
            True if successful
        """
        try:
            logger.info(
                f"Adding collaborator {username} to {repo_name} with {permission} permission"
            )

            if not self._client:
                logger.info(f"Add collaborator (mock): {username} to {repo_name}")
                return True

            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/collaborators/{username}"
            payload = {"permission": permission}

            response = await self._client.put(url, json=payload)

            if response.status_code in [201, 204]:
                logger.info(f"Added collaborator {username} to {repo_name}")
                return True
            else:
                logger.warning(
                    f"Failed to add collaborator {username}: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to add collaborator {username} to {repo_name}: {e}")
            return False

    async def remove_repository_collaborator(
        self, repo_name: str, username: str
    ) -> bool:
        """
        Remove a collaborator from a repository.

        Args:
            repo_name: Repository name
            username: GitHub username

        Returns:
            True if successful
        """
        try:
            logger.info(f"Removing collaborator {username} from {repo_name}")

            if not self._client:
                logger.info(f"Remove collaborator (mock): {username} from {repo_name}")
                return True

            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/collaborators/{username}"
            response = await self._client.delete(url)

            if response.status_code == 204:
                logger.info(f"Removed collaborator {username} from {repo_name}")
                return True
            else:
                logger.warning(
                    f"Failed to remove collaborator {username}: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(
                f"Failed to remove collaborator {username} from {repo_name}: {e}"
            )
            return False

    async def get_repository_collaborators(
        self, repo_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of repository collaborators.

        Args:
            repo_name: Repository name

        Returns:
            List of collaborator information
        """
        try:
            logger.debug(f"Getting collaborators for {repo_name}")

            if not self._client:
                # Mock collaborators
                return [
                    {
                        "login": "platform-admin",
                        "permissions": {"admin": True, "push": True, "pull": True},
                    },
                    {
                        "login": "developer-1",
                        "permissions": {"admin": False, "push": True, "pull": True},
                    },
                ]

            url = f"{self.base_url}/repos/{self.organization}/{repo_name}/collaborators"
            response = await self._client.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    f"Failed to get collaborators for {repo_name}: {response.status_code}"
                )
                return []

        except Exception as e:
            logger.error(f"Failed to get collaborators for {repo_name}: {e}")
            return []

    def _get_gitignore_template(self, template: str) -> str:
        """Get appropriate .gitignore template based on muppet template."""
        template_mapping = {"java-micronaut": "Java"}
        return template_mapping.get(template, "Java")

    async def delete_repository(self, name: str) -> bool:
        """
        Delete a repository.

        Args:
            name: Repository name to delete

        Returns:
            True if deletion was successful

        Raises:
            GitHubError: If repository deletion fails
        """
        try:
            logger.info(f"Deleting repository: {name}")

            if self._client:
                # Real GitHub API implementation
                url = f"{self.base_url}/repos/{self.organization}/{name}"
                response = await self._client.delete(url)

                if response.status_code == 404:
                    logger.warning(f"Repository not found for deletion: {name}")
                    return False
                elif response.status_code != 204:
                    raise GitHubError(
                        message=f"GitHub API error: {response.status_code} - {response.text}",
                        details={
                            "status_code": response.status_code,
                            "repository": name,
                        },
                    )

                logger.info(f"Deleted repository: {name}")
                return True
            else:
                # Mock implementation
                logger.info(f"Deleted repository (mock): {name}")
                return True

        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete repository {name}: {e}")
            raise GitHubError(
                message=f"Failed to delete repository: {str(e)}",
                details={"repository": name},
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.debug("Closed GitHub HTTP client")

    def _get_mock_repositories(self) -> List[Dict[str, Any]]:
        """
        Get mock repository data for testing.

        In a real implementation, this would be replaced with actual GitHub API calls.
        """
        return [
            {
                "name": "test-muppet-1",
                "full_name": f"{self.organization}/test-muppet-1",
                "html_url": f"https://github.com/{self.organization}/test-muppet-1",
                "description": "Test muppet for development",
                "private": True,
                "topics": ["template:java-micronaut", "status:running", "muppet"],
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            },
            {
                "name": "demo-api",
                "full_name": f"{self.organization}/demo-api",
                "html_url": f"https://github.com/{self.organization}/demo-api",
                "description": "Demo API muppet",
                "private": True,
                "topics": ["template:java-micronaut", "status:running", "muppet"],
                "created_at": "2024-01-02T09:00:00Z",
                "updated_at": "2024-01-02T11:30:00Z",
            },
        ]
