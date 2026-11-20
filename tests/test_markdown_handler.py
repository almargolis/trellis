"""Tests for trellis.utils.markdown_handler.

All tests use tmp_path fixtures so production content is never touched.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from trellis.utils.markdown_handler import MarkdownHandler


# ===================================================================
# generate_slug (static, no I/O)
# ===================================================================

class TestGenerateSlug:

    def test_simple_md(self):
        assert MarkdownHandler.generate_slug('article.md') == 'article'

    def test_page_dir(self):
        assert MarkdownHandler.generate_slug('my-project.page') == 'my-project'

    def test_nested_page(self):
        assert MarkdownHandler.generate_slug('section/project.page') == 'section/project'

    def test_nested_md(self):
        assert MarkdownHandler.generate_slug('sub/article.md') == 'sub/article'

    def test_uppercase_lowered(self):
        assert MarkdownHandler.generate_slug('My Article.md') == 'my-article'

    def test_spaces_to_hyphens(self):
        assert MarkdownHandler.generate_slug('my article.md') == 'my-article'

    def test_nested_page_with_md(self):
        slug = MarkdownHandler.generate_slug('project.page/sub.page')
        assert slug == 'project/sub'


# ===================================================================
# extract_excerpt (static, no I/O)
# ===================================================================

class TestExtractExcerpt:

    def test_short_text_no_ellipsis(self):
        assert MarkdownHandler.extract_excerpt('Hello world') == 'Hello world'

    def test_long_text_truncated(self):
        text = 'x' * 300
        result = MarkdownHandler.extract_excerpt(text, length=200)
        assert len(result) == 203  # 200 + '...'
        assert result.endswith('...')

    def test_strips_markdown_formatting(self):
        text = '# Hello **world**'
        result = MarkdownHandler.extract_excerpt(text)
        assert '#' not in result
        assert '*' not in result

    def test_custom_length(self):
        text = 'a' * 50
        result = MarkdownHandler.extract_excerpt(text, length=10)
        assert len(result) == 13  # 10 + '...'

    def test_exact_length_no_ellipsis(self):
        text = 'a' * 200
        result = MarkdownHandler.extract_excerpt(text, length=200)
        assert result == text  # exact length, no ellipsis


# ===================================================================
# parse_file
# ===================================================================

class TestParseFile:

    def test_yaml_frontmatter(self, tmp_path, make_md):
        f = make_md('article.md', body='Hello world', fmt='yaml',
                    title='Test', parent=tmp_path)
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('article.md')
        assert result['metadata']['title'] == 'Test'
        assert 'Hello world' in result['content']
        assert result['raw_content'] == 'Hello world'
        assert result['frontmatter_format'] == 'yaml'

    def test_toml_frontmatter(self, tmp_path, make_md):
        f = make_md('article.md', body='Hello', fmt='toml',
                    title='Test TOML', parent=tmp_path)
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('article.md')
        assert result['metadata']['title'] == 'Test TOML'

    def test_slug_generated(self, tmp_path, make_md):
        make_md('my-article.md', body='content', fmt='yaml',
                title='Article', parent=tmp_path)
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('my-article.md')
        assert result['slug'] == 'my-article'

    def test_page_dir(self, tmp_path, make_md):
        page_dir = tmp_path / 'project.page'
        page_dir.mkdir()
        make_md('page.md', body='Page content', fmt='yaml',
                title='Project', parent=page_dir)
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('project.page')
        assert result['metadata']['title'] == 'Project'
        assert result['is_page_dir'] is True

    def test_page_dir_missing_page_md(self, tmp_path):
        page_dir = tmp_path / 'empty.page'
        page_dir.mkdir()
        mh = MarkdownHandler(tmp_path)
        with pytest.raises(FileNotFoundError):
            mh.parse_file('empty.page')

    def test_no_frontmatter(self, tmp_path):
        (tmp_path / 'bare.md').write_text('Just text', encoding='utf-8')
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('bare.md')
        assert result['metadata'] == {}
        assert 'Just text' in result['content']

    def test_markdown_rendering(self, tmp_path, make_md):
        make_md('article.md', body='**bold** and *italic*', fmt='yaml',
                title='Formatting', parent=tmp_path)
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('article.md')
        assert '<strong>bold</strong>' in result['content']
        assert '<em>italic</em>' in result['content']


# ===================================================================
# _process_includes
# ===================================================================

class TestProcessIncludes:

    def test_include_resolves(self, tmp_path, make_md):
        (tmp_path / 'snippet.txt').write_text('included text', encoding='utf-8')
        make_md('article.md', body='Before {{include: snippet.txt}} After',
                fmt='yaml', title='Inc', parent=tmp_path)
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('article.md')
        assert 'included text' in result['content']

    def test_include_missing_file(self, tmp_path, make_md):
        make_md('article.md', body='{{include: nonexistent.txt}}',
                fmt='yaml', title='Missing', parent=tmp_path)
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('article.md')
        assert 'Include not found' in result['content']

    def test_include_in_page_dir(self, tmp_path, make_md):
        page_dir = tmp_path / 'project.page'
        page_dir.mkdir()
        (page_dir / 'code.py').write_text('print("hello")', encoding='utf-8')
        make_md('page.md', body='Code: {{include: code.py}}',
                fmt='yaml', title='Inc', parent=page_dir)
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('project.page')
        assert 'print("hello")' in result['content']


# ===================================================================
# _process_wikilinks
# ===================================================================

class TestProcessWikilinks:

    def test_no_content_index_returns_broken(self, tmp_path, make_md):
        make_md('article.md', body='See [[Missing Page]]',
                fmt='yaml', title='Links', parent=tmp_path)
        mh = MarkdownHandler(tmp_path)  # no data_dir
        result = mh.parse_file('article.md')
        assert 'broken-wikilink' in result['content']
        assert 'broken_links' in result
        assert 'Missing Page' in result['broken_links']

    def test_resolved_link(self, tmp_path, make_md):
        make_md('article.md', body='See [[Target Page]]',
                fmt='yaml', title='Links', parent=tmp_path)

        mock_index = MagicMock()
        mock_index.find_page_by_title.return_value = {
            'url': '/garden/test/target',
            'title': 'Target Page',
        }

        mh = MarkdownHandler(tmp_path, data_dir=tmp_path)
        mh._content_index = mock_index

        result = mh.parse_file('article.md')
        assert '/garden/test/target' in result['content']
        assert 'Target Page' in result['content']
        assert 'broken_links' not in result

    def test_custom_display_text(self, tmp_path, make_md):
        make_md('article.md', body='See [[Target|Custom Text]]',
                fmt='yaml', title='Links', parent=tmp_path)

        mock_index = MagicMock()
        mock_index.find_page_by_title.return_value = {
            'url': '/garden/test/target',
            'title': 'Target',
        }

        mh = MarkdownHandler(tmp_path, data_dir=tmp_path)
        mh._content_index = mock_index

        result = mh.parse_file('article.md')
        assert 'Custom Text' in result['content']

    def test_fallback_slug_resolution(self, tmp_path, make_md):
        make_md('article.md', body='See [[some-slug]]',
                fmt='yaml', title='Links', parent=tmp_path)

        mock_index = MagicMock()
        mock_index.find_page_by_title.return_value = None
        mock_index.find_page_by_slug.return_value = {
            'url': '/garden/test/some-slug',
            'title': 'Some Slug',
        }

        mh = MarkdownHandler(tmp_path, data_dir=tmp_path)
        mh._content_index = mock_index

        result = mh.parse_file('article.md')
        assert '/garden/test/some-slug' in result['content']

    def test_fallback_fuzzy_resolution(self, tmp_path, make_md):
        make_md('article.md', body='See [[Approximate]]',
                fmt='yaml', title='Links', parent=tmp_path)

        mock_index = MagicMock()
        mock_index.find_page_by_title.return_value = None
        mock_index.find_page_by_slug.return_value = None
        mock_index.find_pages_by_title_fuzzy.return_value = [{
            'url': '/garden/test/approximate-match',
            'title': 'Approximate Match',
        }]

        mh = MarkdownHandler(tmp_path, data_dir=tmp_path)
        mh._content_index = mock_index

        result = mh.parse_file('article.md')
        assert '/garden/test/approximate-match' in result['content']


# ===================================================================
# save_file
# ===================================================================

class TestSaveFile:

    def test_saves_yaml(self, tmp_path):
        mh = MarkdownHandler(tmp_path)
        mh.save_file('new.md', {'title': 'New'}, 'Body text')

        saved = (tmp_path / 'new.md').read_text(encoding='utf-8')
        assert 'title: New' in saved
        assert 'Body text' in saved

    def test_creates_subdirectories(self, tmp_path):
        mh = MarkdownHandler(tmp_path)
        mh.save_file('sub/deep/article.md', {'title': 'Deep'}, 'Content')

        assert (tmp_path / 'sub' / 'deep' / 'article.md').exists()

    def test_roundtrip_preserves_content(self, tmp_path, make_md):
        make_md('article.md', body='Original body', fmt='yaml',
                title='Round', parent=tmp_path)
        mh = MarkdownHandler(tmp_path)
        result = mh.parse_file('article.md')

        mh.save_file('article.md', result['metadata'], result['raw_content'])
        result2 = mh.parse_file('article.md')
        assert result2['raw_content'] == result['raw_content']
        assert result2['metadata']['title'] == 'Round'


# ===================================================================
# list_articles (recursive)
# ===================================================================

class TestListArticles:

    def test_finds_md_files(self, tmp_path, make_md):
        make_md('a.md', body='A', fmt='yaml', title='A', parent=tmp_path)
        make_md('b.md', body='B', fmt='yaml', title='B', parent=tmp_path)

        mh = MarkdownHandler(tmp_path)
        articles = mh.list_articles()
        titles = [a['metadata']['title'] for a in articles]
        assert 'A' in titles
        assert 'B' in titles

    def test_finds_page_dirs(self, tmp_path, make_md):
        page_dir = tmp_path / 'project.page'
        page_dir.mkdir()
        make_md('page.md', body='P', fmt='yaml', title='Project',
                parent=page_dir)

        mh = MarkdownHandler(tmp_path)
        articles = mh.list_articles()
        assert any(a['type'] == 'page' for a in articles)

    def test_recursive_finds_nested(self, tmp_path, make_md):
        sub = tmp_path / 'sub'
        sub.mkdir()
        make_md('nested.md', body='N', fmt='yaml', title='Nested',
                parent=sub)

        mh = MarkdownHandler(tmp_path)
        articles = mh.list_articles()
        assert any(a['metadata']['title'] == 'Nested' for a in articles)

    def test_sorted_by_published_date(self, tmp_path, make_md):
        make_md('old.md', body='O', fmt='yaml', title='Old',
                published_date='2020-01-01', parent=tmp_path)
        make_md('new.md', body='N', fmt='yaml', title='New',
                published_date='2024-01-01', parent=tmp_path)

        mh = MarkdownHandler(tmp_path)
        articles = mh.list_articles()
        # Sorted descending by published_date
        assert articles[0]['metadata']['title'] == 'New'
        assert articles[1]['metadata']['title'] == 'Old'

    def test_empty_dir(self, tmp_path):
        mh = MarkdownHandler(tmp_path)
        assert mh.list_articles() == []


# ===================================================================
# list_items (non-recursive)
# ===================================================================

class TestListItems:

    def test_lists_md_files(self, tmp_path, make_md):
        make_md('article.md', body='Content', fmt='yaml', title='Article',
                parent=tmp_path)
        mh = MarkdownHandler(tmp_path)
        items = mh.list_items()
        assert len(items) == 1
        assert items[0]['type'] == 'markdown'

    def test_skips_hidden_files(self, tmp_path, make_md):
        make_md('.hidden.md', body='H', fmt='yaml', title='Hidden',
                parent=tmp_path)
        mh = MarkdownHandler(tmp_path)
        items = mh.list_items()
        assert len(items) == 0

    def test_skips_config_yaml(self, tmp_path):
        import yaml
        (tmp_path / 'config.yaml').write_text(
            yaml.dump({'title': 'Config'}), encoding='utf-8')
        mh = MarkdownHandler(tmp_path)
        items = mh.list_items()
        assert not any(i.get('filename') == 'config.yaml' for i in items)

    def test_nonexistent_dir(self, tmp_path):
        mh = MarkdownHandler(tmp_path / 'nope')
        items = mh.list_items()
        assert items == []
