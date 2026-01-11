# Architecture

System architecture and design of Trellis CMS.

## Overview

Trellis is a Flask-based digital garden CMS with a focus on simplicity, markdown content, and hierarchical organization.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Web Browser                       │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/HTTPS
┌────────────────────┴────────────────────────────────┐
│              Web Server (Apache/Nginx)              │
└────────────────────┬────────────────────────────────┘
                     │ WSGI
┌────────────────────┴────────────────────────────────┐
│                 Flask Application                   │
│  ┌──────────────────────────────────────────────┐  │
│  │            Blueprints                        │  │
│  │  • main_bp (public routes)                   │  │
│  │  • editor_bp (content editing)               │  │
│  │  • auth_bp (authentication)                  │  │
│  │  • comments_bp (commenting)                  │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │         Utility Modules                      │  │
│  │  • MarkdownHandler (content processing)      │  │
│  │  • GardenManager (directory management)      │  │
│  │  • SearchHandler (full-text search)          │  │
│  │  • GitHandler (version control)              │  │
│  │  • IndexManager (index coordination)         │  │
│  └──────────────────────────────────────────────┘  │
└───────────┬──────────────────────┬──────────────────┘
            │                      │
┌───────────┴──────────┐   ┌──────┴──────────────────┐
│   SQLite Databases   │   │    File System          │
│  • trellis_admin.db  │   │  • content/ (markdown)  │
│  • trellis_content.db│   │  • search_index/        │
└──────────────────────┘   └─────────────────────────┘
```

## Application Factory Pattern

Trellis uses Flask's application factory pattern for flexibility:

```python
# trellis/__init__.py
def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Configure app
    app.config.from_object('trellis.config.Config')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(editor_bp, url_prefix='/editor')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
```

**Benefits:**
- Multiple app instances for testing
- Different configs for dev/staging/prod
- Easy to extend and customize

## Blueprints

### main_bp (Public Routes)

**Purpose:** Public-facing content views

**Routes:**
- `/` - Garden index
- `/garden/<slug>` - Garden view
- `/garden/<slug>/<path:article_path>` - Article view
- `/garden/<slug>/<path:article_path>/assets/<filename>` - Page assets
- `/search` - Search results

**Key Features:**
- Read-only access (no authentication required)
- Markdown rendering with wiki-links
- Search functionality
- Breadcrumb navigation

### editor_bp (Content Editing)

**Purpose:** Content management interface

**Routes:**
- `/editor/` - Editor dashboard
- `/editor/edit/<garden>/<path:article_path>` - Edit article
- `/editor/save` - Save article (AJAX)
- `/editor/create` - Create article
- `/editor/delete` - Delete article

**Key Features:**
- Login required (`@login_required`)
- AJAX-based saving
- Automatic git commits
- Frontmatter editing
- Index updates

### auth_bp (Authentication)

**Purpose:** User management and authentication

**Routes:**
- `/auth/login` - Login page
- `/auth/logout` - Logout
- `/auth/change-password` - Change password
- `/auth/users` - User management (admin only)
- `/auth/users/add` - Add user (admin only)
- `/auth/users/edit/<id>` - Edit user (admin only)

**Key Features:**
- Flask-Login integration
- Role-based access (admin/editor)
- Password hashing
- Session management

### comments_bp (Commenting)

**Purpose:** User comments on articles

**Provided by:** qdcomments package

**Features:**
- Comment posting and moderation
- Spam filtering
- Email notifications
- Comment approval workflow

## Data Models

### User Model

```python
class User(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255))
    role = Column(String(20), default='editor')  # 'admin' or 'editor'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Roles:**
- **Admin:** Full access (users, settings, content)
- **Editor:** Content editing only

### Content Model (Metadata Cache)

```sql
-- trellis_content.db
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    garden_slug TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content TEXT,
    published_date TEXT,
    created_date TEXT,
    updated_date TEXT,
    tags TEXT,
    status TEXT,
    UNIQUE(garden_slug, slug)
);
```

**Purpose:**
- Fast lookups for wiki-link resolution
- Metadata queries without file I/O
- Search result metadata

## Content Processing Pipeline

### Reading Content

```
1. Request: /garden/blog/article
                    ↓
2. GardenManager.get_article_path()
   → Resolves to: content/blog/article.md
                    ↓
3. MarkdownHandler.parse_file()
   → Reads file
   → Parses YAML frontmatter
   → Returns metadata + body
                    ↓
4. MarkdownHandler._process_includes()
   → Processes {{include: filename}}
                    ↓
5. MarkdownHandler.convert_markdown()
   → Converts markdown to HTML
   → Processes wiki-links
                    ↓
6. Template rendering
   → Jinja2 template with HTML content
```

