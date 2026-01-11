# Development Setup

Guide for developers working on Trellis or its dependencies.

## For Users

If you just want to use Trellis, see the [Quick Start](../getting-started/quickstart.md) guide instead.

## For Developers

This section is for developers who want to:
- Contribute to Trellis
- Develop custom features
- Work on the codebase locally
- Develop qdflask or qdcomments packages

## Prerequisites

- Python 3.9+
- Git
- Code editor (VS Code, PyCharm, etc.)
- Basic Flask knowledge

## Clone the Repository

```bash
git clone https://github.com/almargolis/trellis.git
cd trellis
```

## Development Installation

### Option 1: Standard Development Setup

Install Trellis in editable mode:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
pip install -e .
pip install -e ".[dev]"
```

This installs:
- Trellis in editable mode (changes take effect immediately)
- All dependencies from PyPI (including qdflask, qdcomments)
- Development tools (pytest, pytest-cov)

### Option 2: Full Development Setup (Working on Dependencies)

--8<-- "includes/quickdev-dev-setup.md"

### Option 3: Development with Local qdbase

If you need to work on qdbase as well:

```bash
# In Trellis virtual environment
source venv/bin/activate

# Install qdbase in editable mode
pip install -e ../quickdev/qdbase
pip install -e ../quickdev/qdflask
pip install -e ../quickdev/qdcomments

# Install Trellis
pip install -e .
```

## Initial Setup

### Initialize Test Data

```bash
# Create test data directory
mkdir test-site
cd test-site

# Initialize database
trellis-init-db

# Create sample garden
mkdir -p content/blog
cat > content/blog/config.yaml <<EOF
title: Test Blog
description: Test content for development
created_date: null
order: 1
EOF

# Create sample article
cat > content/blog/test.md <<'EOF'
---
title: Test Article
published_date: 2026-01-09
tags: [test]
status: published
---

This is a test article.
EOF

# Build search index
trellis-search --rebuild

# Return to trellis directory
cd ..
```

### Configure Environment

Create `.env` in your test-site directory:

```bash
SECRET_KEY=dev-secret-key-change-in-production
SITE_NAME=Trellis Dev
SITE_AUTHOR=Developer
DEBUG=True
DATA_DIR=.
```

## Running Development Server

### Option 1: Flask CLI

```bash
cd test-site
python -m flask --app trellis run --debug
```

### Option 2: Custom run.py

Create `test-site/run.py`:

```python
from trellis import create_app
import os

# Point to this directory
os.environ['DATA_DIR'] = os.path.dirname(os.path.abspath(__file__))

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

Run it:
```bash
cd test-site
python run.py
```

## Project Structure

```
trellis/
  trellis/                 # Main package
    __init__.py           # App factory
    routes.py             # Route handlers
    config.py             # Configuration
    cli.py                # CLI commands
    models/               # Database models
      __init__.py
      user.py
      comment.py
    utils/                # Utility modules
      markdown_handler.py
      garden_manager.py
      git_handler.py
      search_handler.py
      date_manager.py
      index_manager.py
    templates/            # Jinja2 templates
    static/               # CSS, JavaScript
  tests/                  # Test suite
  docs/                   # MkDocs documentation
  mkdocs.yml             # MkDocs config
  pyproject.toml         # Package configuration
  README.md
  CLAUDE.md              # Developer guide
```

## Development Workflow

### Making Changes

```bash
# Make changes to code
vim trellis/routes.py

# Changes take effect immediately (editable install)
# Restart Flask server to see changes

# Test manually
# Visit http://localhost:5000
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=trellis

# Run specific test
pytest tests/test_routes.py::test_garden_view

# Run with verbose output
pytest -v
```

### Code Style

```bash
# Install development tools
pip install flake8 black isort

# Check style
flake8 trellis/

# Format code
black trellis/
isort trellis/
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "Add my feature"

# Push to GitHub
git push origin feature/my-feature

# Create pull request on GitHub
```

## Database Development

### SQLite Browser

```bash
# Install SQLite browser (optional)
brew install --cask db-browser-for-sqlite  # macOS

# Open database
open trellis_admin.db
```

### Database Migrations

Currently, Trellis uses simple schema creation via `db.create_all()`. For future migrations:

```python
# In trellis/cli.py
def upgrade_database():
    """Apply database migrations"""
    # Migration logic here
    pass
```

### Reset Database

```bash
cd test-site
rm trellis_admin.db trellis_content.db
rm -rf search_index/
trellis-init-db
trellis-search --rebuild
```

## Debugging

### Flask Debug Mode

In `run.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

Enables:
- Auto-reload on code changes
- Interactive debugger in browser
- Detailed error pages

### Logging

Add logging to your code:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Processing article: %s", article_path)
logger.error("Failed to save: %s", error)
```

