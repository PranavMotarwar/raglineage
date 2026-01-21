#!/bin/bash
# Quick script to push raglineage to GitHub

echo "🚀 Pushing raglineage to GitHub..."
echo ""

# Check if remote exists
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "Adding GitHub remote..."
    git remote add origin https://github.com/PranavMotarwar/raglineage.git
else
    echo "Remote already configured:"
    git remote -v
fi

echo ""
echo "📤 Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Done! Repository: https://github.com/PranavMotarwar/raglineage"
