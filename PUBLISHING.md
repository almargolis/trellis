# Publishing Checklist

Steps to publish Trellis and its dependencies to PyPI.

## Current Status

- ✅ Trellis is published to PyPI as `trellis-cms` (v0.2.1)
- ❌ qdflask is NOT on PyPI (temporary GitHub install required)
- ❌ qdcomments is NOT on PyPI (temporary GitHub install required)

## Why This Matters

Trellis depends on qdflask and qdcomments. Until these are on PyPI:

**Current installation (temporary):**
```bash
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdflask
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdcomments
pip install trellis-cms
```

**Goal installation (once on PyPI):**
```bash
pip install trellis-cms  # Automatically installs qdflask and qdcomments
```

## Step 1: Publish qdflask to PyPI

```bash
cd /Users/almargolis/Projects/quickdev/qdflask

# Ensure README.md and setup.py are up to date
cat README.md
cat setup.py

# Build distribution
python setup.py sdist bdist_wheel

# Check the built packages
ls -la dist/

# Upload to PyPI (test first)
twine upload --repository testpypi dist/*

# Test installation from test PyPI
pip install --index-url https://test.pypi.org/simple/ qdflask

# If successful, upload to production PyPI
twine upload dist/*
```

## Step 2: Publish qdcomments to PyPI

```bash
cd /Users/almargolis/Projects/quickdev/qdcomments

# Ensure README.md and setup.py are up to date
cat README.md
cat setup.py

# Build distribution
python setup.py sdist bdist_wheel

# Check the built packages
ls -la dist/

# Upload to PyPI (test first)
twine upload --repository testpypi dist/*

# Test installation from test PyPI
pip install --index-url https://test.pypi.org/simple/ qdcomments

# If successful, upload to production PyPI
twine upload dist/*
```

## Step 3: Update Trellis Documentation

Once qdflask and qdcomments are on PyPI, update documentation:

### Remove temporary warnings from:
- `docs/getting-started/quickstart.md`
- `docs/getting-started/installation.md`
- `docs/reference/deployment.md`

Change from:
```bash
# Install dependencies from GitHub
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdflask
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdcomments
pip install trellis-cms
```

To:
```bash
pip install trellis-cms
```

## Step 4: Release Trellis v0.3.0

```bash
cd /Users/almargolis/Projects/trellis

# Ensure all changes are committed
git status

# Commit documentation
git add docs/ mkdocs.yml
git commit -m "Add comprehensive MkDocs documentation"

# Create version tag
git tag -a v0.3.0 -m "Release v0.3.0: Comprehensive documentation and improved installation"

# Push tag
git push origin v0.3.0

# Build distribution
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Step 5: Deploy Documentation

```bash
# Deploy to GitHub Pages
mkdocs gh-deploy
```

Documentation will be available at: `https://almargolis.github.io/trellis/`

## Step 6: Update README.md

Update main README.md to point to new documentation:

```markdown
## Documentation

Full documentation available at: https://almargolis.github.io/trellis/

- [Quick Start](https://almargolis.github.io/trellis/getting-started/quickstart/)
- [Installation](https://almargolis.github.io/trellis/getting-started/installation/)
- [Deployment](https://almargolis.github.io/trellis/reference/deployment/)
```

## Verification Checklist

After publishing:

- [ ] `pip install trellis-cms` works without GitHub URLs
- [ ] `trellis-init-db` command is available
- [ ] `trellis-search --rebuild` works
- [ ] Documentation builds without errors
- [ ] GitHub Pages shows documentation correctly
- [ ] PyPI page shows correct description and links

## Testing Installation

Create a clean test environment:

```bash
# Create new virtual environment
python3 -m venv test-install
source test-install/bin/activate

# Install Trellis (should pull dependencies automatically)
pip install trellis-cms

# Verify commands
trellis-init-db --help
trellis-search --help

# Test basic functionality
mkdir test-site
cd test-site
trellis-init-db

# Clean up
cd ..
rm -rf test-install test-site
```

## Rollback Plan

If there are issues after publishing:

1. **Unpublish from PyPI** (within 72 hours)
   ```bash
   # PyPI doesn't support unpublishing, but you can yank versions
   # This hides them but doesn't delete
   ```

2. **Revert git tags**
   ```bash
   git tag -d v0.3.0
   git push origin :refs/tags/v0.3.0
   ```

3. **Fix issues and re-release** as v0.3.1

## Notes

- PyPI doesn't allow re-uploading the same version number
- Once published, a version cannot be deleted (only yanked)
- Test on TestPyPI first when possible
- Keep qdflask and qdcomments versions in sync if they depend on each other

## Alternative: Keep Dependencies Private

If you don't want to publish qdflask/qdcomments to PyPI, you can:

1. **Use Git URLs in pyproject.toml** (not recommended for public packages):
   ```toml
   dependencies = [
       "qdflask @ git+https://github.com/almargolis/quickdev.git#subdirectory=qdflask",
       "qdcomments @ git+https://github.com/almargolis/quickdev.git#subdirectory=qdcomments",
   ]
   ```

2. **Bundle the code** - Move qdflask/qdcomments code into trellis package (more maintenance)

3. **Document manual installation** - Keep current temporary installation process

**Recommendation:** Publish to PyPI for best user experience.