### Saving Content

```
1. Editor: POST /editor/save
   { metadata: {...}, content: "..." }
                    ↓
2. DateManager.auto_update_modified()
   → Sets updated_date to now
                    ↓
3. MarkdownHandler.save_file()
   → Combines frontmatter + content
   → Writes to .md file
                    ↓
4. GitHandler.auto_commit()
   → git add
   → git commit -m "Update: article.md"
                    ↓
5. IndexManager.update_single_file()
   → Updates search index
   → Updates content index
                    ↓
6. Response: { success: true, metadata: {...} }
```

## Utility Modules

### MarkdownHandler

**Purpose:** Markdown processing and file I/O

**Key Methods:**
- `parse_file(file_path)` - Read and parse markdown with frontmatter
- `save_file(file_path, metadata, content)` - Write markdown file
- `convert_markdown(text)` - Convert markdown to HTML
- `list_articles(garden_path)` - Find all articles in garden
- `_process_includes(content, base_dir)` - Process include files

**Features:**
- YAML frontmatter parsing
- Markdown extensions (code highlighting, tables, TOC)
- Wiki-link resolution
- Include file processing

### GardenManager

**Purpose:** Directory structure management

**Key Methods:**
- `list_gardens()` - Get all gardens with config
- `get_hierarchy(garden_slug)` - Build hierarchical tree
- `get_breadcrumbs(path)` - Generate breadcrumb trail
- `get_article_path(garden, slug)` - Resolve article path

**Features:**
- Garden configuration (config.yaml)
- Hierarchical navigation
- URL slug generation
- Path validation

### SearchHandler

**Purpose:** Full-text search with Whoosh

**Key Methods:**
- `rebuild_index()` - Build index from all content
- `search(query)` - Execute search query
- `add_document(doc)` - Add/update document
- `get_stats()` - Index statistics

**Features:**
- Full-text indexing
- Fuzzy search
- Field-specific search
- Relevance ranking

### GitHandler

**Purpose:** Version control integration

**Key Methods:**
- `auto_commit(file_path, message)` - Commit single file
- `push()` - Push to remote
- `pull()` - Pull from remote
- `get_log(limit)` - Get commit history

**Features:**
- Automatic commits on save
- Commit message generation
- GitPython integration
- Optional auto-push

### IndexManager

**Purpose:** Coordinate search and content indexes

**Key Methods:**
- `update_single_file(file_path)` - Update indexes for one file
- `rebuild_all()` - Rebuild both indexes
- `mark_dirty()` - Set dirty flag for deferred updates

**Modes:**
- **Immediate:** Updates happen on save (default)
- **Deferred:** Updates happen via cron job

## Request Lifecycle

### Public Article View

```
1. User requests: /garden/blog/hello-world
                    ↓
2. routes.article(garden_slug='blog', article_path='hello-world')
                    ↓
3. GardenManager.get_article_path('blog', 'hello-world')
   → Returns: content/blog/hello-world.md
                    ↓
4. MarkdownHandler.parse_file('content/blog/hello-world.md')
   → Returns: metadata, content
                    ↓
5. Check status: if metadata['status'] != 'published' → 403
                    ↓
6. MarkdownHandler.convert_markdown(content)
   → Returns: HTML
                    ↓
7. render_template('article.html',
                   title=metadata['title'],
                   content=HTML,
                   ...)
                    ↓
8. Response: HTML page
```

### Editor Save

```
1. User clicks "Save" in editor
   → AJAX POST to /editor/save
   → { garden, path, metadata, content }
                    ↓
2. @login_required → Check authentication
                    ↓
3. DateManager.auto_update_modified(metadata)
   → metadata['updated_date'] = today
                    ↓
4. file_path = GardenManager.get_article_path(garden, path)
                    ↓
5. MarkdownHandler.save_file(file_path, metadata, content)
   → Writes file to disk
                    ↓
6. GitHandler.auto_commit(file_path, "Update: article.md")
   → git add + git commit
                    ↓
7. IndexManager.update_single_file(file_path)
   → Updates search and content indexes
                    ↓
8. Response: JSON { success: true, metadata: {...} }
                    ↓
9. JavaScript updates UI with new metadata
```

## Database Architecture

### Two-Database Design

**trellis_admin.db:**
- User accounts
- Authentication data
- User roles and permissions
- Session data

