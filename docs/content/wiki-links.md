# Wiki Links

Easy internal linking with wiki-style syntax.

## What Are Wiki Links?

Wiki links provide a simple way to link between articles using double brackets:

```markdown
[[Article Title]]
```

This is easier than:
```markdown
[Article Title](/garden/blog/article-title)
```

## Basic Syntax

### Link by Title

```markdown
See [[Getting Started]] for more information.
```

Trellis finds the article with title "Getting Started" and creates the link automatically.

### Link by Slug

```markdown
Check out [[python-tutorial]] for details.
```

You can use the article's URL slug instead of the full title.

### Custom Display Text

```markdown
Learn more about [[Python Tutorial|Python]].
```

Shows "Python" but links to "Python Tutorial".

## How It Works

When you use a wiki link, Trellis:

1. Searches for articles with matching titles (case-insensitive)
2. Falls back to URL slug matching
3. Resolves the link to the correct URL
4. Converts to standard markdown: `[text](url)`

## Examples

### Simple References

```markdown
This article builds on [[Previous Article]].

For background, see [[Introduction to Python]].
```

### With Custom Text

```markdown
We discussed this [[Advanced Concepts|earlier]].

Learn about [[Python Virtual Environments|venvs]] first.
```

### Multiple Links

```markdown
Related articles: [[Article 1]], [[Article 2]], and [[Article 3]].
```

## Garden-Specific Links

Specify the garden for disambiguation:

```markdown
[[tech/article-name]]
[[blog/another-article]]
```

This is useful when multiple articles have similar titles in different gardens.

## Broken Links

If a wiki link can't be resolved:

```markdown
[[Nonexistent Article]]
```

It appears with red styling and a dashed underline, preserving the original `[[...]]` syntax so you can easily identify and fix broken links.

## Benefits

**Resilient to Refactoring:**
- Rename files without breaking links
- Move articles between gardens
- Links resolve by title, not URL

**Easy to Write:**
- No need to look up URLs
- Faster than typing full markdown links
- More readable in source

**Knowledge Graph:**
- Build interconnected content
- Create topic clusters
- Discover related content

## Use Cases

### Cross-References

```markdown
---
title: Python Functions
---

For more on this topic, see [[Python Classes]] and [[Python Modules]].

## Advanced Usage

Learn about [[Decorators]] and [[Generators]].
```

### Series Articles

```markdown
---
title: Python Tutorial - Part 2
---

Previous: [[Python Tutorial - Part 1]]
Next: [[Python Tutorial - Part 3]]
```

### Topic Hubs

```markdown
---
title: Python Resources
---

## Getting Started
- [[Installing Python]]
- [[First Python Program]]
- [[Python Basics]]

## Intermediate
- [[Python Functions]]
- [[Python Classes]]
- [[Python Modules]]

## Advanced
- [[Python Decorators]]
- [[Python Generators]]
- [[Python Metaclasses]]
```

### Backlinks (Manual)

Create "See Also" sections:

```markdown
## Related Articles

- [[Related Topic 1]]
- [[Related Topic 2]]
- [[Related Topic 3]]
```

## Best Practices

**Use descriptive titles:**
```markdown
# Good
[[Python Virtual Environments]]

# Less good
[[Venv]]
```

**Be consistent:**
- Use the same title/slug format throughout
- Don't alternate between title and slug unnecessarily

**Link generously:**
- Create connections between related content
- Build topic clusters
- Help readers discover related articles

**Check broken links:**
- Broken links appear in red with dashed underline
- Fix them by correcting the title or creating the target article

**Update after refactoring:**
- If you rename an article, update wiki-links that reference it
- Use search to find all references: `grep -r "\[\[Old Title\]\]" content/`

## Technical Details

### Resolution Order

Trellis resolves wiki links in this order:

1. **Exact title match** (case-insensitive)
   - `[[Python Tutorial]]` → finds article with `title: Python Tutorial`

2. **URL slug match**
   - `[[python-tutorial]]` → finds article at `/garden/*/python-tutorial`

3. **Garden-specific slug**
   - `[[blog/python-tutorial]]` → finds article at `/garden/blog/python-tutorial`

4. **Fuzzy title match** (fallback)
   - Tries partial matches if exact match fails

### Performance

Wiki links are resolved at render time using:
- In-memory content index (`trellis_content.db`)
- Fast SQLite lookups
- Cached results

This is much faster than scanning the filesystem for each link.

### Indexing

For wiki links to work, your content must be indexed:

```bash
trellis-search --rebuild
```

This builds the content index used for link resolution.

## Troubleshooting

**Links not resolving?**

Rebuild the content index:
```bash
trellis-search --rebuild
```

**Links to wrong article?**

Use more specific syntax:
```markdown
[[garden-name/article-slug]]
```

**Want to use `[[` literally?**

Escape with backslash:
```markdown
Use \[\[double brackets\]\] for wiki links.
```

## Comparison with Standard Links

**Wiki links:**
```markdown
[[Article Title]]
```

✅ Resilient to refactoring
✅ Easy to write
✅ Title-based (human-friendly)
❌ Requires content index
❌ Broken if article doesn't exist

**Standard markdown links:**
```markdown
[Article Title](/garden/blog/article-title)
```

✅ Always work (no index needed)
✅ Explicit URLs
✅ Standard markdown
❌ Break if URLs change
❌ More verbose
❌ Harder to maintain

**Recommendation:** Use wiki links for internal references, standard markdown links for external URLs.

## Next Steps

- **[Writing Content](writing.md)** - Markdown basics
- **[Content Structure](structure.md)** - Organizing gardens
- **[Page Directories](page-directories.md)** - Hierarchical content
