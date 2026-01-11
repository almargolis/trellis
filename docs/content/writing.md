# Writing Content

Comprehensive guide to writing and formatting content in Trellis.

## Markdown Basics

Trellis uses standard markdown with extensions.

### Headers

```markdown
# H1 Header
## H2 Header
### H3 Header
#### H4 Header
```

### Text Formatting

```markdown
**Bold text**
*Italic text*
***Bold and italic***
~~Strikethrough~~
`inline code`
```

### Lists

**Unordered:**
```markdown
- Item one
- Item two
  - Nested item
  - Another nested item
- Item three
```

**Ordered:**
```markdown
1. First item
2. Second item
3. Third item
```

### Links

```markdown
[Link text](https://example.com)
[Link with title](https://example.com "Hover text")

# Internal links using wiki-style
[[Article Title]]
[[Article Title|Custom Text]]
```

### Images

```markdown
![Alt text](/path/to/image.png)
![Alt text](https://example.com/image.png "Image title")
```

For page-specific images, see [Page Directories](page-directories.md).

### Code Blocks

With syntax highlighting:

````markdown
```python
def hello_world():
    print("Hello, World!")
```

```javascript
function hello() {
    console.log("Hello, World!");
}
```
````

### Quotes

```markdown
> This is a blockquote.
> It can span multiple lines.
>
> And have multiple paragraphs.
```

### Tables

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1    | Data     | More     |
| Row 2    | Data     | More     |
```

### Horizontal Rules

```markdown
---
```

## Frontmatter

Every article needs YAML frontmatter at the top:

```markdown
---
title: Article Title
published_date: 2026-01-09
created_date: 2026-01-08
updated_date: 2026-01-09
tags: [python, tutorial, web]
status: published
description: Brief description for SEO
---

Your content starts here...
```

### Frontmatter Fields

**Required:**
- `title`: Article title (shown in navigation and page header)
- `status`: Either `published` or `draft`

**Optional:**
- `published_date`: Publication date (YYYY-MM-DD format)
- `created_date`: Creation date
- `updated_date`: Last modified date (auto-updated by editor)
- `tags`: List of tags `[tag1, tag2, tag3]`
- `description`: Brief summary (used in meta tags)

### Date Handling

Dates can be:
- `YYYY-MM-DD` format: `2026-01-09`
- `null`: No date set
- Omitted: Field not used

The `updated_date` is automatically set when saving through the web editor.

## Advanced Markdown

### Footnotes

```markdown
Here's a sentence with a footnote.[^1]

[^1]: This is the footnote content.
```

### Attribute Lists

Add attributes to elements:

```markdown
## Header {: #custom-id }

[Link](url){: .external target="_blank" }
```

### Tables of Contents

Add `[TOC]` on its own line to generate a table of contents:

```markdown
---
title: Long Article
---

[TOC]

## Section 1
Content here...

## Section 2
More content...
```

## Include Files

Include external files in your content:

```markdown
{{include: code-example.py}}
```

This is useful for:
- Sharing code examples across multiple articles
- Keeping large code blocks in separate files
- Reusing common content sections

Include files are resolved relative to the article's directory. See [Page Directories](page-directories.md) for details.

## Draft vs Published

Control visibility with the `status` field:

**Published:**
```yaml
---
title: My Article
status: published
published_date: 2026-01-09
---
```

Article appears in garden views and search results.

**Draft:**
```yaml
---
title: Work in Progress
status: draft
published_date: null
---
```

Article is hidden from public views but accessible to editors.

## SEO Best Practices

### Set Descriptions

```yaml
---
title: Python Tutorial
description: Learn Python basics with hands-on examples
---
```

### Use Descriptive Titles

Good: "Getting Started with Python Virtual Environments"
Bad: "Python Tutorial 1"

### Tag Appropriately

```yaml
tags: [python, tutorial, beginner, virtual-environments]
```

Use 3-6 relevant tags per article.

### Link Internally

Use wiki-links to create connections:

```markdown
For more information, see [[Python Basics]] and [[Advanced Topics]].
```

## File Organization

### Flat Structure

Simple blogs can use flat files:

```
content/
  blog/
    article-1.md
    article-2.md
    article-3.md
```

### Hierarchical Structure

Complex projects benefit from nested page directories:

```
content/
  projects/
    my-app.page/
      page.md
      screenshot.png
      getting-started.page/
        page.md
      api.page/
        page.md
```

See [Page Directories](page-directories.md) for details.

## Tips

**Keep filenames simple:**
- Use lowercase
- Use hyphens for spaces
- Avoid special characters
- Be descriptive: `python-virtual-environments.md` not `pvenv.md`

**Write regularly:**
- Draft posts can stay in `status: draft` until ready
- Set future `published_date` for scheduled content (requires manual publishing)

**Use tags consistently:**
- Create a tag taxonomy
- Reuse existing tags
- Avoid tag proliferation

**Link generously:**
- Use wiki-links for internal references
- Create connections between related articles
- Build a knowledge graph

## Next Steps

- **[Content Structure](structure.md)** - Organize multiple gardens
- **[Wiki Links](wiki-links.md)** - Internal linking
- **[Page Directories](page-directories.md)** - Hierarchical content
