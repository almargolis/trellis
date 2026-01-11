# Your First Garden

A step-by-step guide to creating a complete digital garden with multiple posts.

## What is a Garden?

In Trellis, a "garden" is a collection of related content. Think of it like:

- A blog category (e.g., "Tech Blog", "Personal Thoughts")
- A topic area (e.g., "Python Tutorials", "Book Reviews")
- A project (e.g., "My App Documentation")

You can have multiple gardens, each with its own theme and organization.

## Setting Up Your Data Directory

Choose where your content will live:

```bash
# Create your data directory
mkdir ~/my-trellis-site
cd ~/my-trellis-site

# Initialize the database
trellis-init-db
```

This creates:
```
my-trellis-site/
  trellis_admin.db         # User accounts
  trellis_content.db       # Content metadata cache
  content/                 # Your markdown files go here
  search_index/            # Full-text search index
```

## Optional: Set Up Git

Track your content changes with version control:

```bash
git init
git add .
git commit -m "Initial Trellis setup"
```

Trellis will automatically commit changes when you save content through the web editor.

## Create Your First Garden

Let's create a blog garden:

```bash
mkdir content/blog
```

Create `content/blog/config.yaml`:

```yaml
title: My Blog
description: Personal thoughts and technical writing
created_date: 2026-01-09
order: 1
```

**Configuration options:**

- `title`: Display name for your garden
- `description`: Brief description (shown in garden list)
- `created_date`: When you created this garden
- `order`: Sort order (lower numbers appear first)

## Write Multiple Posts

### Post 1: Welcome

Create `content/blog/welcome.md`:

```markdown
---
title: Welcome to My Garden
published_date: 2026-01-09
tags: [meta, welcome]
status: published
---

This is my digital garden where I share thoughts, projects, and learnings.

## What I'll Write About

- Technology and programming
- Personal projects
- Book reviews
- Random musings

Stay tuned!
```

### Post 2: A Technical Article

Create `content/blog/python-tips.md`:

```markdown
---
title: 5 Python Tips for Beginners
published_date: 2026-01-09
tags: [python, programming, tutorial]
status: published
---

Here are five things I wish I knew when starting with Python.

## 1. Use Virtual Environments

Always create a virtual environment for your projects:

```python
python3 -m venv venv
source venv/bin/activate
```

## 2. F-Strings Are Your Friend

Instead of:
```python
name = "Alice"
print("Hello, " + name)
```

Use:
```python
name = "Alice"
print(f"Hello, {name}")
```

## 3. List Comprehensions

Transform lists elegantly:
```python
squares = [x**2 for x in range(10)]
```

## 4. The `with` Statement

Always use `with` for file operations:
```python
with open('file.txt', 'r') as f:
    content = f.read()
```

## 5. Use `enumerate()` in Loops

Instead of:
```python
for i in range(len(items)):
    print(i, items[i])
```

Use:
```python
for i, item in enumerate(items):
    print(i, item)
```

Check out [[Python Resources]] for more learning materials!
```

### Post 3: Draft Post

Create `content/blog/draft-post.md`:

```markdown
---
title: Work in Progress
published_date: null
tags: [draft]
status: draft
---

This is a draft post. It won't appear in the public garden view because the status is "draft".

Use this for work-in-progress content.
```

## Frontmatter Fields

Every post should have YAML frontmatter at the top:

**Required:**
- `title`: Post title
- `status`: `published` or `draft`

**Optional:**
- `published_date`: When you published it (YYYY-MM-DD)
- `created_date`: When you wrote it
- `updated_date`: Auto-updated when you save
- `tags`: List of tags `[tag1, tag2]`
- `description`: Brief summary (for SEO)

## Build Search Index

After creating content, build the search index:

```bash
trellis-search --rebuild
```

This enables full-text search across all your content.

## Run Your Site

Create a `run.py` file in your site directory:

```python
from trellis import create_app
import os

# Tell Trellis where your data is
os.environ['DATA_DIR'] = os.path.dirname(os.path.abspath(__file__))

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

Run it:

```bash
python run.py
```

Visit `http://localhost:5000`

## Using the Web Editor

1. **Login**: Navigate to `/auth/login`, use `admin` / `admin`
2. **Change password**: Go to profile and update your password immediately
3. **Access editor**: Click "Editor" in the navigation
4. **Edit posts**: Browse your gardens and click "Edit" on any post
5. **Create new**: Click "New Article" in the editor dashboard

The web editor provides:
- Syntax highlighting for markdown
- Live preview
- Auto-save to prevent data loss
- Automatic git commits
- Frontmatter editing

## Create Additional Gardens

Want more than one garden? Just repeat the process:

```bash
mkdir content/projects
```

`content/projects/config.yaml`:

```yaml
title: My Projects
description: Software projects and experiments
created_date: 2026-01-09
order: 2
```

Then add articles to `content/projects/`.

## Directory Structure

After following this guide, you should have:

```
my-trellis-site/
  run.py
  .env                       # Optional environment config
  trellis_admin.db
  trellis_content.db
  content/
    blog/
      config.yaml
      welcome.md
      python-tips.md
      draft-post.md
    projects/
      config.yaml
  search_index/
    # Search index files
```

## Next Steps

- **[Writing Content](../content/writing.md)** - Advanced markdown features
- **[Wiki Links](../content/wiki-links.md)** - Link between posts easily
- **[Page Directories](../content/page-directories.md)** - Hierarchical organization
- **[Backup Strategy](../maintenance/backup.md)** - Protect your content
