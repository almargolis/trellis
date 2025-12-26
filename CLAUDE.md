# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Trellis** is a Flask-based digital garden and hierarchical content management system. It features markdown content management, user authentication, Git integration, and support for hierarchical `.page` directories. Content is organized into "gardens" (topic-based directories) with a built-in editor interface for content management.

The name "Trellis" reflects the system's hierarchical structure - like a garden trellis that supports and organizes growing plants, this CMS provides a framework for organizing and growing digital content.

## Development Setup

### Initial Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install trellis
pip install -e .

# Initialize database
trellis-init-db

# Initialize search index (after adding content)
trellis-search --rebuild
```

Default admin credentials after init: `admin` / `admin` (change immediately)

### Running the Application
```bash
# Development server
python run.py
# Server runs on http://localhost:5000
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
- `SECRET_KEY`: Flask secret key
- `SITE_NAME`: Site name displayed in header/footer (defaults to `Trellis`)
- `SITE_AUTHOR`: Author name displayed in footer (optional)
- `DATA_DIR`: Directory for database and writable content (required)
- `CONTENT_DIR`: Directory for markdown content (defaults to `DATA_DIR/content`)
- `GITLAB_REPO_PATH`: Path to git repository for auto-commits (defaults to `.`)

## Architecture

### Content Organization
The application uses a "digital garden" concept:
- Content is organized into **gardens** (subdirectories under `content/`)
- Each garden contains markdown files (articles)
- Each garden has a `config.yaml` defining title, description, and metadata
- Articles use YAML frontmatter for metadata (title, dates, tags)

### Core Components

**Flask Application Factory** (`app/__init__.py`):
- Creates app with configurable instance path for production
- Initializes database and Flask-Login
- Registers three blueprints: main, editor, auth

**Blueprints**:
- `main_bp`: Public-facing routes (gardens, articles)
- `editor_bp`: Protected content editing interface
- `auth_bp`: Authentication and user management

**Data Models** (`app/models.py`):
- `User`: Authentication with role-based access (admin/editor)
- Uses Flask-SQLAlchemy with SQLite by default
- Password hashing via werkzeug

**Utility Modules** (`app/utils/`):
- `MarkdownHandler`: Parse/save markdown with frontmatter, render to HTML
- `GardenManager`: Manage garden directories and config.yaml files
- `GitHandler`: Auto-commit changes using GitPython
- `DateManager`: Handle article date metadata (created/published/updated)

### Data Flow for Content Editing

1. User edits article via `/editor/edit/<garden_slug>/<slug>` route
2. JavaScript sends POST to `/editor/save` with metadata and content
3. `DateManager.auto_update_modified()` updates the `updated_date`
4. `MarkdownHandler.save_file()` writes markdown with frontmatter
5. `GitHandler.auto_commit()` commits the change to git
6. Frontend receives updated metadata (including new dates)

### Production Architecture

Production uses a separate data directory structure:
- **Repository**: `/var/www/trellis/` (read-only code)
- **Data Directory**: `/var/www/trellis_data/` (writable database and content)
- Database and content are stored outside git repo for write permissions

This separation is configured via `DATA_DIR` and `CONTENT_DIR` environment variables.

## Common Tasks

### Database Operations
```bash
# Initialize or reset database
python init_db.py

# The database schema is auto-created on app startup via db.create_all()
```

### Content Structure

The application supports two content formats:

1. **Flat files** (traditional): `article.md` in a garden directory
2. **Page directories** (new): `article.page/page.md` for hierarchical content

Each markdown file should have YAML frontmatter:
```yaml
---
title: Article Title
published_date: 2024-01-01
updated_date: 2024-01-15
tags: [python, flask]
status: published
---
```

**Page directories** (`.page`) allow:
- Unlimited nesting depth: `project.page/setup.page/advanced.page/`
- Page-specific assets: images, code files stored alongside content
- Include files: Use `{{include: filename}}` syntax to include content from other files
- Clean URLs: `.page` extension is stripped (e.g., `/garden/projects/article`)

### Index Management

Trellis maintains two indexes that must be kept in sync with content changes:
1. **Search Index** (Whoosh): Full-text search across all content
2. **Content Index** (trellis_content.db): Metadata cache for wiki-links and queries