Configure logging level:

```python
# In create_app()
logging.basicConfig(level=logging.DEBUG)
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "trellis",
        "FLASK_ENV": "development",
        "DATA_DIR": "${workspaceFolder}/test-site"
      },
      "args": ["run", "--debug", "--no-reload"],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### PyCharm Debugging

1. Create Flask run configuration
2. Set module: `flask`
3. Set parameters: `run --debug`
4. Set environment variable: `DATA_DIR=/path/to/test-site`

## Testing

### Writing Tests

Create test in `tests/`:

```python
# tests/test_markdown_handler.py
import pytest
from trellis.utils.markdown_handler import MarkdownHandler

def test_parse_frontmatter():
    content = """---
title: Test
---
Body"""

    handler = MarkdownHandler("/tmp")
    metadata, body = handler.parse_file_content(content)

    assert metadata['title'] == "Test"
    assert body.strip() == "Body"
```

Run it:
```bash
pytest tests/test_markdown_handler.py
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
import tempfile
import os

@pytest.fixture
def temp_content_dir():
    """Create temporary content directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up test content
        os.makedirs(f"{tmpdir}/blog")
        with open(f"{tmpdir}/blog/config.yaml", 'w') as f:
            f.write("title: Test\ndescription: Test\n")

        yield tmpdir
```

Use in tests:
```python
def test_garden_list(temp_content_dir):
    manager = GardenManager(temp_content_dir)
    gardens = manager.list_gardens()
    assert len(gardens) > 0
```

## Documentation Development

### Building Docs

```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Serve docs locally
mkdocs serve

# Visit http://localhost:8000

# Build static docs
mkdocs build
```

### Documentation Structure

```
docs/
  index.md                      # Home page
  getting-started/
    quickstart.md
    installation.md
    first-garden.md
  content/
    writing.md
    structure.md
    wiki-links.md
    page-directories.md
  maintenance/
    backup.md
    indexing.md
    updates.md
  reference/
    architecture.md
    development.md              # This file
    deployment.md
    api.md
```

## Dependencies

### Runtime Dependencies

Defined in `pyproject.toml`:

```toml
dependencies = [
    "Flask>=3.0.0",
    "Flask-Login>=0.6.3",
    "Flask-SQLAlchemy>=3.1.1",
    "Markdown>=3.5.1",
    "Pygments>=2.17.2",
    "python-dotenv>=1.0.0",
    "PyYAML>=6.0.1",
    "GitPython>=3.1.40",
    "python-frontmatter>=1.1.0",
    "Werkzeug>=3.0.0",
    "Whoosh>=2.7.4",
    "qdflask",
    "qdcomments",
]
```

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "flake8>=6.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
]
```

### Updating Dependencies

```bash
# Update all dependencies
pip install --upgrade -e .

# Update specific dependency
pip install --upgrade Flask

# Check for outdated packages
pip list --outdated
```

## Contributing

### Before Submitting PR

- [ ] Run tests: `pytest`
- [ ] Check code style: `flake8 trellis/`
- [ ] Format code: `black trellis/ && isort trellis/`
- [ ] Update documentation if needed
- [ ] Add tests for new features
- [ ] Update CHANGELOG.md

### Commit Messages

Follow conventional commits:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
test: Add tests
refactor: Refactor code
chore: Update dependencies
```

Examples:
```
feat: Add wiki-link support
fix: Resolve search indexing race condition
docs: Add backup strategy guide
```

## Release Process

### Creating a Release

```bash
# Update version in pyproject.toml (setuptools_scm uses git tags)

# Commit changes
git add .
git commit -m "Prepare v0.3.0 release"

# Create tag
git tag -a v0.3.0 -m "Release v0.3.0"

# Push tag
git push origin v0.3.0

# Build distribution
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

### Publishing qdflask/qdcomments

Before publishing Trellis, ensure dependencies are on PyPI:

```bash
# In quickdev/qdflask
python setup.py sdist bdist_wheel
twine upload dist/*

# In quickdev/qdcomments
python setup.py sdist bdist_wheel
twine upload dist/*
```

## Troubleshooting Development Issues

### Import Errors

```bash
# Reinstall in editable mode
pip uninstall trellis-cms
pip install -e .

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### Database Locked

```bash
# Kill running processes
pkill -f "python.*trellis"

# Remove lock files
rm *.db-journal
```

### Git Conflicts

```bash
# Stash changes
git stash

# Pull latest
git pull origin main

# Reapply changes
git stash pop
```

## Next Steps

- **[Architecture](architecture.md)** - System design
- **[Deployment](deployment.md)** - Production setup
- **[API Reference](api.md)** - Code documentation
