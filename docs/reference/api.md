# API Reference

Code-level documentation for Trellis CMS modules and classes.

## Core Modules

### trellis

Main application module.

#### create_app(config=None)

Create and configure Flask application instance.

**Parameters:**
- `config` (dict, optional): Configuration overrides

**Returns:**
- `Flask`: Configured Flask application

**Example:**
```python
from trellis import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
```

## Utility Classes

### MarkdownHandler

Handle markdown file I/O and processing.

**Location:** `trellis/utils/markdown_handler.py`

#### \_\_init\_\_(content_dir)

Initialize markdown handler.

**Parameters:**
- `content_dir` (str): Path to content directory

```python
from trellis.utils.markdown_handler import MarkdownHandler

handler = MarkdownHandler('/path/to/content')
```

#### parse_file(file_path)

Read and parse markdown file with frontmatter.

**Parameters:**
- `file_path` (str): Path to markdown file

**Returns:**
- `tuple`: (metadata dict, content string)

**Example:**
```python
metadata, content = handler.parse_file('content/blog/article.md')

print(metadata['title'])
print(content)
```

**Metadata Fields:**
- `title` (str): Article title
- `published_date` (str): Publication date
- `created_date` (str): Creation date
- `updated_date` (str): Last update date
- `tags` (list): List of tags
- `status` (str): 'published' or 'draft'

#### save_file(file_path, metadata, content)

Save markdown file with frontmatter.

**Parameters:**
- `file_path` (str): Path to save file
- `metadata` (dict): Frontmatter metadata
- `content` (str): Markdown content

**Returns:**
- `bool`: True if successful

**Example:**
```python
metadata = {
    'title': 'My Article',
    'published_date': '2026-01-09',
    'tags': ['python', 'flask'],
    'status': 'published'
}

content = "# Hello\n\nThis is content."

handler.save_file('content/blog/article.md', metadata, content)
```

#### convert_markdown(text, garden_slug=None, article_slug=None)

Convert markdown to HTML with extensions.

**Parameters:**
- `text` (str): Markdown text
- `garden_slug` (str, optional): Garden slug for wiki-link resolution
- `article_slug` (str, optional): Article slug for wiki-link resolution

**Returns:**
- `str`: HTML string

**Example:**
```python
html = handler.convert_markdown("# Hello\n\nThis is **bold**.")
```

**Features:**
- Code syntax highlighting
- Tables, footnotes, TOC
- Wiki-link resolution: `[[Page Title]]`
- Include file processing: `{{include: file.py}}`

#### list_articles(garden_path, recursive=True)

List all articles in a garden.

**Parameters:**
- `garden_path` (str): Path to garden directory
- `recursive` (bool): Include nested pages

**Returns:**
- `list`: List of article file paths

**Example:**
```python
articles = handler.list_articles('content/blog')
for article in articles:
    print(article)
```

### GardenManager

Manage garden directories and configuration.

**Location:** `trellis/utils/garden_manager.py`

#### \_\_init\_\_(content_dir)

Initialize garden manager.

**Parameters:**
- `content_dir` (str): Path to content directory

```python
from trellis.utils.garden_manager import GardenManager

manager = GardenManager('/path/to/content')
```

#### list_gardens()

Get all gardens with their configurations.

**Returns:**
- `list`: List of garden dicts with 'slug', 'title', 'description', 'order'

**Example:**
```python
gardens = manager.list_gardens()

for garden in gardens:
    print(f"{garden['title']}: {garden['description']}")
```

#### get_hierarchy(garden_slug)

Build hierarchical tree of articles in a garden.

**Parameters:**
- `garden_slug` (str): Garden identifier

**Returns:**
- `dict`: Nested dictionary representing article hierarchy

**Example:**
```python
tree = manager.get_hierarchy('blog')

# tree structure:
# {
#   'article.md': {...},
#   'project.page': {
#     'page.md': {...},
#     'setup.page': {
#       'page.md': {...}
#     }
#   }
# }
```

#### get_breadcrumbs(path)

Generate breadcrumb trail for a path.

**Parameters:**
- `path` (str): Article path (e.g., 'blog/article' or 'projects/my-app/setup')

**Returns:**
- `list`: List of (title, url) tuples

**Example:**
```python
breadcrumbs = manager.get_breadcrumbs('projects/my-app/setup')

# [
#   ('Home', '/'),
#   ('Projects', '/garden/projects'),
#   ('My App', '/garden/projects/my-app'),
#   ('Setup', '/garden/projects/my-app/setup')
# ]
```

#### get_article_path(garden_slug, article_slug)

Resolve article slug to file path.

**Parameters:**
- `garden_slug` (str): Garden identifier
- `article_slug` (str): Article identifier

**Returns:**
- `str`: Full file path to article

**Example:**
```python
path = manager.get_article_path('blog', 'hello-world')
# Returns: 'content/blog/hello-world.md' or 'content/blog/hello-world.page/page.md'
```

### SearchHandler

Full-text search with Whoosh.

