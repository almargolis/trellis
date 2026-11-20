"""Tests for trellis.models.content_index.

All tests use tmp_path fixtures so production databases are never touched.
"""

from datetime import date, datetime

import pytest

from trellis.models.content_index import ContentIndex


# ===================================================================
# Database setup
# ===================================================================

class TestDatabaseCreation:

    def test_creates_db_file(self, data_dir):
        ci = ContentIndex(data_dir)
        assert (data_dir / 'trellis_content.db').exists()

    def test_creates_data_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / 'new_data'
        ci = ContentIndex(new_dir)
        assert new_dir.exists()
        assert (new_dir / 'trellis_content.db').exists()

    def test_empty_index_has_zero_pages(self, data_dir):
        ci = ContentIndex(data_dir)
        assert ci.get_page_count() == 0


# ===================================================================
# upsert_page / get_page_count
# ===================================================================

class TestUpsertPage:

    def test_insert_new_page(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/article', 'test/article.md',
                        {'title': 'Article', 'updated_date': '2024-01-01'})
        assert ci.get_page_count() == 1

    def test_update_existing_page(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/article', 'test/article.md',
                        {'title': 'Old Title', 'updated_date': '2024-01-01'})
        ci.upsert_page('/garden/test/article', 'test/article.md',
                        {'title': 'New Title', 'updated_date': '2024-06-01'})
        assert ci.get_page_count() == 1
        page = ci.find_page_by_title('New Title')
        assert page is not None

    def test_stores_guid(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/article', 'test/article.md',
                        {'title': 'Article'}, guid='abc-123')
        page = ci.find_page_by_guid('abc-123')
        assert page is not None
        assert page['title'] == 'Article'

    def test_public_and_draft_flags(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/public', 'test/public.md',
                        {'title': 'Public', 'updated_date': '2024-01-01'},
                        public_effective=True, draft=False)
        assert ci.is_page_visible('/garden/test/public') is True

    def test_draft_not_visible(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/draft', 'test/draft.md',
                        {'title': 'Draft', 'updated_date': '2024-01-01'},
                        public_effective=True, draft=True)
        assert ci.is_page_visible('/garden/test/draft') is False


# ===================================================================
# delete_page / delete_by_source
# ===================================================================

