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
        Push template code to the repository.

        Args:
            repo_name: Repository name
            template: Template type
            template_files: Dictionary of file paths to content

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

            # Push each template file
            for file_path, content in template_files.items():
                success = await self._create_file(
                    repo_name,
                    file_path,
                    content,
                    f"Add {file_path} from {template} template",
                )
                if not success:
                    logger.warning(f"Failed to push file {file_path} to {repo_name}")

            # Update repository status to indicate code has been pushed
            await self.update_repository_status(repo_name, "ready")

            logger.info(f"Successfully pushed template code to {repo_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to push template code to {repo_name}: {e}")
            raise GitHubError(
                message=f"Failed to push template code: {str(e)}",
                details={"repository": repo_name, "template": template},
            )

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
            }
        else:
            # Default to Java Micronaut workflows for all templates
            return {
                "ci.yml": self._get_java_ci_workflow(),
                "cd.yml": self._get_java_cd_workflow(),
            }

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
