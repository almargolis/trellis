+++
guid = "b3feaf02-2641-4d70-a293-9ca34fa067d0"
date-created = 2026-11-05
date-modified = 2026-11-05
sensitive = true
publish = false
draft = true
date-published = ""
slug = "claude"
publish_path = "trellis"
source_path = "/Users/almargolis/projects/published/trellis/CLAUDE.md"
+++
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

### Configuration

Trellis is always a qdstart-managed application. Path configuration comes from `conf/trellis.toml` via the `qdbase.qdconf.get_conf()` object:

- `trellis.content_dpath`: Root directory for site content, databases, and indexes (required)

The conf value is used to set `DATA_DIR`, `CONTENT_DIR`, and `GARDEN_DIR` in the Flask app config. No `.env` file or environment variables are needed for path configuration.

Optional environment variables (for non-path settings):
- `SECRET_KEY`: Flask secret key
- `SITE_NAME`: Site name displayed in header/footer (defaults to `Trellis`)
- `SITE_AUTHOR`: Author name displayed in footer (optional)
- `GITLAB_REPO_PATH`: Path to git repository for auto-commits (defaults to `.`)

### TrellisSources (Companion Tool)

TrellisSources is a **separate repository** (`trellis-sources/`) that provides the `trellis-source` CLI for publishing markdown files from source directories into Trellis gardens. It depends on `trellis-cms` for shared frontmatter handling.

**Configuration** lives in `~/.trellis/`:
- `config.toml` (legacy single-garden config)
- `sources.toml` (global settings for multi-garden mode)
- `gardens/<nickname>/config.toml` (per-garden source config)

```toml
# Example: ~/.trellis/config.toml (legacy)
default_front_matter_format = "toml"
destination_path = "/path/to/trellis/content"

[[source]]
path = "~/projects"
publish_path = "projects"
public = false
publish = false
draft = true
process = "publish"        # "publish" | "omit" | "review"

[[source]]
path = "~/projects/secret"
process = "omit"           # exclude this subtree entirely

[[source]]
path = "~/projects/published"
publish_path = "published"
public = true
publish = true
draft = false
```

**CLI commands:**
```bash
trellis-source init          # Create ~/.trellis/ structure
trellis-source add <path>    # Register a garden
trellis-source list          # List registered gardens
trellis-source process       # Add/update frontmatter (default)
trellis-source check         # Report publishing status
trellis-source publish       # Copy files to garden content tree
trellis-source publish --force  # Overwrite even if garden copy is newer
trellis-source update        # Sync changes from garden back to source
trellis-source -g <nickname> <cmd>  # Per-garden operations
```

Sources are matched longest-path-first. The `process` field replaces the old `omit` boolean (auto-migrated). File-level rules (`source_file_path`, `source_file_filter`) enable per-file publish overrides and non-markdown file publishing.

## Architecture

### Content Organization
The application uses a "digital garden" concept:
- Content is organized into **gardens** (subdirectories under `content/`)
- Each garden contains markdown files (articles)
- Each garden has a `config.yaml` defining title, description, and metadata
- Articles use YAML frontmatter for metadata (title, dates, tags)

### Core Components

**Flask Application Factory** (`trellis/__init__.py`):
- Creates app with configurable instance path for production
- Initializes database and Flask-Login
- Registers blueprints: main, editor

**Blueprints**:
- `main_bp`: Public-facing routes (gardens, articles)
- `editor_bp`: Protected content editing interface
- Authentication is delegated to `qdflaskauth`

**Data Models** (`trellis/models/`):
- `User`: Authentication with role-based access (admin/editor) via `qdflaskauth`
- `ContentIndex`: SQLite-based content metadata index (`trellis_content.db`) for wiki-links, page lookups, and public/draft filtering

**Utility Modules** (`trellis/utils/`):
- `frontmatter`: Shared frontmatter parsing/writing for YAML, TOML, JSON formats; auto-migration (`sensitive`→`public`); GUID generation; field validation and defaults. This is the single source of truth used by both Trellis and TrellisSources.
- `MarkdownHandler`: Parse/save markdown with frontmatter, render to HTML, process wiki-links and includes
- `GardenManager`: Manage garden directories, config.yaml files, nicknames, public visibility inheritance, hierarchy navigation
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
- **Data Directory**: configured via `trellis.content_dpath` in `conf/trellis.toml` (writable database and content)
- Database, content, and indexes are stored outside git repo for write permissions