class TestDeletePage:

    def test_delete_by_url(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/article', 'test/article.md',
                        {'title': 'Article', 'updated_date': '2024-01-01'})
        ci.delete_page('/garden/test/article')
        assert ci.get_page_count() == 0

    def test_delete_by_source(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/article', 'test/article.md',
                        {'title': 'Article', 'updated_date': '2024-01-01'})
        ci.delete_by_source('test/article.md')
        assert ci.get_page_count() == 0

    def test_delete_nonexistent_no_error(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.delete_page('/garden/test/nope')  # should not raise


# ===================================================================
# get_recent_pages / get_all_pages
# ===================================================================

class TestQueryPages:

    def _populate(self, ci):
        ci.upsert_page('/garden/test/a', 'test/a.md',
                        {'title': 'Alpha', 'updated_date': '2024-01-01'},
                        public_effective=True, draft=False)
        ci.upsert_page('/garden/test/b', 'test/b.md',
                        {'title': 'Beta', 'updated_date': '2024-06-01'},
                        public_effective=False, draft=False)
        ci.upsert_page('/garden/test/c', 'test/c.md',
                        {'title': 'Gamma', 'updated_date': '2024-03-01'},
                        public_effective=True, draft=True)

    def test_get_all_pages(self, data_dir):
        ci = ContentIndex(data_dir)
        self._populate(ci)
        pages = ci.get_all_pages()
        assert len(pages) == 3

    def test_get_all_pages_public_only(self, data_dir):
        ci = ContentIndex(data_dir)
        self._populate(ci)
        pages = ci.get_all_pages(public_only=True)
        assert len(pages) == 1
        assert pages[0]['title'] == 'Alpha'

    def test_get_recent_pages_ordered(self, data_dir):
        ci = ContentIndex(data_dir)
        self._populate(ci)
        pages = ci.get_recent_pages(limit=10)
        assert pages[0]['title'] == 'Beta'  # most recent updated_date

    def test_get_recent_pages_limit(self, data_dir):
        ci = ContentIndex(data_dir)
        self._populate(ci)
        pages = ci.get_recent_pages(limit=1)
        assert len(pages) == 1

    def test_get_recent_pages_public_only(self, data_dir):
        ci = ContentIndex(data_dir)
        self._populate(ci)
        pages = ci.get_recent_pages(limit=10, public_only=True)
        assert len(pages) == 1
        assert pages[0]['title'] == 'Alpha'


# ===================================================================
# clear_index
# ===================================================================

class TestClearIndex:

    def test_clears_all(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/a', 'a.md',
                        {'title': 'A', 'updated_date': '2024-01-01'})
        ci.upsert_page('/garden/test/b', 'b.md',
                        {'title': 'B', 'updated_date': '2024-01-01'})
        ci.clear_index()
        assert ci.get_page_count() == 0


# ===================================================================
# find_page_by_title
# ===================================================================

class TestFindByTitle:

    def test_exact_match(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/a', 'a.md',
                        {'title': 'My Article', 'updated_date': '2024-01-01'})
        page = ci.find_page_by_title('My Article')
        assert page is not None
        assert page['url'] == '/garden/test/a'

    def test_case_insensitive(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/a', 'a.md',
                        {'title': 'My Article', 'updated_date': '2024-01-01'})
        page = ci.find_page_by_title('my article')
        assert page is not None

    def test_not_found(self, data_dir):
        ci = ContentIndex(data_dir)
        assert ci.find_page_by_title('Nonexistent') is None


# ===================================================================
# find_pages_by_title_fuzzy
# ===================================================================

class TestFindByTitleFuzzy:

    def test_partial_match(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/a', 'a.md',
                        {'title': 'Python Tutorial', 'updated_date': '2024-01-01'})
        ci.upsert_page('/garden/test/b', 'b.md',
                        {'title': 'JavaScript Guide', 'updated_date': '2024-01-01'})
        pages = ci.find_pages_by_title_fuzzy('Python')
        assert len(pages) == 1
        assert pages[0]['title'] == 'Python Tutorial'

    def test_respects_limit(self, data_dir):
        ci = ContentIndex(data_dir)
        for i in range(10):
            ci.upsert_page(f'/garden/test/t{i}', f't{i}.md',
                            {'title': f'Tutorial {i}', 'updated_date': '2024-01-01'})
        pages = ci.find_pages_by_title_fuzzy('Tutorial', limit=3)
        assert len(pages) == 3

    def test_no_match(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/a', 'a.md',
                        {'title': 'Python', 'updated_date': '2024-01-01'})
        pages = ci.find_pages_by_title_fuzzy('JavaScript')
        assert len(pages) == 0


# ===================================================================
# find_page_by_slug
# ===================================================================

class TestFindBySlug:

    def test_exact_url_match(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/article', 'test/article.md',
                        {'title': 'Article', 'updated_date': '2024-01-01'})
        page = ci.find_page_by_slug('/garden/test/article')
        assert page is not None
        assert page['title'] == 'Article'

    def test_slug_without_leading_slash(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/article', 'test/article.md',
                        {'title': 'Article', 'updated_date': '2024-01-01'})
        page = ci.find_page_by_slug('garden/test/article')
        assert page is not None

    def test_partial_slug_match(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/my-article', 'test/my-article.md',
                        {'title': 'My Article', 'updated_date': '2024-01-01'})
        page = ci.find_page_by_slug('my-article')
        assert page is not None

    def test_not_found(self, data_dir):
        ci = ContentIndex(data_dir)
        assert ci.find_page_by_slug('nonexistent') is None


# ===================================================================
# find_page_by_guid
# ===================================================================

class TestFindByGuid:

    def test_found(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/a', 'a.md',
                        {'title': 'A'}, guid='guid-123')
        page = ci.find_page_by_guid('guid-123')
        assert page is not None
        assert page['title'] == 'A'

    def test_not_found(self, data_dir):
        ci = ContentIndex(data_dir)
        assert ci.find_page_by_guid('nonexistent') is None


# ===================================================================
# is_page_visible
# ===================================================================

class TestIsPageVisible:

    def test_public_non_draft(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/a', 'a.md', {'title': 'A'},
                        public_effective=True, draft=False)
        assert ci.is_page_visible('/garden/test/a') is True

    def test_private_non_draft(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/a', 'a.md', {'title': 'A'},
                        public_effective=False, draft=False)
        assert ci.is_page_visible('/garden/test/a') is False

    def test_public_draft(self, data_dir):
        ci = ContentIndex(data_dir)
        ci.upsert_page('/garden/test/a', 'a.md', {'title': 'A'},
                        public_effective=True, draft=True)
        assert ci.is_page_visible('/garden/test/a') is False

    def test_nonexistent_page(self, data_dir):
        ci = ContentIndex(data_dir)
        assert ci.is_page_visible('/garden/test/nope') is False
