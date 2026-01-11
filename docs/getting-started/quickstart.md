# Quick Start

Get your digital garden running in under 5 minutes.

## Prerequisites - DevOps

--8<-- "quick_start_devops.md"

## Prerequisites - Your Trellis App

- Python 3.9 or higher
- pip (Python package installer)

!!! note "First Time?"
    If you've never used Python before, see the [detailed installation guide](installation.md).

## Installation

### Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv trellis-env

# Activate it
source trellis-env/bin/activate  # Linux/macOS
# OR
trellis-env\Scripts\activate     # Windows
```

### Install Trellis

!!! warning "Temporary Installation Steps"
    Until qdflask and qdcomments are published to PyPI, you need to install them from GitHub first:

```bash
# Install dependencies from GitHub
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdflask
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdcomments

# Install Trellis
pip install trellis-cms
```

!!! info "Future Simplified Installation"
    Once dependencies are on PyPI, this will simply be:
    ```bash
    pip install trellis-cms
    ```

## Initialize Your Site

Create a new directory for your site and initialize the database:

```bash
# Create a data directory
mkdir my-garden
cd my-garden

# Initialize the database
trellis-init-db
```

This creates:
- `trellis_admin.db` - User accounts and settings
- `content/` - Directory for your markdown files

Default login: `admin` / `admin` (change this immediately!)

## Create Your First Garden

A "garden" is a collection of related articles (like a blog category). Create one:

```bash
mkdir -p content/blog
```

Create a garden configuration file `content/blog/config.yaml`:

```yaml
title: My Blog
description: Thoughts and musings
created_date: null
order: 1
```

## Write Your First Post

Create `content/blog/hello-world.md`:

```markdown
---
title: Hello World
published_date: 2026-01-09
tags: [welcome, intro]
status: published
---

Welcome to my digital garden! This is my first post.

I can write in **markdown** with all the usual formatting:

- Lists
- **Bold** and *italic*
- [Links](https://example.com)
- Code blocks

```python
def hello():
    print("Hello from Trellis!")
```

And I can link to other pages using wiki-style links: [[Another Page]]
```

## Initialize Search

Build the search index so your content is discoverable:

```bash
trellis-search --rebuild
```

## Run Your Site

Start the development server:

```bash
python -m flask --app trellis run
```

Or create a simple `run.py` file:

```python
from trellis import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

Then run:

```bash
python run.py
```

Visit `http://localhost:5000` in your browser!

## First Steps

1. **Login**: Click "Login" and use `admin` / `admin`
2. **Change Password**: Go to your profile and change the default password
3. **Create Content**: Click "Editor" to access the web-based editor
4. **Customize**: Edit `content/blog/config.yaml` to change your garden's title

## What's Next?

- **[Writing Content](../content/writing.md)** - Learn markdown and frontmatter
- **[Content Structure](../content/structure.md)** - Organize multiple gardens
- **[Backup Strategy](../maintenance/backup.md)** - Protect your content

## Environment Variables

For production deployment, create a `.env` file:

```bash
SECRET_KEY=your-secret-key-here
SITE_NAME=My Digital Garden
SITE_AUTHOR=Your Name
DATA_DIR=/path/to/data
```

See [Deployment](../reference/deployment.md) for production setup details.

## Troubleshooting

**Port already in use?**

```bash
python -m flask --app trellis run --port 5001
```

**Can't find trellis module?**

Make sure you installed it: `pip install trellis-cms`

**Search not working?**

Rebuild the search index: `trellis-search --rebuild`
