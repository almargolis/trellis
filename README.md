+++
guid = "2a8ede4b-abb5-4241-92fc-df090e3aa9fb"
date-created = 2026-10-04
date-modified = 2026-10-04
sensitive = true
publish = false
draft = true
date-published = ""
slug = "readme"
publish_path = "trellis"
source_path = "/Users/almargolis/projects/published/trellis/README.md"
+++
# Trellis

A Flask-based digital garden and hierarchical content management system.

## Overview

Trellis is a flexible CMS for building digital gardens with hierarchical content organization. It supports both traditional flat markdown files and nested `.page` directories, allowing you to organize complex projects with multiple pages while keeping related assets together.

## What is a Digital Garden

A digital garden is a publishing system for articles about various topics. It shares many characteristics with blog publishing systems. The main difference is that blog articles are typically published like journal entries that are written and never updated. If the author wishes to expand on or correct a prior article, the mechanism is a new blog article that mentions the prior work. The key concept of the digital garden is that articles are nurtured and developed over time rather than being frozen. Trellis also allows the garden structure to be modified over time in an organic manner.

## Features

- 📁 **Hierarchical Content Structure** - Organize content in nested directories with unlimited depth
- 📝 **Markdown-Based** - Write content in markdown with YAML, TOML, or JSON frontmatter
- 🔍 **Full-Text Search** - Powered by Whoosh with error-tolerant query parsing
- 🔗 **Include System** - Compose content from multiple files using `{{include: filename}}` syntax
    - Included content does not have to be markdown. This allows included code to be kept as source files that can be tested separately to ensure code quality.
- 🖼️ **Page-Specific Assets** - Use page directories (*.page) to isolate images and files for complex pages from other content.
- 🔐 **User Authentication** - Role-based access control (admin/editor)
- ✏️ **Built-in Editor** - Web-based interface for editing content
- 🌿 **Git Integration** - Automatic commits for content changes
- 🎨 **Digital Gardens** - Content organized into themed "gardens"
- 🔄 **Multi Source** - Content can be collected from multiple markdown sources such as Obsidian and development project trees via the TrellisSources companion tool
- 🔗 **Wiki-Links** - Cross-reference pages with `[[Page Title]]` syntax, resolved via content index
- 👁️ **Public/Draft Visibility** - Hierarchical public visibility inheritance with per-directory and per-file control

## GUID and Frontmatter

Markdown files processed by Trellis are assigned a Globally Unique Identifier (GUID) that uniquely identifies the content. This allows Trellis to recognize a document even after file name, title, or URL changes without treating it as new material.

Trellis supports YAML frontmatter for Obsidian compatibility, and both TOML and JSON frontmatter for compatibility with static site generators. The format of existing files is detected by the opening delimiter (`---`, `+++`, or `{}`). The default format for new files is a configuration option. Frontmatter field names have been chosen for compatibility with other systems to support dual use and migration.

Trellis imposes few restrictions on where or how you create content. New files can be created with any text editor or with applications like Obsidian. When Trellis discovers a new file within its garden directory tree or via TrellisSources, it adds required frontmatter fields automatically without imposing requirements on other applications. It reuses existing metadata created by other tools to avoid duplicate work and conflicts.

## TrellisSources

TrellisSources is a **separate companion package** ([trellis-sources](https://github.com/almargolis/trellis-sources)) that publishes markdown files from source directories into Trellis gardens. It supports multi-garden configurations, per-file publish rules, and bidirectional sync.

Key capabilities:
- **Process**: Add or update frontmatter in source files
- **Publish**: Copy files from source directories into the garden content tree
- **Update**: Sync changes made in the garden back to source files
- **Multi-garden**: Manage multiple gardens with per-garden configurations
- **File-level rules**: Fine-grained control over which files are published, with support for non-markdown files, filename overrides, and sed/awk transforms

Install separately: `pip install -e ../trellis-sources`

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
- **[docs/reference/frontmatter.md](docs/reference/frontmatter.md)** - Frontmatter fields, formats, and auto-migration
- **[docs/reference/architecture.md](docs/reference/architecture.md)** - System architecture
- **[docs/reference/api.md](docs/reference/api.md)** - API reference

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
