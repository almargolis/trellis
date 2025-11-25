# Trellis

A Flask-based digital garden and hierarchical content management system.

## Overview

Trellis is a flexible CMS for building digital gardens with hierarchical content organization. It supports both traditional flat markdown files and nested `.page` directories, allowing you to organize complex projects with multiple pages while keeping related assets together.

## Features

- 📁 **Hierarchical Content Structure** - Organize content in nested `.page` directories with unlimited depth
- 📝 **Markdown-Based** - Write content in markdown with YAML frontmatter
- 🔍 **Full-Text Search** - Powered by Whoosh with error-tolerant query parsing
- 🔗 **Include System** - Reference other files using `{{include: filename}}` syntax
- 🖼️ **Page-Specific Assets** - Store images and files alongside your content
- 🔐 **User Authentication** - Role-based access control (admin/editor)
- ✏️ **Built-in Editor** - Web-based interface for editing content
- 🌿 **Git Integration** - Automatic commits for content changes
- 🎨 **Digital Gardens** - Content organized into themed "gardens"
- 🔄 **Backwards Compatible** - Works with both flat `.md` files and `.page` directories

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions on creating a new site.

**TL;DR:**
```bash
# Install Trellis
git clone https://github.com/almargolis/trellis.git
pip install -e ./trellis

# Set up your site (see QUICKSTART.md for details)
trellis-init-db
trellis-search --rebuild  # Initialize search index
python run.py
```

## Content Structure

### Traditional Flat Files

```
content/
  garden-name/
    article.md
    another-article.md
```

### Hierarchical Pages

```
content/
  projects/
    my-project.page/
      page.md              # Main content
      screenshot.png       # Page asset
      code.py              # Include file
      setup.page/          # Nested sub-page
        page.md
```

**URL mapping:**
- `content/projects/article.md` → `/garden/projects/article`
- `content/projects/project.page/page.md` → `/garden/projects/project`
- `content/projects/project.page/setup.page/page.md` → `/garden/projects/project/setup`

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Developer guide and architecture overview
- **[HIERARCHICAL_CONTENT.md](HIERARCHICAL_CONTENT.md)** - Detailed guide to hierarchical content structure
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment instructions

## Project Name

**Trellis** - A trellis is a garden structure that supports growth, perfectly representing this system's hierarchical framework for organizing and growing your digital content.

## Technology Stack

- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Markdown** - Content format with Python-Markdown extensions
- **Whoosh** - Full-text search engine
- **GitPython** - Git integration
- **Flask-Login** - Authentication

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