**trellis_content.db:**
- Article metadata cache
- Tag index
- Wiki-link resolution
- Search result metadata

**Why separate?**
- Different access patterns
- Can rebuild content DB from files
- Admin DB is critical (requires backup)
- Content DB is cache (can regenerate)

### Content Index Schema

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    garden_slug TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content TEXT,
    published_date TEXT,
    created_date TEXT,
    updated_date TEXT,
    tags TEXT,  -- JSON array
    status TEXT DEFAULT 'published',
    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(garden_slug, slug)
);

CREATE INDEX idx_slug ON articles(slug);
CREATE INDEX idx_garden ON articles(garden_slug);
CREATE INDEX idx_status ON articles(status);
CREATE INDEX idx_published ON articles(published_date);
```

## Search Architecture

### Whoosh Index Schema

```python
from whoosh.fields import Schema, ID, TEXT, DATETIME, KEYWORD

schema = Schema(
    path=ID(stored=True, unique=True),
    title=TEXT(stored=True, field_boost=2.0),
    content=TEXT(stored=True),
    tags=KEYWORD(stored=True, commas=True, scorable=True),
    published_date=DATETIME(stored=True),
    garden_slug=ID(stored=True),
)
```

**Index Location:** `DATA_DIR/search_index/`

**Index Operations:**
- **Add:** New article created
- **Update:** Article modified
- **Delete:** Article deleted
- **Rebuild:** Full index reconstruction

## Security Architecture

### Authentication Flow

```
1. User submits login form
                    ↓
2. auth_bp.login()
   → Validate credentials
   → Check password hash
                    ↓
3. Flask-Login: login_user(user)
   → Creates session
   → Sets session cookie
                    ↓
4. Redirect to dashboard
                    ↓
5. Subsequent requests include session cookie
                    ↓
6. @login_required decorator
   → Verifies session
   → Loads user from database
```

### Authorization

**Role-Based Access Control:**

```python
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

**Access Levels:**
- **Public:** View published content
- **Editor:** Edit content, view drafts
- **Admin:** User management, all editor permissions

### Path Validation

Prevent directory traversal attacks:

```python
def validate_path(path):
    """Ensure path doesn't escape content directory"""
    real_path = os.path.realpath(path)
    content_dir = os.path.realpath(CONTENT_DIR)
    if not real_path.startswith(content_dir):
        abort(403)
    return real_path
```

## Performance Considerations

### Caching Strategy

**Content:**
- No application-level cache (files are fast)
- OS filesystem cache handles file reads
- Web server caches static files

**Indexes:**
- In-memory SQLite queries (fast)
- Whoosh index cached by OS

**Templates:**
- Jinja2 template compilation cache
- Production: precompile templates

### Scalability

**Current Architecture:**
- Good for: 1-10 concurrent users
- Good for: 1,000-10,000 articles
- Bottleneck: SQLite write concurrency

**Scaling Options:**
- Add Redis for session storage
- Use PostgreSQL instead of SQLite
- Add application-level caching (Flask-Caching)
- Serve static assets via CDN
- Add load balancer for multiple app servers

## Extension Points

### Custom Blueprints

```python
from flask import Blueprint

custom_bp = Blueprint('custom', __name__)

@custom_bp.route('/custom')
def custom_route():
    return "Custom content"

# Register in create_app()
app.register_blueprint(custom_bp)
```

### Custom Markdown Extensions

```python
from markdown.extensions import Extension

class CustomExtension(Extension):
    def extendMarkdown(self, md):
        # Custom processing
        pass

# Use in MarkdownHandler
md = markdown.Markdown(extensions=[CustomExtension()])
```

### Custom CLI Commands

```python
# trellis/cli.py
import click

@click.command()
def custom_command():
    """Custom CLI command"""
    click.echo("Running custom command")

# Add to pyproject.toml
[project.scripts]
trellis-custom = "trellis.cli:custom_command"
```

## Dependencies

### Core Dependencies

- **Flask** - Web framework
- **Flask-Login** - Authentication
- **Flask-SQLAlchemy** - ORM
- **Markdown** - Markdown processing
- **Pygments** - Syntax highlighting
- **Whoosh** - Full-text search
- **GitPython** - Git integration
- **python-frontmatter** - YAML frontmatter parsing

### Optional Dependencies

- **qdflask** - Reusable Flask utilities
- **qdcomments** - Commenting system

## Next Steps

- **[Development Setup](development.md)** - Set up dev environment
- **[Deployment](deployment.md)** - Deploy to production
- **[API Reference](api.md)** - Code documentation
