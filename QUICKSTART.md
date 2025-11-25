# Trellis Quick Start

## Creating a New Site

### 1. Set Up Your Site Directory

```bash
# Create your site directory
mkdir my-site
cd my-site

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Trellis

**Option A: From GitHub (during development)**
```bash
git clone https://github.com/almargolis/trellis.git
pip install -e ./trellis
```

**Option B: From PyPI (once published)**
```bash
pip install trellis-cms  # Not yet available
```

### 3. Create Site Configuration

Create `config.py`:
```python
from trellis.config import TrellisConfig

class MySiteConfig(TrellisConfig):
    SITE_NAME = "My Digital Garden"
    SITE_AUTHOR = "Your Name"
    DATA_DIR = "/path/to/data"  # Or set via environment
```

Create `.env`:
```bash
SECRET_KEY=your-secret-key-here
SITE_NAME=My Digital Garden
SITE_AUTHOR=Your Name
DATA_DIR=/path/to/your/data
```

### 4. Create Application Entry Point

Create `run.py`:
```python
from trellis import create_app
from config import MySiteConfig

if __name__ == '__main__':
    app = create_app(MySiteConfig)
    app.run(debug=True)
```

### 5. Set Up Data Directory

```bash
# Create data directory structure
mkdir -p /path/to/data/content
```

### 6. Initialize Database

```bash
trellis-init-db
```

Default credentials: `admin` / `admin` (change immediately!)

### 7. Create Your First Garden

```bash
# Create a garden directory
mkdir -p /path/to/data/content/essays

# Create config
cat > /path/to/data/content/essays/config.yaml << EOF
title: Essays
description: My thoughts and writings
order: 1
EOF

# Create first article
cat > /path/to/data/content/essays/hello.md << EOF
---
title: Hello World
published_date: 2025-01-01
---

# Hello World

This is my first post!
EOF
```

### 8. Initialize Search Index

```bash
trellis-search --rebuild
```

This builds the full-text search index from your content. Rerun this command after adding new content to update the search index.

### 9. Run Development Server

```bash
python run.py
# Visit http://localhost:5000
```

## Project Structure

```
my-site/
├── venv/                    # Virtual environment
├── trellis/                 # Trellis source (if using -e)
├── run.py                   # Application entry point
├── config.py                # Site configuration
├── .env                     # Environment variables
└── requirements.txt         # Dependencies (optional)
```

Data directory structure:
```
/path/to/data/
├── trellis_admin.db         # User database
├── trellis_content.db       # Content index
├── search_index/            # Whoosh search index
└── content/                 # Your content
    ├── essays/
    │   ├── config.yaml
    │   └── hello.md
    └── projects/
        ├── config.yaml
        └── my-project.md
```

## Minimal requirements.txt

If you want to track dependencies:
```
# Editable install of trellis
-e ./trellis

# Or from PyPI (once available):
# trellis-cms>=0.1.0
```

## Next Steps

- Read [HIERARCHICAL_CONTENT.md](HIERARCHICAL_CONTENT.md) to learn about `.page` directories
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Check [CLAUDE.md](CLAUDE.md) for development details
