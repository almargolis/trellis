"""
Trellis Content Index

SQLite database for indexing content pages to enable:
- Fast queries for recently updated pages
- Search functionality (future)
- Content metadata tracking

Stored in trellis_content.db alongside trellis_admin.db
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path


class ContentIndex:
    """Manages the content index database (trellis_content.db)"""

    def __init__(self, data_dir):
        """Initialize content index

        Args:
            data_dir: Directory where trellis_content.db will be stored
        """
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / 'trellis_content.db'
        self._ensure_db()

    def _ensure_db(self):
        """Create database and tables if they don't exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    source_file TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    created_date TEXT,
                    published_date TEXT,
                    updated_date TEXT,
                    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_updated_date ON pages(updated_date DESC)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source_file ON pages(source_file)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_title ON pages(title COLLATE NOCASE)')
            conn.commit()

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(str(self.db_path))

    def _normalize_date(self, date_value):
        """Convert date to string format YYYY-MM-DD

        Handles datetime objects, date objects, strings, and None
        """
        if date_value is None:
            return None
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%Y-%m-%d')
        return str(date_value) if date_value else None

    def _get_effective_updated_date(self, metadata, source_file=None):
        """Get the effective updated date with fallback logic

        Priority:
        1. updated_date from metadata
        2. published_date from metadata
        3. created_date from metadata
        4. File modification time (if source_file provided)
        5. Current date
        """
        updated = self._normalize_date(metadata.get('updated_date'))
        if updated:
            return updated

        published = self._normalize_date(metadata.get('published_date'))
        if published:
            return published

        created = self._normalize_date(metadata.get('created_date'))
        if created:
            return created

        # Try file modification time
        if source_file:
            try:
                mtime = os.path.getmtime(source_file)
                return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            except:
                pass

        # Fallback to today
        return datetime.now().strftime('%Y-%m-%d')

    def upsert_page(self, url, source_file, metadata, content_dir=None):
        """Insert or update a page in the index

        Args:
            url: URL path for the page (e.g., /garden/projects/my-project)
            source_file: Path to source file relative to content dir
            metadata: Dictionary with title, description, dates from frontmatter
            content_dir: Content directory for file mtime lookup (optional)
        """
        # Build full source path for mtime lookup
        full_source_path = None
        if content_dir:
            full_source_path = Path(content_dir) / source_file
            if not full_source_path.exists():
                # Try with page.md for .page directories
                if source_file.endswith('.page'):
                    full_source_path = Path(content_dir) / source_file / 'page.md'

        effective_updated = self._get_effective_updated_date(metadata, full_source_path)

        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO pages (url, source_file, title, description,
                                   created_date, published_date, updated_date, last_indexed)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(url) DO UPDATE SET
                    source_file = excluded.source_file,
                    title = excluded.title,
                    description = excluded.description,
                    created_date = excluded.created_date,
                    published_date = excluded.published_date,
                    updated_date = excluded.updated_date,
                    last_indexed = CURRENT_TIMESTAMP
            ''', (
                url,
                source_file,
                metadata.get('title', ''),
                metadata.get('description', ''),
                self._normalize_date(metadata.get('created_date')),
                self._normalize_date(metadata.get('published_date')),
                effective_updated
            ))
            conn.commit()

    def delete_page(self, url):
        """Remove a page from the index"""
        with self._get_connection() as conn:
            conn.execute('DELETE FROM pages WHERE url = ?', (url,))
            conn.commit()

    def delete_by_source(self, source_file):
        """Remove a page by source file path"""
        with self._get_connection() as conn:
            conn.execute('DELETE FROM pages WHERE source_file = ?', (source_file,))
            conn.commit()

    def get_recent_pages(self, limit=10):
        """Get recently updated pages

        Args:
            limit: Maximum number of pages to return

        Returns:
            List of dictionaries with page info
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, source_file, title, description,
                       created_date, published_date, updated_date
                FROM pages
                WHERE updated_date IS NOT NULL
                ORDER BY updated_date DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_pages(self):
        """Get all indexed pages"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, source_file, title, description,
                       created_date, published_date, updated_date
                FROM pages
                ORDER BY title
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_page_count(self):
        """Get total number of indexed pages"""
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM pages')
            return cursor.fetchone()[0]

    def clear_index(self):
        """Clear all entries from the index"""
        with self._get_connection() as conn:
            conn.execute('DELETE FROM pages')
            conn.commit()

    def find_page_by_title(self, title):
        """Find a page by exact title match (case-insensitive)

        Args:
            title: Page title to search for

        Returns:
            Dictionary with page info or None if not found
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, source_file, title, description
                FROM pages
                WHERE LOWER(title) = LOWER(?)
                LIMIT 1
            ''', (title,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def find_pages_by_title_fuzzy(self, title, limit=5):
        """Find pages with titles similar to the search term

        Args:
            title: Title to search for
            limit: Maximum results

        Returns:
            List of page dictionaries, ordered by relevance
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, source_file, title, description
                FROM pages
                WHERE LOWER(title) LIKE LOWER(?)
                ORDER BY LENGTH(title), title
                LIMIT ?
            ''', (f'%{title}%', limit))
            return [dict(row) for row in cursor.fetchall()]

    def find_page_by_slug(self, slug):
        """Find a page by URL slug pattern

        Tries multiple patterns:
        - /garden/{slug}
        - Exact URL match
        - URL ending with slug

        Args:
            slug: URL slug or path to search for

        Returns:
            Dictionary with page info or None if not found
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row

            # Try exact URL match first
            cursor = conn.execute('''
                SELECT url, source_file, title, description
                FROM pages
                WHERE url = ?
                LIMIT 1
            ''', (slug if slug.startswith('/') else f'/{slug}',))
            row = cursor.fetchone()
            if row:
                return dict(row)

            # Try URL ending with slug
            cursor = conn.execute('''
                SELECT url, source_file, title, description
                FROM pages
                WHERE url LIKE ?
                ORDER BY LENGTH(url)
                LIMIT 1
            ''', (f'%/{slug}',))
            row = cursor.fetchone()
            if row:
                return dict(row)

            # Try as garden/slug pattern
            cursor = conn.execute('''
                SELECT url, source_file, title, description
                FROM pages
                WHERE url LIKE ?
                ORDER BY LENGTH(url)
                LIMIT 1
            ''', (f'%/{slug}',))
            row = cursor.fetchone()
            return dict(row) if row else None
