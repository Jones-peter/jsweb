#!/bin/bash
# Pre-commit hooks setup script for jsweb
# This script sets up pre-commit hooks to automatically run code quality checks

set -e

echo "🔧 Setting up pre-commit hooks for jsweb..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
fi

# Install the git hooks
echo "📝 Installing git pre-commit hooks..."
pre-commit install
pre-commit install --hook-type pre-push

# Optional: Run all hooks on all files to check current state
echo "🔍 Running hooks on all files (this may take a moment)..."
pre-commit run --all-files || true

echo "✅ Pre-commit hooks setup complete!"
echo ""
echo "📚 Usage:"
echo "  - Hooks will run automatically before each commit"
echo "  - Run manually: pre-commit run --all-files"
echo "  - Skip hooks: git commit --no-verify"
echo "  - Update hooks: pre-commit autoupdate"
echo ""