This separation is configured via the conf object (`get_conf()`) which reads `conf/trellis.toml`.

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

Each markdown file uses frontmatter (YAML, TOML, or JSON). Trellis frontmatter fields:

```toml
# TOML example (also supports YAML --- and JSON {})
guid = "uuid4-string"          # Unique identifier (auto-generated)
date-created = 2024-01-01     # From filesystem on first process
date-modified = 2024-01-15    # From filesystem on process
date-published = 2024-01-01   # Set when publish=true
public = false                # Visibility (replaces old 'sensitive' field)
publish = false               # Whether file should be published to garden
draft = true                  # Draft status
slug = "article-title"        # URL slug (auto-derived from filename)
publish_path = "garden-name"  # Target garden for publishing
source_path = "/path/to/source.md"  # Original source location
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
nickname: garden_name         # Lowercase identifier (auto-derived from slug)
created_date: null
order: 999
public: true                  # Optional: sets default public visibility for all content in this garden
```

**Public Visibility Inheritance:**
- Each garden and subdirectory can set `public: true/false` in its `config.yaml`
- Files inherit from the nearest ancestor that sets public
- An explicit `public` in frontmatter overrides inheritance
- A `public: false` ancestor always overrides child settings
- `GardenManager.compute_effective_public()` resolves the final visibility

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
- `trellis/__init__.py` `create_app()` reads `trellis.content_dpath` from the conf object
- If set and absolute, uses it as Flask's instance path
- This allows SQLite database to be created outside the read-only git repo

### Frontmatter Module (`trellis/utils/frontmatter.py`)
The shared frontmatter module is the single source of truth for both Trellis and TrellisSources:
- Parses YAML (`---`), TOML (`+++`), and JSON (`{}`) frontmatter
- `ensure_required_fields()` adds missing fields (guid, dates, public, publish, draft, slug)
- Auto-migrates `sensitive` → `public` (inverted: `sensitive=true` becomes `public=false`)
- `format_frontmatter()` serializes metadata back to any format
- Obsidian format uses `permalink` instead of `slug`

### Markdown Processing
`MarkdownHandler` uses Python-Markdown with extensions:
- `fenced_code`: Code blocks with syntax highlighting
- `codehilite`: Pygments integration
- `tables`, `toc`, `footnotes`, `attr_list`: Enhanced markdown features

Before markdown conversion, the handler processes:
1. `{{include: filename}}` directives (resolved relative to the containing directory)
2. `[[Wiki Links]]` (resolved via ContentIndex with title → slug → fuzzy fallback)

### Date Auto-Updates
The `updated_date` field is automatically set to current date on every save via `DateManager.auto_update_modified()`. The `created_date` and `published_date` are manually managed.

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

## Testing

### Running Tests
```bash
source venv/bin/activate
pytest tests/ -v
```

### Test Structure
All tests use `tmp_path` fixtures to avoid touching production data:

- `tests/conftest.py`: Shared fixtures (`make_md`, `content_dir`, `data_dir`, `garden_dir`, `make_garden`)
- `tests/test_frontmatter.py`: Frontmatter parsing/writing for all formats, auto-migration, field validation
- `tests/test_garden_manager.py`: GardenManager methods, nicknames, public inheritance, hierarchy
- `tests/test_markdown_handler.py`: MarkdownHandler parsing, includes, wiki-links, save/list operations
- `tests/test_content_index.py`: ContentIndex CRUD, queries, public/draft filtering, wiki-link resolution
- `tests/test_date_manager.py`: DateManager date parsing, validation, auto-update
- `tests/test_garden_features.py`: Integration tests for garden features (nicknames, public/draft, themes)

### TrellisSources Tests
```bash
cd ../trellis-sources
pytest tests/ -v
```
- `tests/test_publisher.py`: Source scanning, frontmatter processing, publish/check/update commands
- `tests/test_cli.py`: CLI dispatch and argument handling

## Deployment

For production deployment, refer to `DEPLOYMENT.md`. Key points:
- Use `setup_production.sh` script to configure data directory
- Configure `trellis.content_dpath` in `conf/trellis.toml`
- Run under Apache/WSGI with `trellis.wsgi`
- Ensure `www-data` has write permissions to the content directory
