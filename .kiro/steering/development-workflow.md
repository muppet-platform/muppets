---
inclusion: always
---

# Development Workflow and Code Quality Standards

**Mandatory 5-step process for all code changes. No exceptions.**

## Core Principle
**Quality First**: Every commit must pass all tests and undergo rigorous review.

## Mandatory Workflow

### Step 1: Pre-Commit Testing (MANDATORY)
```bash
cd platform && make ci-full  # Must pass before commit
```

**If ANY test fails:**
- ❌ DO NOT COMMIT, PUSH, or CREATE PR

### Step 1.5: GitHub Actions Monitoring (MANDATORY)
```bash
gh run list --limit 5  # Check within 10 minutes of push
gh run watch <run-id>  # Monitor real-time
```

**If ANY workflow fails:**
- 🚨 IMMEDIATE ACTION REQUIRED
- 🚨 DO NOT push until resolved
- 🚨 MUST perform failure analysis (Step 2)

### Step 2: Failure Analysis (MANDATORY)
When tests fail, provide detailed analysis:
```
## Failure Analysis
### Failed Tests/Workflows: [exact errors + GitHub URLs]
### Root Cause: [why it failed, what changed]
### Impact: [functionality broken, risk level]
### Fix Strategy: [specific approach, why correct]
```

### Step 3: Critical Code Review (MANDATORY)
Review checklist:
- [ ] Architecture & design principles followed
- [ ] Code quality & readability
- [ ] Security & input validation
- [ ] Testing & edge cases
- [ ] Performance & compatibility

### Step 4: User Permission (MANDATORY)
Present analysis and ask explicit permission:
```
Based on analysis, I recommend:
1. [Change 1 with rationale]
2. [Change 2 with rationale]

**May I proceed with implementing these changes?**
```

### Step 5: Iterative Process (MANDATORY)
1. Implement approved changes
2. Return to Step 1 (run tests again)
3. Repeat until ALL tests pass AND ALL workflows pass
4. Only then consider work complete

## Quality Gates
**Before commit:**
- ✅ All tests pass (`make ci-full`)
- ✅ Failure analysis provided (if needed)
- ✅ Critical code review completed
- ✅ User permission granted

**After push:**
- ✅ All GitHub Actions workflows pass
- ✅ No failing runs in last 24 hours

## Essential Commands
```bash
# Complete CI simulation
make ci-full

# GitHub Actions monitoring
gh run list && gh run watch <run-id>

# Development environment
make run && make stop && make clean
```

**Remember: Quality is not negotiable. This process protects platform integrity.**
- [How to prevent similar failures in the future]
```

**GitHub Actions Failure Analysis Requirements:**
- 📊 **Download and review full logs** from failed workflows
- 🔍 **Compare local vs GitHub Actions environment** differences
- 🕐 **Check for timing/race conditions** in integration tests
- 🔑 **Verify secrets and environment variables** are properly configured
- 🌐 **Validate external service dependencies** (AWS, GitHub API)
- 📈 **Review resource usage** (memory, CPU, disk space)

**Example GitHub Actions Failure Analysis:**
```
## Test/Workflow Failure Analysis

