# Page Directories

Hierarchical content organization with nested pages and assets.

## What Are Page Directories?

**Page directories** (ending in `.page`) allow you to organize complex content hierarchically with related files kept together.

### Flat File

```
content/
  blog/
    article.md
```

### Page Directory

```
content/
  blog/
    article.page/
      page.md
      image.png
      code-example.py
```

Both create the same URL: `/garden/blog/article`

## Why Use Page Directories?

**Keep assets together:**
```
my-project.page/
  page.md
  screenshot.png
  demo.gif
  architecture.svg
```

**Nest related content:**
```
my-project.page/
  page.md
  getting-started.page/
    page.md
  advanced-usage.page/
    page.md
```

**Include external files:**
```
tutorial.page/
  page.md
  example.py
  config.yaml
```

## Basic Structure

### Single Page

```
content/
  projects/
    my-app.page/
      page.md         # Main content (required)
      screenshot.png  # Page asset
```

The `page.md` file contains your markdown content with frontmatter:

```markdown
---
title: My App
published_date: 2026-01-09
---

This is my app.

![Screenshot](screenshot.png)
```

**URL:** `/garden/projects/my-app`

### Nested Pages

```
content/
  projects/
    my-app.page/
      page.md                    # /garden/projects/my-app
      getting-started.page/
        page.md                  # /garden/projects/my-app/getting-started
      api-reference.page/
        page.md                  # /garden/projects/my-app/api-reference
        authentication.page/
          page.md                # /garden/projects/my-app/api-reference/authentication
```

Unlimited nesting depth!

## Using Assets

### Images

Store images alongside your content:

```
article.page/
  page.md
  diagram.png
  photo.jpg
```

Reference them in markdown:

```markdown
![Diagram](diagram.png)
![Photo](photo.jpg)
```

Trellis serves assets at: `/garden/<garden>/<path>/assets/<filename>`

### Other Files

Store any file type:

```
project.page/
  page.md
  config.json
  example.py
  data.csv
  presentation.pdf
```

Link to them:

```markdown
Download the [config file](config.json) or
view the [example code](example.py).
```

## Include Files

Include external files in your content:

```markdown
{{include: example.py}}
```

This inserts the contents of `example.py` into your markdown before rendering.

### Example Structure

```
tutorial.page/
  page.md
  hello.py
  advanced.py
```

In `page.md`:

````markdown
---
title: Python Tutorial
---

Here's a simple example:

{{include: hello.py}}

And here's an advanced version:

{{include: advanced.py}}
````

### Syntax Highlighting

Wrap includes in code blocks for syntax highlighting:

````markdown
```python
{{include: example.py}}
```
````

### Include Paths

Includes are resolved relative to the directory containing `page.md`:

```
project.page/
  page.md
  code/
    example.py
  docs/
    api.md
```

In `page.md`:
```markdown
{{include: code/example.py}}
{{include: docs/api.md}}
```

## Hierarchical Organization

### Documentation Site

```
content/
  docs/
    introduction.page/
      page.md
    installation.page/
      page.md
      linux.page/
        page.md
      macos.page/
        page.md
      windows.page/
        page.md
    guide.page/
      page.md
      basics.page/
        page.md
      advanced.page/
        page.md
```

**URLs:**
- `/garden/docs/introduction`
- `/garden/docs/installation`
- `/garden/docs/installation/linux`
- `/garden/docs/installation/macos`
- `/garden/docs/installation/windows`
- `/garden/docs/guide`
- `/garden/docs/guide/basics`
- `/garden/docs/guide/advanced`

### Project Portfolio

```
content/
  projects/
    web-app.page/
      page.md
      screenshots/
        home.png
        dashboard.png
      architecture.page/
        page.md
        diagram.svg
      deployment.page/
        page.md
        docker-compose.yml
    cli-tool.page/
      page.md
      demo.gif
```

### Tutorial Series

