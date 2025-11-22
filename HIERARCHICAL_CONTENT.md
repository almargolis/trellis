# Hierarchical Content Structure

This document describes the hierarchical content structure feature in Trellis, a Flask-based digital garden CMS.

## Overview

Content can now be organized in a hierarchical directory structure using `.page` directories. This allows:
- Nested pages with unlimited depth
- Page-specific assets (images, code files) stored alongside content
- Include files that can be referenced in markdown
- Clean URLs without .page extensions

## Structure

### Basic Structure

```
content/
  garden-name/
    article.md                    # Traditional flat file (still supported)
    project.page/                 # New .page directory
      page.md                     # Main content (required)
      screenshot.png              # Page-specific image
      example.py                  # Include file
      details.md                  # Include file
      setup.page/                 # Nested sub-page
        page.md
```

### URL Mapping

- `content/projects/article.md` → `/garden/projects/article`
- `content/projects/project.page/page.md` → `/garden/projects/project`
- `content/projects/project.page/setup.page/page.md` → `/garden/projects/project/setup`

The `.page` extension is stripped from URLs for cleaner paths.

## Features

### 1. Include Files

You can include content from other files using the `{{include: filename}}` syntax:

```markdown
---
title: My Project
---

# My Project

Here's some code:

{{include: example.py}}

And more details:

{{include: details.md}}
```

Includes are processed relative to the directory containing `page.md`. The included content is inserted before markdown rendering.

### 2. Page-Specific Assets

Assets can be stored in `.page` directories and accessed via:

```
/garden/<garden>/<path>/assets/<filename>
```

For example:
- File: `content/projects/my-project.page/screenshot.png`
- URL: `/garden/projects/my-project/assets/screenshot.png`

In markdown:
```markdown
![Screenshot](/garden/projects/my-project/assets/screenshot.png)
```

### 3. Unlimited Nesting

`.page` directories can contain other `.page` directories to any depth:

```
content/
  projects/
    big-project.page/
      page.md                  # /garden/projects/big-project
      overview.page/
        page.md                # /garden/projects/big-project/overview
      setup.page/
        page.md                # /garden/projects/big-project/setup
        advanced.page/
          page.md              # /garden/projects/big-project/setup/advanced
```

### 4. Backwards Compatibility

Traditional flat `.md` files still work alongside `.page` directories. The system automatically detects and handles both formats.

## Implementation Details

### Modified Files

1. **app/utils/markdown_handler.py**
   - `parse_file()`: Detects `.page` directories and looks for `page.md` inside
   - `_process_includes()`: New method that processes `{{include: filename}}` syntax
   - `list_articles()`: Updated to find both `.md` files and `.page` directories
   - `generate_slug()`: Strips `.page` extensions from URLs

2. **app/routes.py**
   - `article()`: Updated to use Flask's `path` converter for nested paths
   - `page_asset()`: New route to serve static files from `.page` directories
   - `edit()` and `save()`: Updated to handle `.page` directories in editor

3. **app/utils/garden_manager.py**
   - `get_hierarchy()`: New method to build tree structure of content
   - `get_breadcrumbs()`: New method to generate breadcrumb navigation

### Security Considerations

- Asset serving includes path validation to prevent directory traversal attacks
- Include file paths are resolved relative to the containing directory only
- File access is restricted to content within the garden directory

## Example

A complete example has been created at `content/projects/test-project.page/`:

```
content/projects/test-project.page/
├── page.md           # Main content with includes
├── example.py        # Python code to include
├── details.md        # Markdown to include
└── setup.page/       # Nested sub-page
    └── page.md
```

You can view it at:
- Main page: http://localhost:5000/garden/projects/test-project
- Setup page: http://localhost:5000/garden/projects/test-project/setup

## Migration Guide

### Converting Existing Content

To convert a flat `.md` file to a `.page` directory:

1. Create a directory with `.page` extension:
   ```bash
   mkdir -p content/projects/my-article.page
   ```

2. Move the content to `page.md`:
   ```bash
   mv content/projects/my-article.md content/projects/my-article.page/page.md
   ```

3. Add any assets or include files to the directory:
   ```bash
   cp ~/screenshots/*.png content/projects/my-article.page/
   ```

4. URLs remain the same - `/garden/projects/my-article` works for both formats

### Creating New Hierarchical Content

1. Create the directory structure:
   ```bash
   mkdir -p content/projects/new-project.page
   ```

2. Create `page.md` with frontmatter:
   ```markdown
   ---
   title: New Project
   published_date: 2024-01-15
   tags: [project, demo]
   ---

   # New Project

   Content here...
   ```

3. Add includes and assets as needed

4. For nested pages, create sub-directories:
   ```bash
   mkdir -p content/projects/new-project.page/setup.page
   ```

## Future Enhancements

Potential improvements:
- Template variables in includes (e.g., `{{include: file.md | param=value}}`)
- Auto-generated table of contents for hierarchical structures
- Navigation sidebar showing page hierarchy
- Asset management UI in the editor
- Bulk conversion tool for migrating flat files to `.page` directories