**Automatic Updates (Default):**
- When content is saved/created via the web editor, indexes update immediately
- Single-file updates are fast (milliseconds)
- No manual intervention needed

**Deferred Updates (Optional):**
For high-traffic sites with multiple concurrent editors:
```bash
# Enable deferred mode via environment variable
export TRELLIS_DEFERRED_INDEXING=true

# Set up cron job to rebuild periodically (e.g., every 5 minutes)
*/5 * * * * cd /var/www/trellis && trellis-index-update
```

**Manual Commands:**
```bash
# Check if rebuild needed and rebuild if dirty
trellis-index-update

# Force rebuild regardless of dirty flag
trellis-index-update --force

# Rebuild search index only
trellis-search --rebuild

# Rebuild content index only
trellis-index --clear

# Show statistics
trellis-search --stats
trellis-index --stats
```

**How It Works:**
- `IndexManager` class coordinates both indexes
- Immediate mode: Updates happen after each save/create
- Deferred mode: Sets `.index_dirty` flag, cron job checks and rebuilds
- Incremental updates: Only changed files are re-indexed

### Backup Strategies

**For Text Content (Markdown, YAML, Code):**
Git version control is recommended and enabled by default:
```bash
# Auto-commits happen on every save via GitHandler
# Configure git repository path
export GITLAB_REPO_PATH=/path/to/content

# Manual git operations
cd /path/to/content
git log                    # View history
git push origin main       # Push to remote
```

**For Binary Content (Images, PDFs):**
Git is not ideal for large binary files. Consider:

1. **Git with LFS** (for moderate binary content):
```bash
cd /path/to/content
git lfs install
git lfs track "*.png" "*.jpg" "*.pdf"
git add .gitattributes
```

2. **Rsync for Full Backups** (recommended for mixed content):
```bash
# Daily backup to external location
rsync -av --delete /var/www/trellis_data/ /backup/trellis_data/

# Exclude git repo from binary backups
rsync -av --delete --exclude='.git' /var/www/trellis_data/content/ /backup/content/
```

3. **Hybrid Approach** (best for most sites):
- Keep git for text content version control
- Add binary files to `.gitignore`
- Use rsync/tar for periodic full backups
- Consider cloud storage (S3, BackBlaze) for off-site backups

**Example .gitignore for Hybrid Approach:**
```gitignore
# Database files (handled by rsync)
*.db
*.db-journal

# Large binary content
*.png
*.jpg
*.jpeg
*.gif
*.pdf
*.zip
*.tar.gz

# Search index (rebuilt from content)
search_index/

# Keep text content in git
!*.md
!*.yaml
!*.yml
!*.py
!*.js
!*.css
!*.html
```

**Backup Script Example:**
```bash
#!/bin/bash
# backup-trellis.sh

DATA_DIR="/var/www/trellis_data"
BACKUP_DIR="/backup/trellis/$(date +%Y%m%d)"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
cp "$DATA_DIR"/*.db "$BACKUP_DIR/"

# Backup full content (including binaries)
rsync -av "$DATA_DIR/content/" "$BACKUP_DIR/content/"

# Commit and push text content to git
cd "$DATA_DIR/content"
git add -A
git commit -m "Automated backup: $(date)"
git push origin main

# Keep last 7 days of full backups
find /backup/trellis/ -maxdepth 1 -mtime +7 -type d -exec rm -rf {} \;
```

**Restoration:**
```bash
# Restore from rsync backup
rsync -av /backup/trellis/20240115/ /var/www/trellis_data/

# Rebuild indexes after restore
trellis-search --rebuild
trellis-index --clear
```

### Wiki-Links for Internal Linking

Trellis supports wiki-style linking for easy cross-referencing between pages:

**Syntax:**
```markdown
[[Page Title]]              # Link by exact title (case-insensitive)
[[page-slug]]               # Link by slug or path
[[garden/page-slug]]        # Garden-specific slug
[[Page Title|Custom Text]]  # Custom display text
```

**How it works:**
- Links are resolved at render time using `trellis_content.db` for fast lookups
- The system tries multiple resolution strategies:
  1. Exact title match (case-insensitive)
  2. URL slug match
  3. Fuzzy title match as fallback
- Resolved links become standard markdown: `[text](url)`
- Broken links are shown with red styling and tracked

