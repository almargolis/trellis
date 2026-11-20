+++
guid = "d9e3f1a2-7c4b-4e8d-b5a6-3f2e1d0c9b8a"
date-created = 2026-11-20
date-modified = 2026-11-20
public = false
publish = false
draft = true
date-published = ""
slug = "frontmatter"
publish_path = "trellis/docs/reference"
source_path = "/Users/almargolis/projects/published/trellis/docs/reference/frontmatter.md"
+++
# Frontmatter Reference

Trellis uses frontmatter metadata at the top of markdown files. Three formats are supported: YAML, TOML, and JSON.

## Formats

### YAML (default for Trellis Garden)

```yaml
---
title: My Article
published_date: 2024-01-15
tags: [python, flask]
---
Article body here.
```

### TOML (default for TrellisSources)

```toml
+++
guid = "b3feaf02-2641-4d70-a293-9ca34fa067d0"
date-created = 2024-01-15
date-modified = 2024-06-01
public = false
publish = true
draft = false
slug = "my-article"
+++
Article body here.
```

### JSON

```json
{
  "title": "My Article",
  "publish": true
}
Article body here.
```

## Standard Fields

These fields are managed by TrellisSources `ensure_required_fields()`:

| Field | Type | Description |
|-------|------|-------------|
| `guid` | string | UUID4 unique identifier. Auto-generated on first processing. |
| `date-created` | date | File creation date from filesystem. Set once. |
| `date-modified` | date | File modification date from filesystem. Updated on each processing. |
| `date-published` | date/string | Publication date. Set to current date when `publish=true`, empty string when `publish=false`. |
| `public` | boolean | Whether content is publicly visible. Default: `false`. |
| `publish` | boolean | Whether file should be published to garden. Default: `false`. |
| `draft` | boolean | Draft status. Default: `true`. |
| `slug` | string | URL slug derived from filename. |
| `publish_path` | string | Target garden path for publishing. |
| `source_path` | string | Absolute path to the original source file. |
| `source_computer` | string | Hostname where the file was first processed. |

## Article Fields

These fields are used by the Trellis Garden web application:

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Display title for the article. |
| `description` | string | Brief description or excerpt. |
| `created_date` | date | Article creation date (manual). |
| `published_date` | date | Article publication date (manual). |
| `updated_date` | date | Last modification date. Auto-set on save by `DateManager`. |
| `tags` | list | List of tags for categorization. |
| `status` | string | Article status ('published', 'draft'). |

## Auto-Migration

### sensitive to public

The `sensitive` field has been replaced by `public` (inverted logic):
- `sensitive: true` becomes `public: false`
- `sensitive: false` becomes `public: true`

Migration happens automatically when `ensure_required_fields()` processes a file. The `sensitive` field is removed after migration.

## Public Visibility Inheritance

Public visibility is determined by a hierarchy of settings:

1. **File-level**: `public` in frontmatter (highest priority)
2. **Directory-level**: `public` in `config.yaml` of containing directory
3. **Garden-level**: `public` in garden's `config.yaml`
4. **Default**: `false` (not public)

Rules:
- A `public: false` at any ancestor level overrides all child settings
- A file's explicit `public` setting takes precedence over inherited values
- `GardenManager.compute_effective_public()` resolves the final visibility
- Both `public_specified` (what the file says) and `public_effective` (computed result) are stored in the content index

## GUID

Every processed file gets a UUID4 `guid` field. This provides:
- Stable identity across renames and moves
- Cross-reference between source files and garden copies
- Lookup via `ContentIndex.find_page_by_guid()`

## Format Detection

Frontmatter format is detected by the opening delimiter:
- `---` on the first line: YAML
- `+++` on the first line: TOML
- `{` on the first line: JSON

The `frontmatter` module in `trellis/utils/frontmatter.py` is the single source of truth for parsing and writing, shared by both Trellis Garden and TrellisSources.
