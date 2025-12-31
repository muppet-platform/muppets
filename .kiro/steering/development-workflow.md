---
inclusion: always
---

# Development Workflow and Code Quality Standards

This document defines the mandatory development workflow for the Muppet Platform. **All code changes must follow this process without exception.**

## Core Principle

**Quality First**: Every commit must pass all tests and undergo rigorous review. No shortcuts, no exceptions.

## Mandatory Development Workflow

### Step 1: Pre-Commit Testing (MANDATORY)

Before every commit, you MUST run the complete test suite:

```bash
cd platform
make ci-full    # Runs exactly what GitHub Actions runs
```

**What this includes:**
- Code formatting (black, isort)
- Linting (flake8, mypy)
- Basic security checks (bandit, safety)
- Unit tests
- Integration tests
- Property-based tests (fast mode)
- MCP validation tests
- Template validation

**If ANY test fails:**
- ❌ **DO NOT COMMIT**
- ❌ **DO NOT push**
- ❌ **DO NOT create PR**

### Step 2: Test Failure Analysis (MANDATORY)

When tests fail, you MUST provide detailed analysis before making any fixes:

**Required Analysis Format:**
```
## Test Failure Analysis

### Failed Tests:
- [List each failing test with exact error message]

### Root Cause Analysis:
- [Detailed explanation of WHY each test failed]
- [What code change caused the failure]
- [What the test was expecting vs what it got]

### Impact Assessment:
- [What functionality is broken]
- [What other components might be affected]
- [Risk level: Critical/High/Medium/Low]

### Proposed Fix Strategy:
- [Specific approach to fix each failure]
- [Why this approach is correct]
- [What changes will be made]
```

**Example:**
```
## Test Failure Analysis

### Failed Tests:
- test_muppet_creation_completeness: AssertionError: Expected 'success': True, got 'success': False
- test_mcp_tool_discovery: Missing MCP tools: {'create_muppet'}

### Root Cause Analysis:
- The muppet creation endpoint is returning failure status due to missing GitHub token validation
- MCP tool registration is failing because the create_muppet tool isn't being loaded properly
- Recent changes to authentication middleware are rejecting requests without proper token format

### Impact Assessment:
- Critical: Core muppet creation functionality is broken
- High: MCP integration is non-functional
- Affects: All muppet lifecycle operations, platform API, MCP tools

### Proposed Fix Strategy:
- Fix authentication middleware to handle test tokens properly
- Update MCP tool registration to ensure all tools are loaded at startup
- Add proper error handling for missing dependencies
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

### Step 5: Iterative Process (MANDATORY)

If changes are approved:

1. **Implement the approved changes**
2. **Return to Step 1** - Run complete test suite again
3. **Repeat the entire process** until all tests pass
4. **Only then commit and push**

## Enforcement Rules

### Absolute Requirements

1. **No commits without passing tests** - Zero tolerance
2. **No fixes without analysis** - Must understand root cause first
3. **No changes without review** - Critical review is mandatory
4. **No implementation without permission** - User approval required
5. **Complete iteration** - Process must be followed to completion

### Violation Consequences

**If this workflow is not followed:**
- ❌ Commits will be rejected
- ❌ PRs will be blocked
- ❌ Code quality will be compromised
- ❌ Platform stability will be at risk

### Quality Gates

**All of these must be true before any commit:**
- ✅ All tests pass (`make ci-full`)
- ✅ Detailed failure analysis provided (if tests failed)
- ✅ Critical code review completed
- ✅ User permission granted for changes
- ✅ Iterative process completed

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
```

## Integration with CI/CD

This local workflow mirrors exactly what GitHub Actions runs:

- **Local**: `make ci-full` 
- **GitHub Actions**: Same commands in `ci.yml`
- **No surprises**: If it passes locally, it passes in CI

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

### Example 2: Test Failure Workflow
```bash
# Step 1: Run tests
make ci-full
# ❌ 3 tests fail

# Step 2: Analyze failures
# [Provide detailed analysis of each failure]

# Step 3: Review code
# [Perform critical code review]

# Step 4: Get permission
# "I found the root cause and have a fix strategy. May I implement these changes?"
# User: "Yes, proceed"

# Step 5: Implement fixes and repeat
# [Make approved changes]
make ci-full
# ✅ All tests pass

# Get final permission and commit
```

## Conclusion

This workflow ensures:
- **High code quality** through mandatory testing
- **Deep understanding** through required analysis
- **Critical thinking** through mandatory review
- **User control** through required permissions
- **Continuous improvement** through iterative process

**Remember: Quality is not negotiable. This process protects the platform's integrity and ensures reliable, maintainable code.**