**Examples:**
```markdown
See [[Getting Started]] for basics.
Learn about [[python/decorators|Python decorators]].
Check the [[API Reference]].
```

**Broken Links:**
- Displayed with red background and dashed underline
- Preserve original `[[...]]` syntax for easy identification
- Hover shows "Page not found: {target}" tooltip

**When to use:**
- Prefer wiki-links for internal references (resilient to URL changes)
- Use standard markdown links for external URLs
- Wiki-links work across all gardens

**Note:** Links are resolved when pages are rendered. To use wiki-links, ensure your content is indexed with `trellis-search --rebuild`.

Each garden directory should have `config.yaml`:
```yaml
title: Garden Display Name
description: Brief description
created_date: null
order: 999
```

See `HIERARCHICAL_CONTENT.md` for detailed documentation on the hierarchical structure.

### User Management
Users are managed via:
- `/auth/users` - List all users (admin only)
- `/auth/users/add` - Create new user (admin only)
- `/auth/users/edit/<id>` - Edit user (admin only)
- `/auth/change-password` - Change own password

### Git Integration
The app auto-commits content changes to git. To enable:
1. Ensure `GITLAB_REPO_PATH` points to a valid git repo
2. Content saves trigger commits via `GitHandler.auto_commit()`
3. Manual push/pull operations are available via `GitHandler` methods

## Important Implementation Details

### Instance Path Configuration
The Flask app uses a custom instance path in production to ensure the database is writable:
- `app/__init__.py:17-20` checks for `DATA_DIR` environment variable
- If set and absolute, uses it as instance path
- This allows SQLite database to be created outside the read-only git repo

### Markdown Processing
`MarkdownHandler` uses Python-Markdown with extensions:
- `fenced_code`: Code blocks with syntax highlighting
- `codehilite`: Pygments integration
- `tables`, `toc`, `footnotes`, `attr_list`: Enhanced markdown features

The handler resets between conversions by creating new `markdown.Markdown()` instances.

### Date Auto-Updates
The `updated_date` field is automatically set to current date on every save via `DateManager.auto_update_modified()` at `app/routes.py:282`. The `created_date` and `published_date` are manually managed.

### Hierarchical Content Architecture

The application supports two content models that work side-by-side:

**Traditional flat files**: `content/garden/article.md`
**Hierarchical pages**: `content/garden/article.page/page.md` with unlimited nesting

Key implementation details:
- `MarkdownHandler.parse_file()` detects `.page` directories and reads `page.md` inside them
- `MarkdownHandler._process_includes()` processes `{{include: filename}}` syntax before markdown conversion
- `MarkdownHandler.list_articles()` finds both `.md` files and `.page` directories recursively
- `MarkdownHandler.generate_slug()` strips `.page` extensions from paths for clean URLs
- `routes.article()` uses Flask's `path` converter to support arbitrary nesting depth
- `routes.page_asset()` serves static files from `.page` directories with path validation
- `GardenManager.get_hierarchy()` builds tree structure for navigation
- `GardenManager.get_breadcrumbs()` generates breadcrumb trails for nested pages

Include files are resolved relative to the directory containing `page.md`. Assets are served via `/garden/<garden>/<path>/assets/<filename>`.

### URL Routing Pattern
- Public:
  - `/` → gardens index
  - `/garden/<slug>` → garden view
  - `/garden/<slug>/<path:article_path>` → article (supports nesting like `project/setup/advanced`)
  - `/garden/<slug>/<path:article_path>/assets/<filename>` → page-specific assets
- Editor: `/editor/` → dashboard, `/editor/edit/<garden>/<path:article_path>` → edit interface
- Auth: `/auth/login`, `/auth/logout`, `/auth/change-password`, `/auth/users/*`

## Testing Notes

This codebase does not currently have automated tests. When adding features:
- Test both logged-in and logged-out states
- Verify admin vs editor role permissions
- Check markdown rendering with various frontmatter combinations
- Test git auto-commit functionality
- Verify database writes work in both dev and production configurations

## Deployment

For production deployment, refer to `DEPLOYMENT.md`. Key points:
- Use `setup_production.sh` script to configure data directory
- Set production environment variables in `.env`
- Run under Apache/WSGI with `trellis.wsgi`
- Ensure `www-data` has write permissions to `DATA_DIR`