**Location:** `trellis/utils/search_handler.py`

#### \_\_init\_\_(index_dir, content_dir)

Initialize search handler.

**Parameters:**
- `index_dir` (str): Path to search index directory
- `content_dir` (str): Path to content directory

```python
from trellis.utils.search_handler import SearchHandler

handler = SearchHandler('/path/to/search_index', '/path/to/content')
```

#### rebuild_index()

Rebuild entire search index from content.

**Returns:**
- `int`: Number of documents indexed

**Example:**
```python
count = handler.rebuild_index()
print(f"Indexed {count} documents")
```

#### search(query_string, limit=50)

Execute search query.

**Parameters:**
- `query_string` (str): Search query
- `limit` (int): Maximum results to return

**Returns:**
- `list`: List of result dicts with 'title', 'path', 'content', 'score'

**Example:**
```python
results = handler.search("python flask", limit=10)

for result in results:
    print(f"{result['title']} - Score: {result['score']}")
```

**Query Syntax:**
- Simple: `python flask`
- Phrase: `"exact phrase"`
- Boolean: `python AND flask`, `python OR javascript`
- Field: `title:python`, `tags:tutorial`
- Wildcard: `python*`

#### add_document(doc)

Add or update document in index.

**Parameters:**
- `doc` (dict): Document with 'path', 'title', 'content', etc.

**Example:**
```python
doc = {
    'path': 'blog/article',
    'title': 'My Article',
    'content': 'Article content here',
    'tags': ['python', 'flask'],
    'published_date': datetime(2026, 1, 9),
    'garden_slug': 'blog'
}

handler.add_document(doc)
```

#### get_stats()

Get search index statistics.

**Returns:**
- `dict`: Stats with 'doc_count', 'index_size', 'last_updated'

**Example:**
```python
stats = handler.get_stats()
print(f"Total documents: {stats['doc_count']}")
print(f"Index size: {stats['index_size']} bytes")
```

### GitHandler

Git integration for version control.

**Location:** `trellis/utils/git_handler.py`

#### \_\_init\_\_(repo_path)

Initialize git handler.

**Parameters:**
- `repo_path` (str): Path to git repository

```python
from trellis.utils.git_handler import GitHandler

handler = GitHandler('/path/to/repo')
```

#### auto_commit(file_path, message=None)

Commit a single file change.

**Parameters:**
- `file_path` (str): Path to file (relative to repo)
- `message` (str, optional): Commit message (auto-generated if None)

**Returns:**
- `bool`: True if committed, False if nothing to commit

**Example:**
```python
handler.auto_commit('content/blog/article.md', 'Update article')
```

**Auto-generated message format:**
```
Update: content/blog/article.md
```

#### push(remote='origin', branch='main')

Push commits to remote.

**Parameters:**
- `remote` (str): Remote name
- `branch` (str): Branch name

**Returns:**
- `bool`: True if successful

**Example:**
```python
handler.push('origin', 'main')
```

#### pull(remote='origin', branch='main')

Pull changes from remote.

**Parameters:**
- `remote` (str): Remote name
- `branch` (str): Branch name

**Returns:**
- `bool`: True if successful

```python
handler.pull('origin', 'main')
```

#### get_log(limit=10)

Get commit history.

**Parameters:**
- `limit` (int): Number of commits

**Returns:**
- `list`: List of commit dicts with 'sha', 'message', 'author', 'date'

**Example:**
```python
commits = handler.get_log(5)

for commit in commits:
    print(f"{commit['sha'][:7]} - {commit['message']}")
```

### DateManager

Manage article dates and timestamps.

**Location:** `trellis/utils/date_manager.py`

#### auto_update_modified(metadata)

Automatically set updated_date to today.

**Parameters:**
- `metadata` (dict): Article metadata (modified in place)

**Returns:**
- `dict`: Updated metadata

**Example:**
```python
from trellis.utils.date_manager import DateManager

metadata = {
    'title': 'My Article',
    'published_date': '2026-01-09'
}

DateManager.auto_update_modified(metadata)

print(metadata['updated_date'])  # Today's date
```

#### format_date(date_str, format='%Y-%m-%d')

Format date string.

**Parameters:**
- `date_str` (str): Date string
- `format` (str): Output format

**Returns:**
- `str`: Formatted date

**Example:**
```python
formatted = DateManager.format_date('2026-01-09', '%B %d, %Y')
print(formatted)  # "January 09, 2026"
```

### IndexManager

Coordinate search and content indexes.

**Location:** `trellis/utils/index_manager.py`

#### \_\_init\_\_(data_dir, content_dir)

Initialize index manager.

**Parameters:**
- `data_dir` (str): Path to data directory
- `content_dir` (str): Path to content directory

```python
from trellis.utils.index_manager import IndexManager

manager = IndexManager('/path/to/data', '/path/to/content')
```

#### update_single_file(file_path)

Update indexes for a single file.

**Parameters:**
- `file_path` (str): Path to changed file

