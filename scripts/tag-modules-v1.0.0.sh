#!/bin/bash
# Tag the current state as v1.0.0 for module versioning

set -e

echo "🏷️  Tagging muppet modules as v1.0.0..."

# Check if we're in the right directory
if [ ! -d "terraform-modules" ]; then
    echo "❌ Error: terraform-modules directory not found. Run this script from the muppets repository root."
    exit 1
fi

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes. Please commit or stash them first."
    echo "Current status:"
    git status --short
    exit 1
fi

# Create and push the tag
echo "📝 Creating git tag v1.0.0..."
git tag -a v1.0.0 -m "Initial release of shared Terraform modules

Features:
- muppet-node-express module with Node.js 20 LTS optimizations
- muppet-java-micronaut module with Java 21 LTS optimizations
- Shared networking, fargate-service, and infrastructure modules
- TLS-by-default support
- Cost optimization based on environment
- ARM64 architecture support
- Auto-scaling and monitoring

Templates updated to use GitHub URL module references."

echo "🚀 Pushing tag to origin..."
git push origin v1.0.0

echo "✅ Successfully tagged and pushed v1.0.0!"
echo ""
echo "📋 Next steps:"
echo "   1. New muppets will automatically use the GitHub URL modules"
echo "   2. Existing muppets can be migrated to use modules during their next update"
echo "   3. Module updates can be released with new version tags (v1.1.0, v1.2.0, etc.)"
echo ""
echo "🔗 Module references in templates:"
echo "   Node.js: git::https://github.com/{{github_organization}}/muppets.git//terraform-modules/muppet-node-express?ref=v1.0.0"
echo "   Java:    git::https://github.com/{{github_organization}}/muppets.git//terraform-modules/muppet-java-micronaut?ref=v1.0.0"