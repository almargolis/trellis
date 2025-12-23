import markdown
import frontmatter
import os
from pathlib import Path
from datetime import datetime
import re

class MarkdownHandler:
    def __init__(self, content_dir, data_dir=None):
        self.content_dir = Path(content_dir)
        self.data_dir = Path(data_dir) if data_dir else None
        self.md = markdown.Markdown(extensions=[
            'fenced_code',
            'codehilite',
            'tables',
            'toc',
            'footnotes',
            'attr_list'
        ])
        self._content_index = None
        self._broken_links = []

    def parse_file(self, filename):
        """Parse markdown file and return metadata + content

        Supports both:
        - Direct .md files: article.md
        - .page directories: article.page/page.md
        """
        filepath = self.content_dir / filename

        # If filename points to a .page directory, look for page.md inside
        if filepath.is_dir() and filepath.suffix == '.page':
            filepath = filepath / 'page.md'
            if not filepath.exists():
                raise FileNotFoundError(f"page.md not found in {filename}")

        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Process includes and wiki-links before converting to HTML
        processed_content = self._process_includes(post.content, filepath.parent)
        processed_content = self._process_wikilinks(processed_content)

        html_content = self.md.convert(processed_content)

        result = {
            'metadata': post.metadata,
            'content': html_content,
            'raw_content': post.content,
            'slug': self.generate_slug(filename),
            'is_page_dir': filepath.name == 'page.md'
        }

        # Include broken links if any were found
        if self._broken_links:
            result['broken_links'] = self._broken_links.copy()
            self._broken_links = []

        return result

    def _get_content_index(self):
        """Lazy-load content index for wiki-link resolution"""
        if self._content_index is None and self.data_dir:
            from trellis.models.content_index import ContentIndex
            self._content_index = ContentIndex(self.data_dir)
        return self._content_index

    def _process_wikilinks(self, content):
        """Process [[Page Title]] wiki-link syntax

        Supports:
        - [[Page Title]] - Link by title
        - [[page-slug]] - Link by slug/path
        - [[Page Title|Custom Text]] - Custom display text
        - [[garden/page-slug]] - Garden-specific slug

        Returns markdown links: [text](url)
        Tracks broken links in self._broken_links
        """
        wikilink_pattern = r'\[\[([^\]]+)\]\]'

        def replace_wikilink(match):
            link_text = match.group(1).strip()

            # Parse custom display text if present
            if '|' in link_text:
                target, display_text = link_text.split('|', 1)
                target = target.strip()
                display_text = display_text.strip()
            else:
                target = link_text
                display_text = None

            # Try to resolve the link
            page = self._resolve_wikilink(target)

            if page:
                url = page['url']
                title = display_text or page['title'] or target
                return f"[{title}]({url})"
            else:
                # Broken link - preserve original syntax and track it
                self._broken_links.append(target)
                # Return a span with broken-link class for styling
                return f'<span class="broken-wikilink" title="Page not found: {target}">[[{link_text}]]</span>'

        return re.sub(wikilink_pattern, replace_wikilink, content)

    def _resolve_wikilink(self, target):
        """Resolve a wiki-link target to a page

        Args:
            target: Page title or slug to find

        Returns:
            Page dict with url and title, or None if not found
        """
        content_index = self._get_content_index()
        if not content_index:
            return None

        # Try exact title match first (case-insensitive)
        page = content_index.find_page_by_title(target)
        if page:
            return page

        # Try as slug/path
        page = content_index.find_page_by_slug(target)
        if page:
            return page

        # Try fuzzy title match as fallback
        fuzzy_matches = content_index.find_pages_by_title_fuzzy(target, limit=1)
        if fuzzy_matches:
            return fuzzy_matches[0]

        return None

    def _process_includes(self, content, base_path):
        """Process {{include: filename}} syntax in markdown content"""
        include_pattern = r'\{\{include:\s*([^\}]+)\}\}'

        def replace_include(match):
            include_file = match.group(1).strip()
            include_path = base_path / include_file

            try:
                with open(include_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return f"<!-- Include not found: {include_file} -->"
            except Exception as e:
                return f"<!-- Error including {include_file}: {e} -->"

        return re.sub(include_pattern, replace_include, content)

    def save_file(self, filename, metadata, content):
        """Save markdown file with frontmatter"""
        filepath = self.content_dir / filename
        post = frontmatter.Post(content, **metadata)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    def list_items(self):
        """List all items in the current directory (non-recursive)

        Returns three types of items:
        - markdown files (.md)
        - page directories (.page)
        - content directories (regular directories)

        Returns:
            List of item dictionaries with type, metadata, and display info
        """
        items = []

        if not self.content_dir.exists():
            return items

        for item in sorted(self.content_dir.iterdir()):
            # Skip hidden files and config.yaml
            if item.name.startswith('.') or item.name in ['config.yaml', 'config.yml']:
                continue

            try:
                if item.is_file() and item.suffix == '.md':
                    # Markdown file
                    article = self.parse_file(item.name)
                    article['filename'] = item.name
                    article['type'] = 'markdown'
                    article['name'] = item.stem
                    items.append(article)

                elif item.is_dir() and item.suffix == '.page':
                    # Page directory
                    page_md = item / 'page.md'
                    if page_md.exists():
                        article = self.parse_file(item.name)
                        article['filename'] = item.name
                        article['type'] = 'page'
                        article['name'] = item.stem.replace('.page', '')
                        items.append(article)

                elif item.is_dir():
                    # Content directory
                    from trellis.utils.garden_manager import GardenManager
                    # Get or create config for this directory
                    garden_mgr = GardenManager(self.content_dir)
                    config = garden_mgr.get_or_create_config(item.name)

                    items.append({
                        'filename': item.name,
                        'type': 'directory',
                        'name': item.name,
                        'slug': self.generate_slug(item.name),
                        'metadata': {
                            'title': config.get('title', item.name.replace('-', ' ').title()),
                            'description': config.get('description', ''),
                            'created_date': config.get('created_date'),
                            'published_date': config.get('created_date'),
                            'updated_date': config.get('updated_date'),
                        },
                        'config': config
                    })
            except Exception as e:
                print(f"Error reading {item}: {e}")

        # Sort: directories first, then by published/created date
        def get_sort_key(item):
            # Directories first
            type_priority = {'directory': 0, 'page': 1, 'markdown': 1}
            priority = type_priority.get(item.get('type', 'markdown'), 2)

            # Then by date
            pub_date = item['metadata'].get('published_date') or item['metadata'].get('created_date', '2000-01-01')
            if hasattr(pub_date, 'strftime'):
                date_str = pub_date.strftime('%Y-%m-%d')
            else:
                date_str = str(pub_date) if pub_date else '2000-01-01'

            return (priority, date_str)

        items.sort(key=get_sort_key, reverse=False)
        return items

    def list_articles(self, recursive=True):
        """List all articles recursively (for backwards compatibility)

        This is kept for editor and other views that need all articles.
        For directory views, use list_items() instead.
        """
        articles = []
        seen_paths = set()

        if recursive:
            # Find all .md files
            for md_file in self.content_dir.rglob('*.md'):
                # Skip page.md files inside .page directories (they'll be found separately)
                if md_file.name == 'page.md' and md_file.parent.suffix == '.page':
                    continue

                rel_path = md_file.relative_to(self.content_dir)
                if str(rel_path) in seen_paths:
                    continue
                seen_paths.add(str(rel_path))

                try:
                    article = self.parse_file(rel_path)
                    article['filename'] = str(rel_path)
                    article['type'] = 'markdown'
                    articles.append(article)
                except Exception as e:
                    print(f"Error reading {md_file}: {e}")

            # Find all .page directories
            for item in self.content_dir.rglob('*'):
                if item.is_dir() and item.suffix == '.page':
                    page_md = item / 'page.md'
                    if not page_md.exists():
                        continue

                    rel_path = item.relative_to(self.content_dir)
                    if str(rel_path) in seen_paths:
                        continue
                    seen_paths.add(str(rel_path))

                    try:
                        article = self.parse_file(rel_path)
                        article['filename'] = str(rel_path)
                        article['type'] = 'page'
                        articles.append(article)
                    except Exception as e:
                        print(f"Error reading {item}: {e}")
        else:
            # Use list_items for non-recursive
            return self.list_items()

        # Sort by published_date
        def get_sort_key(article):
            pub_date = article['metadata'].get('published_date', '2000-01-01')
            if hasattr(pub_date, 'strftime'):
                return pub_date.strftime('%Y-%m-%d')
            return str(pub_date) if pub_date else '2000-01-01'

        articles.sort(key=get_sort_key, reverse=True)
        return articles

    @staticmethod
    def generate_slug(filename):
        """Generate URL slug from filename or directory path

        Examples:
            'article.md' -> 'article'
            'my-project.page' -> 'my-project'
            'section/project.page' -> 'section/project'
        """
        path = Path(filename)

        # Remove .page extension from any part of the path
        parts = []
        for part in path.parts:
            if part.endswith('.page'):
                parts.append(part[:-5])  # Remove .page extension
            elif part.endswith('.md'):
                parts.append(Path(part).stem)  # Remove .md extension
            else:
                parts.append(part)

        slug = '/'.join(parts)
        return slug.lower().replace(' ', '-')

    @staticmethod
    def extract_excerpt(content, length=200):
        """Extract first N characters as excerpt"""
        text = content.replace('#', '').replace('*', '').strip()
        return text[:length] + '...' if len(text) > length else text