### Failed Tests/Workflows:
- CI Workflow (Run #123): https://github.com/muppet-platform/muppets/actions/runs/123
- Job "Platform Tests" failed at step "Run MCP validation tests"
- Error: "ImportError: cannot import name 'get_available_tools'"

### Root Cause Analysis:
- GitHub Actions is using a different Python path resolution than local environment
- The test script is trying to import a function that was recently renamed
- Local tests pass because of cached imports, but fresh GitHub environment fails
- This indicates our local testing doesn't fully replicate the GitHub Actions environment

### Impact Assessment:
- Critical: CI pipeline is broken, blocking all merges
- High: MCP functionality validation is not working in CI
- Affects: All pull requests, deployment pipeline, code quality gates

### GitHub Actions Specific Analysis:
- Workflow: CI (run ID: 123)
- Failed job: Platform Tests
- Failed step: Run MCP validation tests
- Environment: ubuntu-latest with Python 3.10
- No environment differences in dependencies
- Issue is code-related, not infrastructure-related

### Proposed Fix Strategy:
- Update test script to use correct import path
- Add import validation to local test suite
- Verify all imports work in clean Python environment
- Add pre-commit hook to catch import errors
```

### Step 3: Critical Code Review (MANDATORY)

After analysis, you must perform a critical code review of your changes:

**Review Checklist:**

#### Architecture & Design
- [ ] Does this change follow platform design principles?
- [ ] Is the solution simple and maintainable?
- [ ] Are there any architectural violations?
- [ ] Does it maintain separation of concerns?

#### Code Quality
- [ ] Is the code readable and well-documented?
- [ ] Are variable and function names descriptive?
- [ ] Is error handling comprehensive?
- [ ] Are there any code smells or anti-patterns?

#### Security
- [ ] Are all inputs validated and sanitized?
- [ ] Are secrets handled properly?
- [ ] Are there any security vulnerabilities?
- [ ] Does it follow security best practices?

#### Testing
- [ ] Are all edge cases covered?
- [ ] Are tests comprehensive and meaningful?
- [ ] Do tests follow testing best practices?
- [ ] Are mocks used appropriately?

#### Performance
- [ ] Are there any performance bottlenecks?
- [ ] Is resource usage optimized?
- [ ] Are database queries efficient?
- [ ] Is caching used appropriately?

#### Compatibility
- [ ] Does it maintain backward compatibility?
- [ ] Are all dependencies compatible?
- [ ] Does it work across all supported environments?
- [ ] Are breaking changes documented?

**Critical Review Format:**
```
## Critical Code Review

### Architecture Analysis:
[Detailed analysis of architectural decisions]

### Code Quality Assessment:
[Analysis of code quality, readability, maintainability]

### Security Review:
[Security implications and vulnerabilities]

### Performance Impact:
[Performance considerations and optimizations]

### Risk Assessment:
[Potential risks and mitigation strategies]

### Recommendations:
[Specific improvements needed before commit]
```

### Step 4: User Permission (MANDATORY)

Before making any code changes based on the review, you MUST:

1. **Present the complete analysis** (Steps 2 & 3)
2. **Ask explicit permission** to proceed with changes
3. **Wait for user approval** before making any modifications

**Required Permission Format:**
```
Based on my analysis, I recommend the following changes:

1. [Specific change 1 with rationale]
2. [Specific change 2 with rationale]
3. [Specific change 3 with rationale]

These changes address [root causes] and will [expected outcomes].

**May I proceed with implementing these changes?**
```

**For GitHub Actions Failures:**
```
GitHub Actions Analysis Summary:
- Workflow: [workflow name]
- Run ID: [GitHub Actions run ID and URL]
- Root cause: [specific technical cause]
- Proposed fix: [detailed fix strategy]

Local tests: [PASS/FAIL status]
Impact: [production impact assessment]

**May I proceed with implementing the fix for this GitHub Actions failure?**
```

### Step 5: Iterative Process (MANDATORY)

If changes are approved:

1. **Implement the approved changes**
2. **Return to Step 1** - Run complete test suite again
3. **Push changes and monitor GitHub Actions** (Step 1.5)
4. **Repeat the entire process** until all tests pass AND all GitHub Actions workflows pass
5. **Only then consider the work complete**

**GitHub Actions Monitoring Loop:**
- After each push, immediately check GitHub Actions status
- If any workflow fails, return to Step 2 for failure analysis
- Do not proceed with additional work until ALL workflows are green
- Verify all 4 workflows pass: CI, CD, Security, Nightly (if applicable)

## Enforcement Rules

### Absolute Requirements

1. **No commits without passing tests** - Zero tolerance
2. **No fixes without analysis** - Must understand root cause first
3. **No changes without review** - Critical review is mandatory
4. **No implementation without permission** - User approval required
5. **Complete iteration** - Process must be followed to completion
6. **GitHub Actions monitoring** - All workflows must pass after push
7. **Immediate failure response** - GitHub Actions failures require immediate analysis

### Violation Consequences

**If this workflow is not followed:**
- ❌ Commits will be rejected
- ❌ PRs will be blocked
- ❌ Code quality will be compromised
- ❌ Platform stability will be at risk
- ❌ Production deployments will be blocked

### Quality Gates

**All of these must be true before any commit:**
- ✅ All tests pass (`make ci-full`)
- ✅ Detailed failure analysis provided (if tests failed)
- ✅ Critical code review completed
- ✅ User permission granted for changes
- ✅ Iterative process completed

**All of these must be true after any push:**
- ✅ All GitHub Actions workflows pass (CI, CD, Security, Nightly)
- ✅ No failing workflow runs in the last 24 hours
- ✅ All integration tests pass in GitHub Actions environment
- ✅ Security scans complete without critical issues

## Local Development Commands

### Essential Commands
```bash
# Complete CI simulation (MANDATORY before commit)
make ci-full

# Individual test categories
make test           # All tests with smart environment detection
make lint           # Code quality checks
make format         # Code formatting
make type-check     # Type checking

# Development environment
make run            # Start LocalStack + Platform
make stop           # Stop development environment
make clean          # Clean containers and volumes
```

### GitHub Actions Commands
```bash
# Install GitHub CLI (if not already installed)
# macOS: brew install gh
# Login: gh auth login

# Check recent workflow runs
gh run list --limit 10

# Watch a specific run in real-time
gh run watch <run-id>

# View logs for failed runs
gh run view <run-id> --log-failed

# Re-run failed workflows
gh run rerun <run-id>

# Check workflow status for current branch
gh run list --branch $(git branch --show-current) --limit 5
```

### Test Environment Setup
```bash
# First time setup
cd platform
make setup

# Start development environment
make run

# Verify environment
curl http://localhost:8000/health
curl http://localhost:4566/_localstack/health

# Verify GitHub CLI is working
gh auth status
gh repo view --json name,url
```

## Integration with CI/CD

This local workflow mirrors exactly what GitHub Actions runs:

- **Local**: `make ci-full` 
- **GitHub Actions**: Same commands in `ci.yml`
- **No surprises**: If it passes locally, it passes in CI

**GitHub Actions Workflow Monitoring:**
- **CI Workflow**: Runs on every push and PR - monitors code quality, tests, security
- **CD Workflow**: Runs on main branch - handles deployments
- **Security Workflow**: Runs weekly - comprehensive security scanning
- **Nightly Workflow**: Runs daily - extended testing and maintenance

**Workflow Dependencies:**
- CD workflow requires CI workflow to pass
- Security failures block deployments
- All workflows must pass for production releases

## Quality Metrics

### Success Criteria
- 🎯 **100% test pass rate** before commit
- 🎯 **Zero security vulnerabilities** in basic scans
- 🎯 **Complete code coverage** for new functionality
- 🎯 **Comprehensive analysis** for all failures
- 🎯 **Thorough review** of all changes

### Monitoring
- All test results are logged
- Code review quality is tracked
- Workflow compliance is monitored
- Quality metrics are reported

## Examples

### Example 1: Successful Workflow
```bash
# Step 1: Run tests
make ci-full
# ✅ All tests pass

# Step 2: No failures to analyze

# Step 3: Review changes
# [Perform critical code review]

# Step 4: Get permission
# "All tests pass and code review is clean. May I commit these changes?"
# User: "Yes, approved"

# Step 5: Commit
git add .
git commit -m "feat: add muppet validation endpoint"
git push
```

### Example 2: GitHub Actions Failure Workflow
```bash
# Step 1: Run tests locally
make ci-full
# ✅ All tests pass locally

# Push changes
git push

# Step 1.5: Monitor GitHub Actions
gh run list --limit 5
# ❌ CI workflow failed

# Step 2: Analyze GitHub Actions failure
gh run view <run-id> --log-failed
# [Provide detailed analysis of GitHub Actions failure]

# Step 3: Review code
# [Perform critical code review focusing on environment differences]

# Step 4: Get permission
# "GitHub Actions failed due to environment difference. I found the root cause and have a fix strategy. May I implement these changes?"
# User: "Yes, proceed"

# Step 5: Implement fixes and repeat
# [Make approved changes]
make ci-full
# ✅ All tests pass locally

git push
gh run watch <new-run-id>
# ✅ All GitHub Actions workflows pass

# Get final confirmation that all workflows are green
```

### Example 3: Successful Workflow with GitHub Actions
```bash
# Step 1: Run tests
make ci-full
# ✅ All tests pass

# Step 2: No failures to analyze

# Step 3: Review changes
# [Perform critical code review]

# Step 4: Get permission
# "All tests pass and code review is clean. May I commit these changes?"
# User: "Yes, approved"

# Step 5: Commit and monitor
git add .
git commit -m "feat: add new feature"
git push

# Step 1.5: Monitor GitHub Actions
gh run watch
# ✅ All workflows pass

# Work is complete
```

## Conclusion

This workflow ensures:
- **High code quality** through mandatory testing
- **Deep understanding** through required analysis
- **Critical thinking** through mandatory review
- **User control** through required permissions
- **Continuous improvement** through iterative process
- **Production stability** through GitHub Actions monitoring
- **Immediate issue resolution** through mandatory failure analysis

**Remember: Quality is not negotiable. This process protects the platform's integrity and ensures reliable, maintainable code. GitHub Actions failures are treated with the same severity as local test failures - both require immediate analysis and resolution.**