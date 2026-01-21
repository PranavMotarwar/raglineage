# GitHub Repository Setup Guide

## Quick Setup (5 minutes)

### Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `raglineage`
3. Description: `Lineage-aware RAG engine for auditable, reproducible, versioned retrieval and answers`
4. Visibility: **Public**
5. **DO NOT** check any boxes (README, .gitignore, license) - we already have them
6. Click "Create repository"

### Step 2: Push Code to GitHub

```bash
cd /Users/pranavmotarwar/raglineage

# Add remote (if not already added)
git remote add origin https://github.com/PranavMotarwar/raglineage.git

# Push to GitHub
git push -u origin main
```

### Step 3: Configure Repository Settings

1. Go to repository Settings → General
2. Scroll to "Features"
3. Enable:
   - Issues
   - Discussions
   - Wiki (optional)

### Step 4: Add Repository Topics

Go to repository → Click gear icon next to "About" → Add topics:

```
rag, lineage, provenance, vector-search, nlp, llm, python, machine-learning, 
retrieval-augmented-generation, data-lineage, faiss, networkx, pydantic, 
audit-trail, version-control, semantic-search
```

### Step 5: Create First Release

1. Go to https://github.com/PranavMotarwar/raglineage/releases/new
2. Choose tag: `v0.1.0` (create new tag)
3. Release title: `raglineage v0.1.0 - Initial Release`
4. Description:

```markdown
## Initial Release: raglineage v0.1.0

The first lineage-aware RAG engine with complete provenance tracking.

### Features

- **Complete Lineage Tracking**: Every retrievable chunk tracks source, transforms, version, and hash
- **Dataset Versioning**: Track changes with file-level diffing
- **Incremental Updates**: Only recompute changed files
- **Answer Auditing**: Reconstruct provenance of any answer
- **Graph Relationships**: DAG linking nodes semantically
- **Multiple Formats**: Support for text, CSV, JSON
- **CLI Interface**: Easy-to-use command-line tools
- **Production Ready**: Persistent storage, error handling, logging

### Installation

```bash
pip install raglineage
```

### Documentation

- [README](https://github.com/PranavMotarwar/raglineage#readme)
- [Quickstart Guide](https://github.com/PranavMotarwar/raglineage#quickstart)

### Links

- PyPI: https://pypi.org/project/raglineage/
- Documentation: https://github.com/PranavMotarwar/raglineage
```

5. Click "Publish release"

### Step 6: Set Up GitHub Actions Secrets

1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Your PyPI API token (get from https://pypi.org/manage/account/token/)
5. Click "Add secret"

Now GitHub Actions will automatically publish to PyPI when you create releases!

### Step 7: Add Badges to README

The README already includes PyPI badges. After pushing, verify they work.

## Verification Checklist

- [ ] Repository created and public
- [ ] Code pushed to GitHub
- [ ] Topics added
- [ ] First release created (v0.1.0)
- [ ] GitHub Actions secrets configured
- [ ] Issues enabled
- [ ] Discussions enabled (optional)

## Next Steps

1. Share on social media
2. Submit to awesome lists
3. Post on Reddit/Hacker News
4. Write blog post
5. Engage with community