**Example:**
```python
manager.update_single_file('content/blog/article.md')
```

This updates both search index and content index.

#### rebuild_all()

Rebuild both indexes from scratch.

**Example:**
```python
manager.rebuild_all()
```

#### mark_dirty()

Set dirty flag for deferred updates.

**Example:**
```python
# In deferred mode
manager.mark_dirty()

# Cron job later checks flag and rebuilds
```

## CLI Commands

### trellis-init-db

Initialize database with default admin user.

```bash
trellis-init-db
```

Creates `trellis_admin.db` with:
- Admin user: `admin` / `admin`

### trellis-search

Search index management.

```bash
# Rebuild search index
trellis-search --rebuild

# Show statistics
trellis-search --stats
```

### trellis-index

Content index management.

```bash
# Rebuild content index
trellis-index --clear

# Show statistics
trellis-index --stats
```

### trellis-index-update

Update all indexes (checks dirty flag in deferred mode).

```bash
# Check and update if needed
trellis-index-update

# Force update
trellis-index-update --force
```

## Template Context

Templates have access to these variables:

### Base Template Variables

- `site_name` (str): Site name from config
- `site_author` (str): Site author from config
- `current_user`: Flask-Login user object
- `gardens` (list): List of all gardens

### Article Template Variables

- `garden` (dict): Current garden info
- `article` (dict): Article metadata
- `content` (str): Rendered HTML content
- `breadcrumbs` (list): Breadcrumb trail
- `related_articles` (list): Related articles (if enabled)

### Example Template

```jinja2
{% extends "base.html" %}

{% block content %}
<article>
    <h1>{{ article.title }}</h1>

    {% if article.published_date %}
    <time>{{ article.published_date }}</time>
    {% endif %}

    {% if article.tags %}
    <div class="tags">
        {% for tag in article.tags %}
        <span class="tag">{{ tag }}</span>
        {% endfor %}
    </div>
    {% endif %}

    <div class="content">
        {{ content | safe }}
    </div>
</article>
{% endblock %}
```

## Configuration

### Environment Variables

Configuration via `.env` file:

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
SITE_NAME = os.getenv('SITE_NAME', 'Trellis')
DATA_DIR = os.getenv('DATA_DIR', '.')
CONTENT_DIR = os.getenv('CONTENT_DIR', 'content')
```

### Config Class

**Location:** `trellis/config.py`

```python
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    SITE_NAME = os.getenv('SITE_NAME', 'Trellis')
    SITE_AUTHOR = os.getenv('SITE_AUTHOR', '')

    # Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATA_DIR}/trellis_admin.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paths
    DATA_DIR = os.getenv('DATA_DIR', '.')
    CONTENT_DIR = os.getenv('CONTENT_DIR', 'content')

    # Git
    GITLAB_REPO_PATH = os.getenv('GITLAB_REPO_PATH', '.')

    # Indexing
    DEFERRED_INDEXING = os.getenv('TRELLIS_DEFERRED_INDEXING', 'false').lower() == 'true'
```

## Extension Integration

### Adding Custom Blueprints

```python
from flask import Blueprint

custom_bp = Blueprint('custom', __name__, template_folder='templates')

@custom_bp.route('/custom')
def custom_page():
    return render_template('custom.html')

# In create_app()
app.register_blueprint(custom_bp, url_prefix='/custom')
```

### Adding Custom Models

```python
from trellis.models import db

class CustomModel(db.Model):
    __tablename__ = 'custom'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def __repr__(self):
        return f'<CustomModel {self.name}>'
```

### Custom Markdown Extensions

```python
from markdown.extensions import Extension

class CustomExtension(Extension):
    def extendMarkdown(self, md):
        # Add custom processors
        md.preprocessors.register(CustomPreprocessor(md), 'custom', 100)

# Use in MarkdownHandler
handler.md = markdown.Markdown(extensions=[CustomExtension()])
```

## Error Handling

### Common Exceptions

**FileNotFoundError:**
```python
try:
    metadata, content = handler.parse_file('nonexistent.md')
except FileNotFoundError:
    # Handle missing file
    pass
```

**ValidationError:**
```python
try:
    handler.save_file(path, metadata, content)
except ValidationError as e:
    # Handle invalid data
    print(f"Validation error: {e}")
```

### Custom Error Pages

```python
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
```

## Testing

### Unit Tests

```python
import pytest
from trellis.utils.markdown_handler import MarkdownHandler

def test_parse_frontmatter():
    content = """---
title: Test
---
Body"""

    handler = MarkdownHandler('/tmp')
    metadata, body = handler.parse_file_content(content)

    assert metadata['title'] == "Test"
    assert body.strip() == "Body"
```

### Integration Tests

```python
def test_article_view(client):
    response = client.get('/garden/blog/test-article')
    assert response.status_code == 200
    assert b'Test Article' in response.data
```

## Next Steps

- **[Architecture](architecture.md)** - System design
- **[Development](development.md)** - Development setup
- **[Deployment](deployment.md)** - Production deployment
