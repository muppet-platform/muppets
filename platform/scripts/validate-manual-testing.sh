#!/bin/bash
set -e

# Validation script for manual testing setup
# This script verifies that all components are ready for manual testing

echo "🔍 Validating Manual Testing Setup"
echo "=================================="

# Check if we're in the right directory
if [[ ! -f "src/main.py" ]]; then
    echo "❌ Please run this script from the platform directory"
    exit 1
fi

# Check if manual testing setup has been run
if [[ ! -f ".env.real" ]]; then
    echo "❌ Real integration environment not configured"
    echo "   Please run: ./scripts/setup-real-integrations.sh"
    exit 1
fi

echo "✅ Real integration environment configured"

# Check if manual testing directory exists
if [[ ! -d "manual-tests" ]]; then
    echo "❌ Manual testing directory not found"
    echo "   Please run: ./scripts/setup-real-integrations.sh"
    exit 1
fi

echo "✅ Manual testing directory structure exists"

# Check Python environment
echo "🐍 Checking Python environment..."
if ! python -c "import uvicorn, fastapi, httpx, boto3" 2>/dev/null; then
    echo "❌ Required Python packages not installed"
    echo "   Please run: pip install -r requirements.txt"
    exit 1
fi

echo "✅ Python dependencies available"

# Check if we're using real integration mode
if [[ -f ".env" ]]; then
    INTEGRATION_MODE=$(grep "^INTEGRATION_MODE=" .env | cut -d'=' -f2 || echo "mock")
    if [[ "$INTEGRATION_MODE" == "real" ]]; then
        echo "✅ Platform configured for real integration mode"
    else
        echo "⚠️  Platform not in real integration mode (current: $INTEGRATION_MODE)"
        echo "   To enable real integrations: cp .env.real .env"
    fi
else
    echo "⚠️  No .env file found"
    echo "   To enable real integrations: cp .env.real .env"
fi

# Check AWS CLI and credentials
echo "☁️  Checking AWS configuration..."
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed"
    echo "   Please install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured"
    echo "   Please run: aws configure"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-west-2")
echo "✅ AWS configured - Account: $AWS_ACCOUNT_ID, Region: $AWS_REGION"

# Check GitHub CLI and authentication
echo "🐙 Checking GitHub configuration..."
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not installed"
    echo "   Please install: https://cli.github.com/"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI not authenticated"
    echo "   Please run: gh auth login"
    exit 1
fi

GITHUB_USER=$(gh api user --jq .login)
echo "✅ GitHub authenticated as: $GITHUB_USER"

# Check GitHub organization access
echo "🏢 Checking GitHub organization access..."
if gh api orgs/muppet-platform &> /dev/null; then
    echo "✅ Access to muppet-platform organization confirmed"
else
    echo "⚠️  No access to muppet-platform organization"
    echo "   You may need to create it or use a different organization"
fi

# Check if platform service can start
echo "🚀 Testing platform service startup..."
timeout 10s python -c "
import sys
sys.path.insert(0, 'src')
from main import create_app
app = create_app()
print('✅ Platform service can initialize')
" || {
    echo "❌ Platform service failed to initialize"
    echo "   Check logs for errors"
    exit 1
}

# Check manual testing scripts
echo "📝 Checking manual testing scripts..."
if [[ ! -x "manual-tests/scripts/interactive-test.py" ]]; then
    echo "❌ Interactive testing script not executable"
    chmod +x manual-tests/scripts/interactive-test.py
    echo "✅ Fixed interactive testing script permissions"
fi

if [[ ! -x "manual-tests/cleanup/cleanup-test-resources.sh" ]]; then
    echo "❌ Cleanup script not executable"
    chmod +x manual-tests/cleanup/cleanup-test-resources.sh
    echo "✅ Fixed cleanup script permissions"
fi

echo "✅ Manual testing scripts are ready"

# Summary
echo ""
echo "🎉 Manual Testing Validation Complete!"
echo "====================================="
echo ""
echo "✅ All prerequisites are met"
echo "✅ Real integration environment configured"
echo "✅ AWS and GitHub access verified"
echo "✅ Platform service can initialize"
echo "✅ Manual testing scripts are ready"
echo ""
echo "Next Steps:"
echo "1. Start the platform service:"
echo "   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Run interactive tests:"
echo "   cd manual-tests && python scripts/interactive-test.py"
echo ""
echo "3. Or follow the manual testing guide:"
echo "   manual-tests/docs/MANUAL_TESTING_GUIDE.md"
echo ""
echo "4. Clean up when done:"
echo "   ./manual-tests/cleanup/cleanup-test-resources.sh"