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
                    guid TEXT,
                    source_path TEXT,
                    public_specified INTEGER,
                    public_effective INTEGER DEFAULT 0,
                    draft INTEGER DEFAULT 1,
                    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_updated_date ON pages(updated_date DESC)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source_file ON pages(source_file)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_title ON pages(title COLLATE NOCASE)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_guid ON pages(guid)')

            # Migrations: add columns to existing databases
            for col in ('guid TEXT', 'source_path TEXT',
                        'public_specified INTEGER',
                        'public_effective INTEGER DEFAULT 0',
                        'draft INTEGER DEFAULT 1'):
                try:
                    conn.execute(f'ALTER TABLE pages ADD COLUMN {col}')
                except sqlite3.OperationalError:
                    pass  # column already exists

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

    def upsert_page(self, url, source_file, metadata, content_dir=None, guid=None,
                     public_specified=None, public_effective=False, draft=True):
        """Insert or update a page in the index

        Args:
            url: URL path for the page (e.g., /garden/projects/my-project)
            source_file: Path to source file relative to content dir
            metadata: Dictionary with title, description, dates from frontmatter
            content_dir: Content directory for file mtime lookup (optional)
            guid: Optional unique identifier from frontmatter
            public_specified: Explicit public setting on this item (True/False/None)
            public_effective: Computed public status considering inheritance
            draft: Whether the page is a draft
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

        # Use explicit guid param, fall back to metadata
        effective_guid = guid or metadata.get('guid')

        # Convert booleans to integers for SQLite
        pub_spec = None if public_specified is None else int(public_specified)
        pub_eff = int(public_effective)
        draft_int = int(draft)

        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO pages (url, source_file, title, description,
                                   created_date, published_date, updated_date,
                                   guid, source_path,
                                   public_specified, public_effective, draft,
                                   last_indexed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(url) DO UPDATE SET
                    source_file = excluded.source_file,
                    title = excluded.title,
                    description = excluded.description,
                    created_date = excluded.created_date,
                    published_date = excluded.published_date,
                    updated_date = excluded.updated_date,
                    guid = excluded.guid,
                    source_path = excluded.source_path,
                    public_specified = excluded.public_specified,
                    public_effective = excluded.public_effective,
                    draft = excluded.draft,
                    last_indexed = CURRENT_TIMESTAMP
            ''', (
                url,
                source_file,
                metadata.get('title', ''),
                metadata.get('description', ''),
                self._normalize_date(metadata.get('created_date')),
                self._normalize_date(metadata.get('published_date')),
                effective_updated,
                effective_guid,
                metadata.get('source_path'),
                pub_spec,
                pub_eff,
                draft_int,
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

    def get_recent_pages(self, limit=10, public_only=False):
        """Get recently updated pages

        Args:
            limit: Maximum number of pages to return
            public_only: If True, only return public non-draft pages

        Returns:
            List of dictionaries with page info
        """
        where = 'WHERE updated_date IS NOT NULL'
        if public_only:
            where += ' AND public_effective = 1 AND draft = 0'

        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f'''
                SELECT url, source_file, title, description,
                       created_date, published_date, updated_date
                FROM pages
                {where}
                ORDER BY updated_date DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_pages(self, public_only=False):
        """Get all indexed pages

        Args:
            public_only: If True, only return public non-draft pages
        """
        where = ''
        if public_only:
            where = 'WHERE public_effective = 1 AND draft = 0'

        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f'''
                SELECT url, source_file, title, description,
                       created_date, published_date, updated_date
                FROM pages
                {where}
                ORDER BY title
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def is_page_visible(self, url):
        """Check if a page is public and non-draft.

        Returns True if the page at the given URL is visible to readers.
        Returns False if the page doesn't exist or is not visible.
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT public_effective, draft
                FROM pages WHERE url = ?
            ''', (url,))
            row = cursor.fetchone()
            if not row:
                return False
            return bool(row[0]) and not bool(row[1])

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

    def find_page_by_guid(self, guid):
        """Find a page by its guid

        Args:
            guid: Unique identifier from frontmatter

        Returns:
            Dictionary with page info or None if not found
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, source_file, title, description, guid
                FROM pages
                WHERE guid = ?
                LIMIT 1
            ''', (guid,))
            row = cursor.fetchone()
            return dict(row) if row else None
