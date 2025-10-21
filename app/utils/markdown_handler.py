import markdown
import frontmatter
import os
from pathlib import Path
from datetime import datetime

class MarkdownHandler:
    def __init__(self, content_dir):
        self.content_dir = Path(content_dir)
        self.md = markdown.Markdown(extensions=[
            'fenced_code',
            'codehilite',
            'tables',
            'toc',
            'footnotes',
            'attr_list'
        ])

    def parse_file(self, filename):
        """Parse markdown file and return metadata + content"""
        filepath = self.content_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        html_content = self.md.convert(post.content)

        return {
            'metadata': post.metadata,
            'content': html_content,
            'raw_content': post.content,
            'slug': self.generate_slug(filename)
        }

    def save_file(self, filename, metadata, content):
        """Save markdown file with frontmatter"""
        filepath = self.content_dir / filename
        post = frontmatter.Post(content, **metadata)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    def list_articles(self):
        """List all markdown files"""
        articles = []
        for md_file in self.content_dir.rglob('*.md'):
            try:
                article = self.parse_file(md_file.relative_to(self.content_dir))
                article['filename'] = str(md_file.relative_to(self.content_dir))
                articles.append(article)
            except Exception as e:
                print(f"Error reading {md_file}: {e}")

        # Sort by published_date (convert to string for consistent sorting)
        def get_sort_key(article):
            pub_date = article['metadata'].get('published_date', '2000-01-01')
            # Convert datetime.date to string if needed
            if hasattr(pub_date, 'strftime'):
                return pub_date.strftime('%Y-%m-%d')
            return str(pub_date) if pub_date else '2000-01-01'

        articles.sort(key=get_sort_key, reverse=True)
        return articles

    @staticmethod
    def generate_slug(filename):
        """Generate URL slug from filename"""
        return Path(filename).stem.lower().replace(' ', '-')

    @staticmethod
    def extract_excerpt(content, length=200):
        """Extract first N characters as excerpt"""
        text = content.replace('#', '').replace('*', '').strip()
        return text[:length] + '...' if len(text) > length else text
