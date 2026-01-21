#!/bin/bash
# Setup script for GitHub repository

set -e

REPO_NAME="raglineage"
GITHUB_USER="PranavMotarwar"

echo "🚀 Setting up GitHub repository for $REPO_NAME"
echo "=============================================="

# Check if remote already exists
if git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️  Remote 'origin' already exists"
    git remote -v
    read -p "Update remote? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote set-url origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    fi
else
    echo "📦 Adding GitHub remote..."
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
fi

echo ""
echo "📋 Next steps:"
echo ""
echo "1. Create repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Repository name: $REPO_NAME"
echo "   - Description: Lineage-aware RAG engine for auditable, reproducible, versioned retrieval"
echo "   - Visibility: Public"
echo "   - DO NOT initialize with README, .gitignore, or license (we already have them)"
echo ""
echo "2. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "3. Or use GitHub CLI (if installed):"
echo "   gh repo create $GITHUB_USER/$REPO_NAME --public --source=. --remote=origin --push"
echo ""
echo "4. After pushing, add topics on GitHub:"
echo "   - rag, lineage, provenance, vector-search, nlp, llm, python, machine-learning"
echo ""
echo "5. Create first release:"
echo "   - Go to https://github.com/$GITHUB_USER/$REPO_NAME/releases/new"
echo "   - Tag: v0.1.0"
echo "   - Title: raglineage v0.1.0 - Initial Release"
echo "   - Description: See CHANGELOG.md or commit messages"
echo ""

read -p "Push to GitHub now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pushing to GitHub..."
    git push -u origin main || echo "⚠️  Push failed. Make sure repository exists on GitHub first."
fi

echo ""
echo "✅ Setup complete!"
