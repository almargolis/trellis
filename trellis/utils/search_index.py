"""
Trellis Search Index

Full-text search using Whoosh. The search index is stored in DATA_DIR/search_index/
and indexes all markdown content including titles, descriptions, and body text.

All Whoosh operations are wrapped in try/except to gracefully handle
invalid search queries (e.g., unmatched quotes, invalid syntax).
"""
import os
import re
from pathlib import Path
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import MultifieldParser, QueryParser
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh.analysis import StemmingAnalyzer


class SearchIndex:
    """Manages the Whoosh full-text search index"""

    def __init__(self, data_dir):
        """Initialize search index

        Args:
            data_dir: Directory where search_index/ will be stored
        """
        self.data_dir = Path(data_dir)
        self.index_dir = self.data_dir / 'search_index'
        self.schema = Schema(
            url=ID(stored=True, unique=True),
            source_file=ID(stored=True),
            title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            description=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            content=TEXT(analyzer=StemmingAnalyzer()),
            garden=STORED,
            status=STORED,
            public_effective=STORED,
            draft=STORED,
        )
        self._index = None

    def _ensure_index(self):
        """Create or open the search index"""
        if self._index is not None:
            return self._index

        self.index_dir.mkdir(parents=True, exist_ok=True)

        if index.exists_in(str(self.index_dir)):
            self._index = index.open_dir(str(self.index_dir))
        else:
            self._index = index.create_in(str(self.index_dir), self.schema)

        return self._index

    def _strip_html(self, html_content):
        """Remove HTML tags from content"""
        clean = re.sub(r'<[^>]+>', '', html_content)
        return clean

    def add_document(self, url, source_file, title, description, content,
                     garden=None, status=None, public_effective=False, draft=True):
        """Add or update a document in the search index

        Args:
            url: URL path for the page
            source_file: Path to source file
            title: Page title
            description: Page description
            content: Full text content (HTML will be stripped)
            garden: Garden slug (optional)
            status: Article status (e.g. 'published', 'draft')
            public_effective: Whether the page is effectively public
            draft: Whether the page is a draft
        """
        try:
            ix = self._ensure_index()
            writer = ix.writer()

            # Strip HTML from content
            clean_content = self._strip_html(content) if content else ''

            writer.update_document(
                url=url,
                source_file=source_file,
                title=title or '',
                description=description or '',
                content=clean_content,
                garden=garden or '',
                status=status or 'published',
                public_effective=bool(public_effective),
                draft=bool(draft),
            )
            writer.commit()
        except Exception as e:
            print(f"Error adding document to search index: {e}")

    def remove_document(self, url):
        """Remove a document from the search index"""
        try:
            ix = self._ensure_index()
            writer = ix.writer()
            writer.delete_by_term('url', url)
            writer.commit()
        except Exception as e:
            print(f"Error removing document from search index: {e}")

    def search(self, query_string, limit=20, public_only=False):
        """Search the index

        Args:
            query_string: User's search query
            limit: Maximum results to return
            public_only: If True, only return public non-draft results

        Returns:
            dict with 'results' list and 'error' message (if any)
        """
        if not query_string or not query_string.strip():
            return {'results': [], 'error': None}

        try:
            ix = self._ensure_index()

            # Check if index has any documents
            if ix.doc_count() == 0:
                return {'results': [], 'error': None}

            with ix.searcher() as searcher:
                # Search across title, description, and content
                parser = MultifieldParser(
                    ['title', 'description', 'content'],
                    schema=self.schema
                )

                try:
                    query = parser.parse(query_string)
                except Exception as parse_error:
                    # Query parsing failed - likely invalid syntax
                    return {
                        'results': [],
                        'error': f"Invalid search query. Please check your search terms. "
                                 f"Avoid special characters like quotes, parentheses, or brackets."
                    }

                # Fetch extra results when filtering to ensure we return enough
                fetch_limit = limit * 3 if public_only else limit
                results = searcher.search(query, limit=fetch_limit)

                # Convert results to list of dicts
                result_list = []
                for hit in results:
                    # Filter for visibility when public_only
                    if public_only:
                        is_public = hit.get('public_effective', False)
                        is_draft = hit.get('draft', True)
                        status = hit.get('status', 'published')
                        if not is_public or is_draft or status == 'draft':
                            continue

                    result_list.append({
                        'url': hit['url'],
                        'title': hit['title'] or 'Untitled',
                        'description': hit['description'] or '',
                        'garden': hit['garden'] if 'garden' in hit else None,
                        'status': hit['status'] if 'status' in hit else 'published',
                        'score': hit.score,
                    })

                    if len(result_list) >= limit:
                        break

                return {'results': result_list, 'error': None}

        except Exception as e:
            # Catch any other Whoosh errors
            error_msg = str(e)
            if 'parse' in error_msg.lower() or 'syntax' in error_msg.lower():
                return {
                    'results': [],
                    'error': "Invalid search query. Please check your search terms."
                }
            return {
                'results': [],
                'error': f"Search error: {error_msg}"
            }

    def rebuild_index(self, content_dir):
        """Rebuild the entire search index from content directory

        Args:
            content_dir: Path to the content directory

        Returns:
            Number of documents indexed
        """
        from trellis.utils.markdown_handler import MarkdownHandler
        from trellis.utils.garden_manager import GardenManager

        content_path = Path(content_dir)
        count = 0

        try:
            # Clear existing index
            self.index_dir.mkdir(parents=True, exist_ok=True)
            self._index = index.create_in(str(self.index_dir), self.schema)
            writer = self._index.writer()

            garden_manager = GardenManager(content_dir)
            gardens = garden_manager.get_gardens()

            # Index root-level pages
            handler = MarkdownHandler(content_path, self.data_dir)
            for item in handler.list_items():
                if item.get('type') in ['markdown', 'page']:
                    meta = item['metadata']
                    file_public = meta.get('public')
                    pub_effective = bool(file_public) if file_public is not None else False
                    is_draft = meta.get('draft', True) or meta.get('status') == 'draft'
                    url = f"/page/{item['slug']}"
                    writer.add_document(
                        url=url,
                        source_file=item['filename'],
                        title=meta.get('title', ''),
                        description=meta.get('description', ''),
                        content=self._strip_html(item.get('content', '')),
                        garden='',
                        status=meta.get('status', 'published'),
                        public_effective=pub_effective,
                        draft=bool(is_draft),
                    )
                    count += 1

            # Index each garden
            for garden in gardens:
                garden_slug = garden['slug']
                garden_path = content_path / garden_slug
                handler = MarkdownHandler(garden_path, self.data_dir)

                # Recursively get all articles
                for article in handler.list_articles(recursive=True):
                    if article.get('type') in ['markdown', 'page']:
                        meta = article['metadata']
                        file_public = meta.get('public')
                        _, pub_effective = garden_manager.compute_effective_public(
                            garden_slug, article['slug'],
                            file_public=file_public,
                        )
                        is_draft = meta.get('draft', True) or meta.get('status') == 'draft'
                        url = f"/garden/{garden_slug}/{article['slug']}"
                        writer.add_document(
                            url=url,
                            source_file=f"{garden_slug}/{article['filename']}",
                            title=meta.get('title', ''),
                            description=meta.get('description', ''),
                            content=self._strip_html(article.get('content', '')),
                            garden=garden_slug,
                            status=meta.get('status', 'published'),
                            public_effective=pub_effective,
                            draft=bool(is_draft),
                        )
                        count += 1

            writer.commit()
            return count

        except Exception as e:
            print(f"Error rebuilding search index: {e}")
            raise

    def get_document_count(self):
        """Get number of documents in the index"""
        try:
            ix = self._ensure_index()
            return ix.doc_count()
        except Exception:
            return 0
