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

    def add_document(self, url, source_file, title, description, content, garden=None):
        """Add or update a document in the search index

        Args:
            url: URL path for the page
            source_file: Path to source file
            title: Page title
            description: Page description
            content: Full text content (HTML will be stripped)
            garden: Garden slug (optional)
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

    def search(self, query_string, limit=20):
        """Search the index

        Args:
            query_string: User's search query
            limit: Maximum results to return

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

                results = searcher.search(query, limit=limit)

                # Convert results to list of dicts
                result_list = []
                for hit in results:
                    result_list.append({
                        'url': hit['url'],
                        'title': hit['title'] or 'Untitled',
                        'description': hit['description'] or '',
                        'garden': hit['garden'] if 'garden' in hit else None,
                        'score': hit.score,
                    })

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
                    url = f"/page/{item['slug']}"
                    writer.add_document(
                        url=url,
                        source_file=item['filename'],
                        title=item['metadata'].get('title', ''),
                        description=item['metadata'].get('description', ''),
                        content=self._strip_html(item.get('content', '')),
                        garden='',
                    )
                    count += 1

            # Index each garden
            for garden in gardens:
                garden_path = content_path / garden['slug']
                handler = MarkdownHandler(garden_path, self.data_dir)

                # Recursively get all articles
                for article in handler.list_articles(recursive=True):
                    if article.get('type') in ['markdown', 'page']:
                        url = f"/garden/{garden['slug']}/{article['slug']}"
                        writer.add_document(
                            url=url,
                            source_file=f"{garden['slug']}/{article['filename']}",
                            title=article['metadata'].get('title', ''),
                            description=article['metadata'].get('description', ''),
                            content=self._strip_html(article.get('content', '')),
                            garden=garden['slug'],
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