```
content/
  tutorials/
    python-basics.page/
      page.md
      lesson-1.page/
        page.md
        exercise.py
        solution.py
      lesson-2.page/
        page.md
        exercise.py
        solution.py
      lesson-3.page/
        page.md
```

## Breadcrumb Navigation

Trellis automatically generates breadcrumbs for nested pages:

**URL:** `/garden/docs/guide/advanced`

**Breadcrumbs:**
```
Home > Docs > Guide > Advanced
```

Each breadcrumb is clickable and navigates to the parent page.

## Mixed Structure

You can mix flat files and page directories:

```
content/
  blog/
    simple-post.md              # Flat file
    complex-post.page/          # Page directory
      page.md
      images/
        photo.png
    another-simple-post.md      # Flat file
```

Use flat files for simple articles, page directories for complex ones.

## Converting Between Formats

### Flat to Page Directory

```bash
# Before
content/blog/article.md

# After
mkdir content/blog/article.page
mv content/blog/article.md content/blog/article.page/page.md
```

URLs remain the same!

### Page Directory to Flat

```bash
# Before
content/blog/article.page/page.md

# After
mv content/blog/article.page/page.md content/blog/article.md
rm -r content/blog/article.page
```

**Warning:** This removes assets and includes. Make sure they're not needed.

## Best Practices

**Use for complex content:**
- Multi-file projects
- Content with many images
- Tutorials with code examples
- Documentation with includes

**Keep it simple:**
- Don't nest unnecessarily
- Use flat files for simple articles
- Only create page directories when you need them

**Organize assets:**
```
project.page/
  page.md
  images/
    screenshot1.png
    screenshot2.png
  code/
    example1.py
    example2.py
```

**Name descriptively:**
```
# Good
getting-started.page/
installation-guide.page/

# Less good
gs.page/
install.page/
```

**Plan hierarchy:**
- Sketch your content tree before creating
- Group related content together
- Keep hierarchy shallow (2-3 levels is usually enough)

## Limitations

**Asset paths:**
- Assets are served at `/garden/<garden>/<path>/assets/<filename>`
- Use relative paths in markdown: `![](image.png)`
- Don't use absolute paths: `![](/assets/image.png)` won't work

**Include files:**
- Resolved relative to `page.md` location
- Can only include files within the same `.page` directory tree
- Can't include files from other gardens

**URL structure:**
- `.page` extension is stripped from URLs
- `/article.page/page.md` → `/article`
- Can't have `article.md` and `article.page/` in the same directory

## Technical Details

### File Detection

Trellis detects page directories by:
1. Looking for directories ending in `.page`
2. Checking for `page.md` inside
3. Serving `page.md` as the page content

### Asset Serving

Assets are served via the `page_asset()` route:

```python
@main_bp.route('/garden/<garden_slug>/<path:article_path>/assets/<filename>')
def page_asset(garden_slug, article_path, filename):
    # Serves files from the .page directory
    ...
```

Path validation prevents directory traversal attacks.

### Include Processing

Includes are processed by `MarkdownHandler._process_includes()`:

1. Find `{{include: filename}}` patterns
2. Resolve path relative to `page.md`
3. Read file contents
4. Replace pattern with contents
5. Continue with markdown rendering

## Troubleshooting

**Images not loading?**

Check:
- Image is in the same directory as `page.md`
- Using relative path: `![](image.png)` not `![](/image.png)`
- Image file exists and has correct name

**Include not working?**

Check:
- Include file exists in the `.page` directory
- Path is relative: `{{include: file.py}}` not `{{include: /file.py}}`
- Syntax is exact: `{{include: filename}}` with colon and space

**404 on nested pages?**

Check:
- Each level has `.page` extension: `parent.page/child.page/`
- Each level has `page.md` file
- Rebuild content index: `trellis-search --rebuild`

## Next Steps

- **[Writing Content](writing.md)** - Markdown and frontmatter
- **[Content Structure](structure.md)** - Organizing gardens
- **[Wiki Links](wiki-links.md)** - Internal linking
