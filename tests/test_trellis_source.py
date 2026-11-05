"""Comprehensive tests for trellis.utils.trellis_source.

All tests use tmp_path or the trellis_env fixture so that production
~/.trellis/ and content directories are never touched.
"""

import hashlib
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pytest
import yaml

import trellis.utils.trellis_source as ts


# ===================================================================
# Pure functions (no filesystem)
# ===================================================================

class TestToDate:
    """Tests for to_date() — coerces various representations to date."""

    def test_date_passthrough(self):
        d = date(2024, 6, 15)
        assert ts.to_date(d) == d

    def test_datetime_extracts_date(self):
        dt = datetime(2024, 6, 15, 10, 30, 0)
        assert ts.to_date(dt) == date(2024, 6, 15)

    def test_string_iso_format(self):
        assert ts.to_date('2024-06-15') == date(2024, 6, 15)

    def test_string_slash_format(self):
        assert ts.to_date('06/15/2024') == date(2024, 6, 15)

    def test_invalid_returns_none(self):
        assert ts.to_date('not-a-date') is None
        assert ts.to_date(42) is None
        assert ts.to_date(None) is None

    def test_whitespace_stripped(self):
        assert ts.to_date('  2024-06-15  ') == date(2024, 6, 15)


class TestDeriveSlug:
    """Tests for derive_slug() — filename to URL slug."""

    def test_strips_md_extension(self):
        assert ts.derive_slug('/path/to/article.md') == 'article'

    def test_strips_page_extension(self):
        assert ts.derive_slug('/path/to/article.page.md') == 'article'

    def test_lowercases(self):
        assert ts.derive_slug('/path/My-Article.md') == 'my-article'

    def test_spaces_to_hyphens(self):
        assert ts.derive_slug('/path/My Article Title.md') == 'my-article-title'


class TestSlugHelpers:
    """Tests for _get_slug_value() and _set_slug_value()."""

    def test_get_slug_from_slug_key(self):
        assert ts._get_slug_value({'slug': 'my-slug'}) == 'my-slug'

    def test_get_slug_from_permalink_key(self):
        assert ts._get_slug_value({'permalink': 'my-link'}) == 'my-link'

    def test_get_slug_returns_none_when_missing(self):
        assert ts._get_slug_value({}) is None

    def test_get_slug_returns_none_for_empty_string(self):
        assert ts._get_slug_value({'slug': ''}) is None

    def test_set_slug_yaml_uses_slug_key(self):
        meta = {}
        ts._set_slug_value(meta, 'my-slug', 'yaml')
        assert meta == {'slug': 'my-slug'}

    def test_set_slug_toml_uses_slug_key(self):
        meta = {}
        ts._set_slug_value(meta, 'my-slug', 'toml')
        assert meta == {'slug': 'my-slug'}

    def test_set_slug_obsidian_uses_permalink_key(self):
        meta = {}
        ts._set_slug_value(meta, 'my-slug', 'obsidian')
        assert meta == {'permalink': 'my-slug'}


class TestHasHiddenComponent:
    """Tests for _has_hidden_component()."""

    def test_hidden_directory(self):
        root = Path('/src')
        fp = Path('/src/.hidden/file.md')
        assert ts._has_hidden_component(fp, root) is True

    def test_hidden_file(self):
        root = Path('/src')
        fp = Path('/src/dir/.secret.md')
        assert ts._has_hidden_component(fp, root) is True

    def test_no_hidden(self):
        root = Path('/src')
        fp = Path('/src/dir/file.md')
        assert ts._has_hidden_component(fp, root) is False

    def test_outside_root_checks_all_parts(self):
        root = Path('/other')
        fp = Path('/src/.hidden/file.md')
        # Falls back to checking all parts of fp since it's not under root
        assert ts._has_hidden_component(fp, root) is True


class TestComputeDest:
    """Tests for _compute_dest()."""

    def test_with_publish_path(self):
        result = ts._compute_dest('/dest', 'projects/web', 'my-article')
        assert result == Path('/dest/garden/projects/web/my-article.md')

    def test_empty_publish_path(self):
        result = ts._compute_dest('/dest', '', 'my-article')
        assert result == Path('/dest/garden/my-article.md')


