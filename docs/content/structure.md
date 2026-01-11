# Content Structure

How to organize content across multiple gardens and topics.

## Directory Layout

Trellis uses a hierarchical directory structure:

```
content/
  garden-1/
    config.yaml
    article-1.md
    article-2.md
  garden-2/
    config.yaml
    article-1.md
    nested.page/
      page.md
      assets/
        image.png
```

## Gardens

A **garden** is a top-level directory under `content/`. Each garden represents a distinct collection of content.

### Creating a Garden

```bash
mkdir content/my-garden
```

Create `content/my-garden/config.yaml`:

```yaml
title: My Garden
description: Brief description of this garden
created_date: 2026-01-09
order: 1
```

### Garden Configuration

**Required fields:**
- `title`: Display name
- `description`: Brief description

**Optional fields:**
- `created_date`: When you created this garden
- `order`: Sort order (lower numbers first, default: 999)

### Example Garden Structures

**Personal Blog:**
```
content/
  blog/
    config.yaml
    welcome.md
    python-tips.md
    book-review.md
```

**Multiple Topics:**
```
content/
  tech/
    config.yaml
    python-tutorial.md
    web-development.md
  personal/
    config.yaml
    thoughts.md
    travel.md
  projects/
    config.yaml
    my-app.md
    another-project.md
```

**Documentation Site:**
```
content/
  guides/
    config.yaml
    getting-started.md
    installation.md
  api/
    config.yaml
    endpoints.md
    authentication.md
  examples/
    config.yaml
    basic-usage.md
    advanced.md
```

## Article Files

### Flat Files

Standard markdown files in a garden directory:

```
content/
  blog/
    article-1.md
    article-2.md
```

**URL mapping:**
- `content/blog/article-1.md` → `/garden/blog/article-1`

### Page Directories

Directories ending in `.page` with a `page.md` file inside:

```
content/
  projects/
    my-project.page/
      page.md
      screenshot.png
      setup.page/
        page.md
```

**URL mapping:**
- `content/projects/my-project.page/page.md` → `/garden/projects/my-project`
- `content/projects/my-project.page/setup.page/page.md` → `/garden/projects/my-project/setup`

See [Page Directories](page-directories.md) for details.

## Organizing Content

### By Topic

Group related content:

```
content/
  python/
    config.yaml
    basics.md
    advanced.md
    libraries.md
  javascript/
    config.yaml
    intro.md
    frameworks.md
```

### By Content Type

Separate different types of content:

```
content/
  articles/
    config.yaml
    essay-1.md
    essay-2.md
  tutorials/
    config.yaml
    tutorial-1.md
    tutorial-2.md
  projects/
    config.yaml
    project-1.page/
      page.md
```

### By Time Period

Organize chronologically:

```
content/
  2025/
    config.yaml
    january-post.md
    february-post.md
  2026/
    config.yaml
    january-post.md
```

### Hybrid Approach

Combine strategies:

```
content/
  blog/
    config.yaml
    2025/
      post-1.md
      post-2.md
    2026/
      post-1.md
  projects/
    config.yaml
    web-apps/
      app-1.page/
      app-2.page/
    cli-tools/
      tool-1.page/
```

## Garden Order

Control the order gardens appear:

```yaml
# content/important/config.yaml
title: Important Garden
order: 1

# content/less-important/config.yaml
title: Less Important Garden
order: 2

# content/archived/config.yaml
title: Archived Content
order: 999
```

Lower `order` values appear first. Default is 999.

## URL Structure

### Simple URLs

```
https://yoursite.com/garden/blog/article-name
https://yoursite.com/garden/projects/my-project
```

### Nested URLs

```
https://yoursite.com/garden/projects/my-app/setup
https://yoursite.com/garden/projects/my-app/setup/advanced
```

URLs are derived from:
1. Garden name (directory name)
2. Article path (filename without `.md` or `.page`)

## Navigation

Trellis automatically generates:

**Garden Index** (`/`):
- Lists all gardens
- Sorted by `order` field
- Shows title and description

**Garden View** (`/garden/<garden-name>`):
- Lists all articles in the garden
- Sorted by `published_date` (newest first)
- Shows article titles and excerpts

**Article View** (`/garden/<garden>/<article>`):
- Shows full article content
- Displays metadata (date, tags)
- Includes breadcrumb navigation

## Search

The search function indexes:
- Article titles
- Article content
- Tags
- Garden names

All published content is searchable across all gardens.

## Best Practices

**Start simple:**
- Begin with 1-2 gardens
- Add more as your content grows
- Don't over-organize early

**Be consistent:**
- Use consistent naming conventions
- Follow the same structure within gardens
- Tag articles consistently

**Use descriptive names:**
- Garden directories: `python-tutorials` not `pt`
- Article files: `getting-started.md` not `gs.md`

**Plan for growth:**
- Leave room for expansion
- Use page directories for complex topics
- Consider future organization needs

**Leverage hierarchy:**
- Use page directories for related content
- Group sub-topics under main topics
- Create logical content trees

## Migrating Content

### From Flat to Page Directories

Convert a flat article to a page directory:

```bash
# Before
content/blog/article.md

# After
content/blog/article.page/
  page.md
```

Move `article.md` to `article.page/page.md`. URLs remain the same.

### Reorganizing Gardens

Move articles between gardens:

```bash
mv content/old-garden/article.md content/new-garden/article.md
```

Update any wiki-links that reference the moved article.

### Splitting Large Gardens

Break a large garden into multiple smaller ones:

```bash
# Before
content/blog/
  article-1.md
  article-2.md
  article-3.md

# After
content/tech-blog/
  article-1.md
content/personal-blog/
  article-2.md
  article-3.md
```

Update garden configs and wiki-links.

## Next Steps

- **[Writing Content](writing.md)** - Markdown and formatting
- **[Wiki Links](wiki-links.md)** - Internal linking
- **[Page Directories](page-directories.md)** - Hierarchical structure
