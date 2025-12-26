"""
Trellis Index Manager

Manages both search index and content index with support for:
- Immediate incremental updates (default)
- Deferred updates via dirty flag (optional)
- Change detection
"""
import os
from pathlib import Path
from datetime import datetime


class IndexManager:
    """Manages incremental and deferred index updates"""

    def __init__(self, content_dir, data_dir, deferred=None):
        """Initialize index manager

        Args:
            content_dir: Path to content directory
            data_dir: Path to data directory
            deferred: If True, use dirty flag instead of immediate updates.
                     If None, checks TRELLIS_DEFERRED_INDEXING env var.
        """
        self.content_dir = Path(content_dir)
        self.data_dir = Path(data_dir)

        # Determine if using deferred mode
        if deferred is None:
            deferred = os.environ.get('TRELLIS_DEFERRED_INDEXING', '').lower() in ('true', '1', 'yes')
        self.deferred = deferred

        self.dirty_flag_path = self.data_dir / '.index_dirty'

        # Lazy load indexes to avoid circular imports
        self._content_index = None
        self._search_index = None

    def _get_content_index(self):
        """Lazy load content index"""
        if self._content_index is None:
            from trellis.models.content_index import ContentIndex
            self._content_index = ContentIndex(self.data_dir)
        return self._content_index

    def _get_search_index(self):
        """Lazy load search index"""
        if self._search_index is None:
            from trellis.utils.search_index import SearchIndex
            self._search_index = SearchIndex(self.data_dir)
        return self._search_index

    def set_dirty_flag(self):
        """Mark indexes as needing rebuild"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.dirty_flag_path.write_text(datetime.now().isoformat())

    def clear_dirty_flag(self):
        """Clear the dirty flag"""
        if self.dirty_flag_path.exists():
            self.dirty_flag_path.unlink()

    def is_dirty(self):
        """Check if indexes need rebuilding"""
        return self.dirty_flag_path.exists()

    def update_file(self, file_path, garden_slug=None):
        """Update indexes for a single file

        Args:
            file_path: Path to file relative to content_dir (e.g., 'garden/article.md')
            garden_slug: Garden slug if file is in a garden (optional)
        """
        if self.deferred:
            # Just set dirty flag
            self.set_dirty_flag()
            return

        # Immediate incremental update
        try:
            from trellis.utils.markdown_handler import MarkdownHandler

            # Determine full path
            full_path = self.content_dir / file_path

            # Check if it's a .page directory
            if full_path.suffix == '.page' and full_path.is_dir():
                full_path = full_path / 'page.md'

            # Skip if not a markdown file
            if not full_path.suffix == '.md' or not full_path.exists():
                return

            # Parse the file
            handler = MarkdownHandler(self.content_dir, self.data_dir)
            metadata, content, html = handler.parse_file(file_path)

            # Generate URL
            if garden_slug:
                # Remove .page extension and generate slug
                slug = handler.generate_slug(file_path)
                url = f"/garden/{garden_slug}/{slug}"
                source_file = f"{garden_slug}/{file_path}"
            else:
                # Root-level page
                slug = handler.generate_slug(file_path)
                url = f"/page/{slug}"
                source_file = file_path

            # Update content index
            content_index = self._get_content_index()
            content_index.upsert_page(url, source_file, metadata, self.content_dir)

            # Update search index
            search_index = self._get_search_index()
            search_index.add_document(
                url=url,
                source_file=source_file,
                title=metadata.get('title', ''),
                description=metadata.get('description', ''),
                content=html,
                garden=garden_slug or ''
            )

        except Exception as e:
            # Log but don't fail the save operation
            print(f"Warning: Failed to update indexes for {file_path}: {e}")

    def remove_file(self, file_path, garden_slug=None):
        """Remove a file from indexes

        Args:
            file_path: Path to file relative to content_dir
            garden_slug: Garden slug if file is in a garden (optional)
        """
        if self.deferred:
            self.set_dirty_flag()
            return

        try:
            from trellis.utils.markdown_handler import MarkdownHandler

            # Generate URL
            handler = MarkdownHandler(self.content_dir, self.data_dir)
            slug = handler.generate_slug(file_path)

            if garden_slug:
                url = f"/garden/{garden_slug}/{slug}"
            else:
                url = f"/page/{slug}"

            # Remove from both indexes
            content_index = self._get_content_index()
            content_index.delete_page(url)

            search_index = self._get_search_index()
            search_index.remove_document(url)

        except Exception as e:
            print(f"Warning: Failed to remove {file_path} from indexes: {e}")

    def rebuild_if_dirty(self):
        """Rebuild indexes if dirty flag is set

        Returns:
            dict with 'rebuilt' (bool) and 'count' (int) keys
        """
        if not self.is_dirty():
            return {'rebuilt': False, 'count': 0}

        # Rebuild both indexes
        from trellis.models.content_index import ContentIndex
        from trellis.utils.search_index import SearchIndex
        from trellis.utils.markdown_handler import MarkdownHandler
        from trellis.utils.garden_manager import GardenManager

        content_index = ContentIndex(self.data_dir)
        search_index = SearchIndex(self.data_dir)

        # Clear content index
        content_index.clear_index()

        # Rebuild search index (which clears it)
        count = search_index.rebuild_index(self.content_dir)

        # Rebuild content index
        garden_manager = GardenManager(self.content_dir)
        gardens = garden_manager.get_gardens()

        # Index root-level pages
        handler = MarkdownHandler(self.content_dir, self.data_dir)
        for item in handler.list_items():
            if item.get('type') in ['markdown', 'page']:
                url = f"/page/{item['slug']}"
                content_index.upsert_page(
                    url=url,
                    source_file=item['filename'],
                    metadata=item['metadata'],
                    content_dir=self.content_dir
                )

        # Index each garden
        for garden in gardens:
            garden_path = self.content_dir / garden['slug']
            handler = MarkdownHandler(garden_path, self.data_dir)

            for article in handler.list_articles(recursive=True):
                if article.get('type') in ['markdown', 'page']:
                    url = f"/garden/{garden['slug']}/{article['slug']}"
                    content_index.upsert_page(
                        url=url,
                        source_file=f"{garden['slug']}/{article['filename']}",
                        metadata=article['metadata'],
                        content_dir=self.content_dir
                    )

        # Clear dirty flag
        self.clear_dirty_flag()

        return {'rebuilt': True, 'count': count}