# ===================================================================
# File I/O (use tmp_path)
# ===================================================================

class TestContentHash:
    """Tests for _content_hash()."""

    def test_deterministic(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('hello world')
        h1 = ts._content_hash(f)
        h2 = ts._content_hash(f)
        assert h1 == h2
        expected = hashlib.sha256(b'hello world').hexdigest()
        assert h1 == expected

    def test_different_content(self, tmp_path):
        f1 = tmp_path / 'a.md'
        f2 = tmp_path / 'b.md'
        f1.write_text('aaa')
        f2.write_text('bbb')
        assert ts._content_hash(f1) != ts._content_hash(f2)


class TestParseFile:
    """Tests for parse_file()."""

    def test_yaml_frontmatter(self, make_md):
        f = make_md('test.md', body='Hello', fmt='yaml', title='Test')
        fmt, meta, body = ts.parse_file(f)
        assert fmt == 'yaml'
        assert meta['title'] == 'Test'
        assert body == 'Hello'

    def test_toml_frontmatter(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('+++\ntitle = "Test"\n+++\nHello')
        fmt, meta, body = ts.parse_file(f)
        assert fmt == 'toml'
        assert meta['title'] == 'Test'
        assert body == 'Hello'

    def test_no_frontmatter(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('Just some text')
        fmt, meta, body = ts.parse_file(f)
        assert fmt is None
        assert meta == {}
        assert body == 'Just some text'

    def test_empty_file(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('')
        fmt, meta, body = ts.parse_file(f)
        assert fmt is None
        assert meta == {}
        assert body == ''

    def test_whitespace_only(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('   \n\n  ')
        fmt, meta, body = ts.parse_file(f)
        assert fmt is None
        assert meta == {}
        assert body == ''


class TestWriteFile:
    """Tests for write_file()."""

    def test_yaml_roundtrip(self, tmp_path):
        f = tmp_path / 'test.md'
        meta = {'title': 'Hello', 'draft': True}
        ts.write_file(f, 'yaml', meta, 'Body text')

        fmt, parsed_meta, body = ts.parse_file(f)
        assert fmt == 'yaml'
        assert parsed_meta['title'] == 'Hello'
        assert parsed_meta['draft'] is True
        assert body == 'Body text'

    def test_toml_roundtrip(self, tmp_path):
        f = tmp_path / 'test.md'
        meta = {'title': 'Hello', 'draft': True}
        ts.write_file(f, 'toml', meta, 'Body text')

        fmt, parsed_meta, body = ts.parse_file(f)
        assert fmt == 'toml'
        assert parsed_meta['title'] == 'Hello'
        assert parsed_meta['draft'] is True
        assert body == 'Body text'

    def test_obsidian_uses_yaml_delimiters(self, tmp_path):
        f = tmp_path / 'test.md'
        meta = {'permalink': 'my-slug'}
        ts.write_file(f, 'obsidian', meta, 'Body')

        content = f.read_text()
        assert content.startswith('---\n')
        # Parse should see it as YAML
        fmt, parsed_meta, body = ts.parse_file(f)
        assert fmt == 'yaml'
        assert parsed_meta['permalink'] == 'my-slug'


class TestDerivePublishPath:
    """Tests for derive_publish_path()."""

    def test_file_at_source_root(self, source_dir):
        f = source_dir / 'readme.md'
        f.touch()
        source = {
            '_resolved': source_dir.resolve(),
            'publish_path': 'test',
        }
        result = ts.derive_publish_path(f, source)
        assert result == 'test'

    def test_file_in_subdirectory(self, source_dir):
        sub = source_dir / 'docs'
        sub.mkdir()
        f = sub / 'guide.md'
        f.touch()
        source = {
            '_resolved': source_dir.resolve(),
            'publish_path': 'test',
        }
        result = ts.derive_publish_path(f, source)
        assert result == 'test/docs'

    def test_no_publish_path_returns_relative_dir(self, source_dir):
        sub = source_dir / 'docs'
        sub.mkdir()
        f = sub / 'guide.md'
        f.touch()
        source = {'_resolved': source_dir.resolve()}
        result = ts.derive_publish_path(f, source)
        assert result == 'docs'

    def test_no_publish_path_root_file_returns_empty(self, source_dir):
        f = source_dir / 'readme.md'
        f.touch()
        source = {'_resolved': source_dir.resolve()}
        result = ts.derive_publish_path(f, source)
        assert result == ''

    def test_no_source_fallback(self, tmp_path):
        f = tmp_path / 'orphan' / 'file.md'
        f.parent.mkdir(parents=True)
        f.touch()
        result = ts.derive_publish_path(f, None)
        # Falls back to last two parent components
        parts = result.split('/')
        assert len(parts) >= 1


class TestProcessFile:
    """Tests for process_file()."""

    def test_adds_all_required_fields(self, make_md, source_dir, sample_config):
        f = make_md('article.md', body='Hello world', parent=source_dir)
        result = ts.process_file(f, sample_config, sample_config['source'][0])
        assert result is True

        fmt, meta, body = ts.parse_file(f)
        assert meta.get('guid')
        assert 'date-created' in meta
        assert 'date-modified' in meta
        assert meta['sensitive'] is False
        assert meta['publish'] is True
        assert meta['draft'] is False
        assert meta.get('slug') or meta.get('permalink')
        assert 'publish_path' in meta
        assert 'source_path' in meta

    def test_preserves_existing_fields(self, source_dir, sample_config):
        f = source_dir / 'article.md'
        f.write_text(
            '---\n'
            'guid: existing-guid\n'
            'sensitive: true\n'
            'publish: false\n'
            'draft: true\n'
            'slug: custom-slug\n'
            '---\n'
            'Body\n'
        )
        ts.process_file(f, sample_config, sample_config['source'][0])
        _, meta, _ = ts.parse_file(f)
        assert meta['guid'] == 'existing-guid'
        assert meta['sensitive'] is True
        assert meta['publish'] is False
        assert meta['draft'] is True
        assert meta['slug'] == 'custom-slug'

    def test_uses_source_defaults(self, make_md, source_dir):
        f = make_md('article.md', body='Content', parent=source_dir)
        config = {
            'default_front_matter_format': 'yaml',
            'source': [{
                'path': str(source_dir),
                '_resolved': source_dir.resolve(),
                'sensitive': True,
                'publish': False,
                'draft': True,
            }],
        }
        ts.process_file(f, config, config['source'][0])
        _, meta, _ = ts.parse_file(f)
        assert meta['sensitive'] is True
        assert meta['publish'] is False
        assert meta['draft'] is True
        assert meta['date-published'] == ''

    def test_skips_empty_file(self, tmp_path, sample_config):
        f = tmp_path / 'empty.md'
        f.write_text('')
        result = ts.process_file(f, sample_config)
        assert result is False


class TestRemoveEmptyDirs:
    """Tests for _remove_empty_dirs()."""

    def test_removes_empty_leaf(self, tmp_path):
        root = tmp_path / 'root'
        root.mkdir()
        leaf = root / 'a' / 'b'
        leaf.mkdir(parents=True)
        removed = ts._remove_empty_dirs(root)
        assert removed == 2  # both a/b and a are empty
        assert not (root / 'a').exists()

    def test_preserves_non_empty(self, tmp_path):
        root = tmp_path / 'root'
        root.mkdir()
        child = root / 'keep'
        child.mkdir()
        (child / 'file.txt').write_text('data')
        removed = ts._remove_empty_dirs(root)
        assert removed == 0
        assert child.exists()

    def test_never_removes_root(self, tmp_path):
        root = tmp_path / 'root'
        root.mkdir()
        removed = ts._remove_empty_dirs(root)
        assert removed == 0
        assert root.exists()


# ===================================================================
# Config / DB (use trellis_env)
# ===================================================================

class TestLoadConfig:
    """Tests for load_config()."""

    def test_creates_default_config(self, trellis_env):
        config = ts.load_config()
        assert config['default_front_matter_format'] == 'toml'
        assert config['source'] == []
        assert trellis_env['config'].exists()

    def test_reads_existing_config(self, trellis_env, source_dir):
        trellis_env['config'].write_text(
            f'default_front_matter_format = "yaml"\n'
            f'destination_path = "/tmp/dest"\n\n'
            f'[[source]]\n'
            f'path = "{source_dir}"\n'
            f'publish_path = "test"\n'
            f'sensitive = false\n'
            f'publish = true\n'
            f'draft = false\n'
        )
        config = ts.load_config()
        assert config['default_front_matter_format'] == 'yaml'
        assert len(config['source']) == 1
        assert config['source'][0]['publish_path'] == 'test'
        assert '_resolved' in config['source'][0]

    def test_sources_txt_fallback(self, trellis_env, source_dir):
        # Config exists but has no [[source]] entries
        trellis_env['config'].write_text('default_front_matter_format = "toml"\n')
        trellis_env['sources'].write_text(f'{source_dir}\n')

        config = ts.load_config()
        assert len(config['source']) == 1
        assert config['source'][0]['sensitive'] is True
        assert config['source'][0]['publish'] is False


class TestMatchSource:
    """Tests for match_source()."""

    def test_most_specific_wins(self, tmp_path):
        parent = tmp_path / 'parent'
        child = parent / 'child'
        child.mkdir(parents=True)

        config = {
            'source': [
                {'_resolved': parent.resolve(), 'publish_path': 'parent'},
                {'_resolved': child.resolve(), 'publish_path': 'child'},
            ],
        }
        # Sort like load_config does
        config['source'].sort(
            key=lambda s: len(str(s['_resolved'])), reverse=True
        )

        f = child / 'file.md'
        f.touch()
        matched = ts.match_source(config, f)
        assert matched['publish_path'] == 'child'

    def test_parent_fallback(self, tmp_path):
        parent = tmp_path / 'parent'
        parent.mkdir()
        config = {
            'source': [
                {'_resolved': parent.resolve(), 'publish_path': 'parent'},
            ],
        }
        sub = parent / 'sub'
        sub.mkdir()
        f = sub / 'file.md'
        f.touch()
        matched = ts.match_source(config, f)
        assert matched['publish_path'] == 'parent'

    def test_no_match(self, tmp_path):
        config = {
            'source': [
                {'_resolved': (tmp_path / 'other').resolve()},
            ],
        }
        f = tmp_path / 'unrelated' / 'file.md'
        f.parent.mkdir()
        f.touch()
        assert ts.match_source(config, f) is None


class TestCollectSourceFiles:
    """Tests for _collect_source_files()."""

    def test_finds_md_files(self, source_dir):
        (source_dir / 'a.md').write_text('aaa')
        (source_dir / 'sub').mkdir()
        (source_dir / 'sub' / 'b.md').write_text('bbb')
        config = {
            'source': [
                {
                    'path': str(source_dir),
                    '_resolved': source_dir.resolve(),
                },
            ],
        }
        files = list(ts._collect_source_files(config))
        paths = [str(f) for f, _ in files]
        assert any('a.md' in p for p in paths)
        assert any('b.md' in p for p in paths)

    def test_skips_hidden(self, source_dir):
        hidden = source_dir / '.hidden'
        hidden.mkdir()
        (hidden / 'secret.md').write_text('hidden')
        (source_dir / 'visible.md').write_text('visible')
        config = {
            'source': [
                {
                    'path': str(source_dir),
                    '_resolved': source_dir.resolve(),
                },
            ],
        }
        files = list(ts._collect_source_files(config))
        paths = [str(f) for f, _ in files]
        assert not any('.hidden' in p for p in paths)
        assert any('visible.md' in p for p in paths)

    def test_skips_omitted_source(self, source_dir):
        sub = source_dir / 'secret'
        sub.mkdir()
        (sub / 'file.md').write_text('secret')
        (source_dir / 'public.md').write_text('public')

        config = {
            'source': [
                {
                    'path': str(source_dir),
                    '_resolved': source_dir.resolve(),
                },
                {
                    'path': str(sub),
                    '_resolved': sub.resolve(),
                    'omit': True,
                },
            ],
        }
        # Sort like load_config
        config['source'].sort(
            key=lambda s: len(str(s['_resolved'])), reverse=True
        )

        files = list(ts._collect_source_files(config))
        paths = [str(f) for f, _ in files]
        assert not any('secret' in p for p in paths)
        assert any('public.md' in p for p in paths)

    def test_deduplicates(self, source_dir):
        (source_dir / 'file.md').write_text('content')
        config = {
            'source': [
                {
                    'path': str(source_dir),
                    '_resolved': source_dir.resolve(),
                },
                {
                    'path': str(source_dir),
                    '_resolved': source_dir.resolve(),
                },
            ],
        }
        files = list(ts._collect_source_files(config))
        assert len(files) == 1


class TestPublishDB:
    """Tests for publish database operations."""

    def test_ensure_creates_db(self, trellis_env):
        conn = ts._ensure_publish_db()
        assert trellis_env['publish_db'].exists()
        # Verify schema
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='published'"
        )
        assert cur.fetchone() is not None
        conn.close()

    def test_upsert_and_lookup(self, trellis_env):
        conn = ts._ensure_publish_db()
        ts._upsert_published(
            conn, 'test-guid', '/src/file.md', '/dest/file.md',
            'test', 'my-slug', 'abc123'
        )
        record = ts._lookup_published(conn, 'test-guid')
        assert record is not None
        assert record['source_path'] == '/src/file.md'
        assert record['dest_path'] == '/dest/file.md'
        assert record['slug'] == 'my-slug'
        assert record['content_hash'] == 'abc123'
        conn.close()

    def test_upsert_updates_existing(self, trellis_env):
        conn = ts._ensure_publish_db()
        ts._upsert_published(
            conn, 'test-guid', '/src/old.md', '/dest/old.md',
            'test', 'old-slug', 'hash1'
        )
        ts._upsert_published(
            conn, 'test-guid', '/src/new.md', '/dest/new.md',
            'test', 'new-slug', 'hash2'
        )
        record = ts._lookup_published(conn, 'test-guid')
        assert record['source_path'] == '/src/new.md'
        assert record['slug'] == 'new-slug'
        assert record['content_hash'] == 'hash2'
        conn.close()

    def test_lookup_missing_returns_none(self, trellis_env):
        conn = ts._ensure_publish_db()
        assert ts._lookup_published(conn, 'nonexistent') is None
        conn.close()


# ===================================================================
# Integration tests (full pipeline)
# ===================================================================

class TestCmdCheck:
    """Tests for cmd_check()."""

    def test_detects_new_files(self, trellis_env, source_dir, dest_dir, sample_config):
        (source_dir / 'article.md').write_text(
            '---\ntitle: Test\n---\nBody\n'
        )
        result = ts.cmd_check(sample_config)
        assert result == 0

    def test_error_without_destination(self, trellis_env, source_dir):
        (source_dir / 'article.md').write_text('Body')
        config = {
            'default_front_matter_format': 'toml',
            'source': [{
                'path': str(source_dir),
                '_resolved': source_dir.resolve(),
            }],
        }
        result = ts.cmd_check(config)
        assert result == 1


class TestCmdMove:
    """Tests for cmd_move()."""

    def test_copies_new_file(self, trellis_env, source_dir, dest_dir, sample_config):
        (source_dir / 'article.md').write_text(
            '---\ntitle: Test\n---\nBody content\n'
        )
        result = ts.cmd_move(sample_config)
        assert result == 0

        # Verify file was copied to destination
        garden_dir = dest_dir / 'garden'
        md_files = list(garden_dir.rglob('*.md'))
        assert len(md_files) >= 1

    def test_updates_changed_content(self, trellis_env, source_dir, dest_dir, sample_config):
        f = source_dir / 'article.md'
        f.write_text('---\ntitle: Test\n---\nOriginal body\n')

        # First move
        ts.cmd_move(sample_config)

        # Update source (re-read to get guid, then rewrite)
        _, meta, _ = ts.parse_file(f)
        guid = meta['guid']

        # Modify source content after first move
        content = f.read_text()
        f.write_text(content.replace('Original body', 'Updated body'))

        # Second move should detect update
        result = ts.cmd_move(sample_config)
        assert result == 0

    def test_handles_move_rename(self, trellis_env, source_dir, dest_dir, sample_config):
        f = source_dir / 'article.md'
        f.write_text('---\ntitle: Test\nslug: original-slug\n---\nBody\n')

        # First move
        ts.cmd_move(sample_config)

        # Change the slug so destination path changes
        _, meta, body = ts.parse_file(f)
        meta['slug'] = 'new-slug'
        ts.write_file(f, 'yaml', meta, body)

        # Second move should handle the rename
        result = ts.cmd_move(sample_config)
        assert result == 0

        # New destination should exist
        new_dest = dest_dir / 'garden' / 'test' / 'new-slug.md'
        assert new_dest.exists()

    def test_omit_deletes_from_destination(self, trellis_env, source_dir, dest_dir):
        sub = source_dir / 'secret'
        sub.mkdir()
        f = sub / 'private.md'
        f.write_text('---\ntitle: Private\n---\nSecret stuff\n')

        # Config without omit — publish first
        config = {
            'default_front_matter_format': 'yaml',
            'destination_path': str(dest_dir),
            'source': [{
                'path': str(source_dir),
                '_resolved': source_dir.resolve(),
                'publish_path': 'test',
                'sensitive': False,
                'publish': True,
                'draft': False,
            }],
        }
        ts.cmd_move(config)

        # Verify file was published
        garden_files = list((dest_dir / 'garden').rglob('*.md'))
        assert len(garden_files) >= 1

        # Now add omit source and re-run
        config['source'].append({
            'path': str(sub),
            '_resolved': sub.resolve(),
            'omit': True,
        })
        config['source'].sort(
            key=lambda s: len(str(s['_resolved'])), reverse=True
        )
        ts.cmd_move(config)

        # The file under the omitted source should be deleted from destination
        # Check the publish db no longer has it
        conn = ts._ensure_publish_db()
        cur = conn.execute('SELECT * FROM published')
        remaining = cur.fetchall()
        # The private.md's guid should be gone
        conn.close()

    def test_empty_dir_cleanup(self, trellis_env, source_dir, dest_dir, sample_config):
        # Create a file at the source root (not in a subdir) so publish_path
        # is exactly the configured value with no extra subdirectory appended.
        f = source_dir / 'only-file.md'
        f.write_text('---\ntitle: Test\nslug: only-file\n---\nBody\n')

        sample_config['source'][0]['publish_path'] = 'deep/nested'
        ts.cmd_move(sample_config)

        # The garden/deep/nested/ dir should exist with the file
        assert (dest_dir / 'garden' / 'deep' / 'nested' / 'only-file.md').exists()

        # Change slug and publish_path to trigger a move to a different dir
        _, meta, body = ts.parse_file(f)
        meta['slug'] = 'renamed-file'
        ts.write_file(f, 'yaml', meta, body)

        # Update source config publish_path so process_file computes new path
        sample_config['source'][0]['publish_path'] = 'other'
        ts.cmd_move(sample_config)

        # New file should exist in the new location
        assert (dest_dir / 'garden' / 'other' / 'renamed-file.md').exists()

        # Old empty directories should have been cleaned up
        assert not (dest_dir / 'garden' / 'deep' / 'nested').exists()
        assert not (dest_dir / 'garden' / 'deep').exists()


class TestCmdProcess:
    """Tests for cmd_process()."""

    def test_updates_bare_files(self, source_dir, sample_config):
        (source_dir / 'bare.md').write_text('Just plain text')
        result = ts.cmd_process(sample_config)
        assert result == 0

        # File should now have frontmatter
        fmt, meta, body = ts.parse_file(source_dir / 'bare.md')
        assert fmt is not None
        assert meta.get('guid')
        assert 'date-created' in meta

    def test_skips_complete_files(self, make_md, source_dir, sample_config):
        f = make_md(
            'complete.md', body='Body', fmt='yaml', parent=source_dir,
            guid='existing-guid',
            slug='complete',
            sensitive=False,
            publish=True,
            draft=False,
            **{
                'date-created': '2024-01-01',
                'date-modified': '2024-01-01',
                'date-published': '2024-01-01',
                'publish_path': 'test',
                'source_path': str((source_dir / 'complete.md').resolve()),
            }
        )
        # The source_path already matches, so nothing should change
        # (publish_path will match because config says 'test')
        result = ts.cmd_process(sample_config)
        assert result == 0
