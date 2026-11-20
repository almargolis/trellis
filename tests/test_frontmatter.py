"""Tests for trellis.utils.frontmatter.

Covers parsing, writing, and validation for YAML, TOML, and JSON frontmatter
formats, as well as auto-migration, GUID generation, and field defaults.
"""

import json
import platform
from datetime import date, datetime
from pathlib import Path

import pytest
import yaml

import trellis.utils.frontmatter as fm


# ===================================================================
# Format constants
# ===================================================================

class TestFormatConstants:
    def test_format_values(self):
        assert fm.FMT_YAML == 'yaml'
        assert fm.FMT_TOML == 'toml'
        assert fm.FMT_JSON == 'json'
        assert fm.FMT_OBSIDIAN == 'obsidian'


# ===================================================================
# Parsing: parse_file
# ===================================================================

class TestParseFileYAML:
    def test_basic_yaml(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('---\ntitle: Hello\ntags: [a, b]\n---\nBody text\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_YAML
        assert meta['title'] == 'Hello'
        assert meta['tags'] == ['a', 'b']
        assert body == 'Body text\n'

    def test_yaml_with_dates(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('---\ncreated: 2024-01-15\n---\nBody\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_YAML
        # PyYAML parses dates as datetime.date
        assert meta['created'] == date(2024, 1, 15)

    def test_yaml_error_returns_none(self, tmp_path):
        f = tmp_path / 'bad.md'
        f.write_text('---\n: invalid: yaml: [}\n---\nBody\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt is None
        assert meta == {}


class TestParseFileTOML:
    def test_basic_toml(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('+++\ntitle = "Hello"\npublish = true\n+++\nBody text\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_TOML
        assert meta['title'] == 'Hello'
        assert meta['publish'] is True
        assert body == 'Body text\n'

    def test_toml_with_date(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('+++\ncreated = 2024-01-15\n+++\nBody\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_TOML
        assert meta['created'] == date(2024, 1, 15)

    def test_toml_error_returns_none(self, tmp_path):
        f = tmp_path / 'bad.md'
        f.write_text('+++\ntitle = [invalid\n+++\nBody\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt is None
        assert meta == {}


class TestParseFileJSON:
    def test_basic_json(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('{\n  "title": "Hello",\n  "publish": true\n}\nBody text\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_JSON
        assert meta['title'] == 'Hello'
        assert meta['publish'] is True
        assert body == 'Body text\n'

    def test_json_compact(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('{"title": "Hello"}\nBody\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_JSON
        assert meta['title'] == 'Hello'
        assert body == 'Body\n'

    def test_json_nested(self, tmp_path):
        f = tmp_path / 'test.md'
        data = {"title": "Hello", "meta": {"author": "Test"}}
        f.write_text(json.dumps(data, indent=2) + '\nBody\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_JSON
        assert meta['meta']['author'] == 'Test'
        assert body == 'Body\n'

    def test_json_with_braces_in_body(self, tmp_path):
        """JSON frontmatter should not consume braces that appear in the body."""
        f = tmp_path / 'test.md'
        f.write_text('{"title": "Hello"}\nSome text with {braces}\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_JSON
        assert meta['title'] == 'Hello'
        assert 'braces' in body

    def test_json_error_returns_none(self, tmp_path):
        f = tmp_path / 'bad.md'
        f.write_text('{invalid json}\nBody\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt is None

    def test_json_with_strings_containing_braces(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('{"title": "Hello {world}"}\nBody\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_JSON
        assert meta['title'] == 'Hello {world}'
        assert body == 'Body\n'


class TestParseFileEdgeCases:
    def test_empty_file(self, tmp_path):
        f = tmp_path / 'empty.md'
        f.write_text('')
        fmt, meta, body = fm.parse_file(f)
        assert fmt is None
        assert meta == {}
        assert body == ''

    def test_whitespace_only(self, tmp_path):
        f = tmp_path / 'ws.md'
        f.write_text('   \n  \n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt is None
        assert meta == {}
        assert body == ''

    def test_no_frontmatter(self, tmp_path):
        f = tmp_path / 'plain.md'
        f.write_text('# Just a heading\n\nSome text.\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt is None
        assert meta == {}
        assert '# Just a heading' in body

    def test_empty_yaml_frontmatter(self, tmp_path):
        f = tmp_path / 'empty_yaml.md'
        f.write_text('---\n\n---\nBody\n')
        fmt, meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_YAML
        assert meta == {}


# ===================================================================
# Parsing: parse_string
# ===================================================================

class TestParseString:
    def test_yaml(self):
        fmt, meta, body = fm.parse_string('---\ntitle: Hello\n---\nBody\n')
        assert fmt == fm.FMT_YAML
        assert meta['title'] == 'Hello'

    def test_toml(self):
        fmt, meta, body = fm.parse_string('+++\ntitle = "Hello"\n+++\nBody\n')
        assert fmt == fm.FMT_TOML
        assert meta['title'] == 'Hello'

    def test_json(self):
        fmt, meta, body = fm.parse_string('{"title": "Hello"}\nBody\n')
        assert fmt == fm.FMT_JSON
        assert meta['title'] == 'Hello'

    def test_empty_string(self):
        fmt, meta, body = fm.parse_string('')
        assert fmt is None
        assert meta == {}


# ===================================================================
# Writing
# ===================================================================

class TestWriteFile:
    def test_yaml_roundtrip(self, tmp_path):
        f = tmp_path / 'out.md'
        meta = {'title': 'Test', 'publish': True}
        fm.write_file(f, fm.FMT_YAML, meta, 'Body text\n')

        fmt, parsed_meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_YAML
        assert parsed_meta['title'] == 'Test'
        assert parsed_meta['publish'] is True
        assert body == 'Body text\n'

    def test_toml_roundtrip(self, tmp_path):
        f = tmp_path / 'out.md'
        meta = {'title': 'Test', 'publish': True}
        fm.write_file(f, fm.FMT_TOML, meta, 'Body text\n')

        fmt, parsed_meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_TOML
        assert parsed_meta['title'] == 'Test'
        assert parsed_meta['publish'] is True
        assert body == 'Body text\n'

    def test_json_roundtrip(self, tmp_path):
        f = tmp_path / 'out.md'
        meta = {'title': 'Test', 'publish': True}
        fm.write_file(f, fm.FMT_JSON, meta, 'Body text\n')

        fmt, parsed_meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_JSON
        assert parsed_meta['title'] == 'Test'
        assert parsed_meta['publish'] is True
        assert body == 'Body text\n'

    def test_obsidian_uses_yaml_delimiters(self, tmp_path):
        f = tmp_path / 'out.md'
        meta = {'title': 'Test'}
        fm.write_file(f, fm.FMT_OBSIDIAN, meta, 'Body\n')

        content = f.read_text()
        assert content.startswith('---\n')

    def test_json_serializes_dates(self, tmp_path):
        f = tmp_path / 'out.md'
        meta = {'title': 'Test', 'created': date(2024, 6, 15)}
        fm.write_file(f, fm.FMT_JSON, meta, 'Body\n')

        fmt, parsed_meta, body = fm.parse_file(f)
        assert fmt == fm.FMT_JSON
        assert parsed_meta['created'] == '2024-06-15'


class TestFormatFrontmatter:
    def test_yaml_format(self):
        result = fm.format_frontmatter(fm.FMT_YAML, {'title': 'Test'})
        assert result.startswith('---\n')
        assert result.endswith('---\n')
        assert 'title: Test' in result

    def test_toml_format(self):
        result = fm.format_frontmatter(fm.FMT_TOML, {'title': 'Test'})
        assert result.startswith('+++\n')
        assert result.endswith('+++\n')
        assert 'title' in result

    def test_json_format(self):
        result = fm.format_frontmatter(fm.FMT_JSON, {'title': 'Test'})
        parsed = json.loads(result.strip())
        assert parsed['title'] == 'Test'

    def test_unknown_format_returns_empty(self):
        result = fm.format_frontmatter('unknown', {'title': 'Test'})
        assert result == ''


# ===================================================================
# Date helpers
# ===================================================================

class TestToDate:
    def test_date_passthrough(self):
        d = date(2024, 6, 15)
        assert fm.to_date(d) == d

    def test_datetime_extracts_date(self):
        dt = datetime(2024, 6, 15, 10, 30)
        assert fm.to_date(dt) == date(2024, 6, 15)

    def test_string_iso_format(self):
        assert fm.to_date('2024-06-15') == date(2024, 6, 15)

    def test_string_slash_format(self):
        assert fm.to_date('2024/06/15') == date(2024, 6, 15)

    def test_string_us_format(self):
        assert fm.to_date('06-15-2024') == date(2024, 6, 15)

    def test_invalid_returns_none(self):
        assert fm.to_date('not-a-date') is None
        assert fm.to_date(42) is None
        assert fm.to_date(None) is None

    def test_whitespace_stripped(self):
        assert fm.to_date('  2024-06-15  ') == date(2024, 6, 15)


class TestFileSystemDates:
    def test_get_creation_date(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_text('hello')
        d = fm.get_creation_date(f)
        assert isinstance(d, date)
        assert d == date.today()

    def test_get_modified_date(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_text('hello')
        d = fm.get_modified_date(f)
        assert isinstance(d, date)
        assert d == date.today()


# ===================================================================
# Slug helpers
# ===================================================================

class TestDeriveSlug:
    def test_strips_md_extension(self):
        assert fm.derive_slug('article.md') == 'article'

    def test_strips_page_extension(self):
        assert fm.derive_slug('project.page') == 'project'

    def test_lowercases(self):
        assert fm.derive_slug('My Article.md') == 'my-article'

    def test_spaces_to_hyphens(self):
        assert fm.derive_slug('my article.md') == 'my-article'


class TestSlugGetSet:
    def test_get_from_slug_key(self):
        assert fm.get_slug_value({'slug': 'my-slug'}) == 'my-slug'

    def test_get_from_permalink_key(self):
        assert fm.get_slug_value({'permalink': 'my-link'}) == 'my-link'

    def test_get_returns_none_when_missing(self):
        assert fm.get_slug_value({}) is None

    def test_get_returns_none_for_empty_string(self):
        assert fm.get_slug_value({'slug': ''}) is None

    def test_set_yaml_uses_slug_key(self):
        meta = {}
        fm.set_slug_value(meta, 'my-slug', fm.FMT_YAML)
        assert meta == {'slug': 'my-slug'}

    def test_set_toml_uses_slug_key(self):
        meta = {}
        fm.set_slug_value(meta, 'my-slug', fm.FMT_TOML)
        assert meta == {'slug': 'my-slug'}

    def test_set_json_uses_slug_key(self):
        meta = {}
        fm.set_slug_value(meta, 'my-slug', fm.FMT_JSON)
        assert meta == {'slug': 'my-slug'}

    def test_set_obsidian_uses_permalink_key(self):
        meta = {}
        fm.set_slug_value(meta, 'my-slug', fm.FMT_OBSIDIAN)
        assert meta == {'permalink': 'my-slug'}


# ===================================================================
# GUID
# ===================================================================

class TestGUID:
    def test_generate_guid_is_string(self):
        guid = fm.generate_guid()
        assert isinstance(guid, str)
        assert len(guid) == 36  # UUID4 format

    def test_generate_guid_is_unique(self):
        guids = {fm.generate_guid() for _ in range(100)}
        assert len(guids) == 100


# ===================================================================
# source_computer
# ===================================================================

class TestSourceComputer:
    def test_returns_hostname(self):
        result = fm.get_source_computer()
        assert isinstance(result, str)
        assert result == platform.node()


# ===================================================================
# ensure_required_fields
# ===================================================================

class TestEnsureRequiredFields:
    def test_adds_all_missing_fields(self, tmp_path):
        f = tmp_path / 'bare.md'
        f.write_text('Just text')
        meta = {}
        fmt, changed = fm.ensure_required_fields(f, meta, None)
        assert changed is True
        assert fmt == fm.FMT_TOML  # default format
        assert 'guid' in meta
        assert 'date-created' in meta
        assert 'date-modified' in meta
        assert 'public' in meta
        assert meta['public'] is False  # default
        assert 'publish' in meta
        assert meta['publish'] is False
        assert 'draft' in meta
        assert meta['draft'] is True
        assert 'date-published' in meta
        assert fm.get_slug_value(meta) is not None

    def test_uses_custom_default_format(self, tmp_path):
        f = tmp_path / 'bare.md'
        f.write_text('Just text')
        meta = {}
        fmt, changed = fm.ensure_required_fields(f, meta, None, default_fmt=fm.FMT_JSON)
        assert fmt == fm.FMT_JSON

    def test_preserves_existing_fields(self, tmp_path):
        f = tmp_path / 'existing.md'
        f.write_text('text')
        meta = {
            'guid': 'my-custom-guid',
            'public': True,
            'publish': True,
            'draft': False,
        }
        fmt, changed = fm.ensure_required_fields(f, meta, fm.FMT_YAML)
        assert meta['guid'] == 'my-custom-guid'
        assert meta['public'] is True
        assert meta['publish'] is True
        assert meta['draft'] is False

    def test_uses_source_defaults(self, tmp_path):
        f = tmp_path / 'test.md'
        f.write_text('text')
        meta = {}
        defaults = {'public': True, 'publish': True, 'draft': False}
        fmt, changed = fm.ensure_required_fields(
            f, meta, fm.FMT_YAML, source_defaults=defaults
        )
        assert meta['public'] is True
        assert meta['publish'] is True
        assert meta['draft'] is False

    def test_date_published_set_when_publish_true(self, tmp_path):
        f = tmp_path / 'pub.md'
        f.write_text('text')
        meta = {'publish': True}
        fm.ensure_required_fields(f, meta, fm.FMT_YAML)
        assert meta['date-published'] == date.today()

    def test_date_published_empty_when_publish_false(self, tmp_path):
        f = tmp_path / 'unpub.md'
        f.write_text('text')
        meta = {'publish': False}
        fm.ensure_required_fields(f, meta, fm.FMT_YAML)
        assert meta['date-published'] == ''

    def test_date_published_uses_existing_date_tag(self, tmp_path):
        f = tmp_path / 'dated.md'
        f.write_text('text')
        meta = {'publish': True, 'date': '2024-03-15'}
        fm.ensure_required_fields(f, meta, fm.FMT_YAML)
        assert meta['date-published'] == date(2024, 3, 15)


# ===================================================================
# Auto-migration: sensitive -> public
# ===================================================================

class TestSensitiveToPublicMigration:
    def test_migrates_sensitive_true(self, tmp_path):
        f = tmp_path / 'old.md'
        f.write_text('text')
        meta = {'sensitive': True}
        fm.ensure_required_fields(f, meta, fm.FMT_YAML)
        assert 'sensitive' not in meta
        assert meta['public'] is False

    def test_migrates_sensitive_false(self, tmp_path):
        f = tmp_path / 'old.md'
        f.write_text('text')
        meta = {'sensitive': False}
        fm.ensure_required_fields(f, meta, fm.FMT_YAML)
        assert 'sensitive' not in meta
        assert meta['public'] is True

    def test_no_migration_if_public_exists(self, tmp_path):
        f = tmp_path / 'both.md'
        f.write_text('text')
        meta = {'sensitive': True, 'public': True}
        fm.ensure_required_fields(f, meta, fm.FMT_YAML)
        # sensitive is not removed because public already exists
        assert meta['public'] is True

    def test_full_roundtrip_migration(self, tmp_path):
        """Write a file with sensitive=true, process it, verify public=false."""
        f = tmp_path / 'migrate.md'
        fm.write_file(f, fm.FMT_YAML, {'sensitive': True, 'title': 'Test'}, 'Body\n')

        fmt, meta, body = fm.parse_file(f)
        assert meta['sensitive'] is True

        fm.ensure_required_fields(f, meta, fmt)
        assert 'sensitive' not in meta
        assert meta['public'] is False

        fm.write_file(f, fmt, meta, body)
        fmt2, meta2, body2 = fm.parse_file(f)
        assert 'sensitive' not in meta2
        assert meta2['public'] is False


# ===================================================================
# TOML simple serializer fallback
# ===================================================================

class TestTomlSimpleDumps:
    def test_bool_values(self):
        result = fm._toml_simple_dumps({'flag': True, 'other': False})
        assert 'flag = true' in result
        assert 'other = false' in result

    def test_numeric_values(self):
        result = fm._toml_simple_dumps({'count': 42, 'rate': 3.14})
        assert 'count = 42' in result
        assert 'rate = 3.14' in result

    def test_string_values(self):
        result = fm._toml_simple_dumps({'name': 'hello'})
        assert 'name = "hello"' in result

    def test_date_values(self):
        result = fm._toml_simple_dumps({'created': date(2024, 6, 15)})
        assert 'created = 2024-06-15' in result

    def test_list_values(self):
        result = fm._toml_simple_dumps({'tags': ['a', 'b']})
        assert 'tags = ["a", "b"]' in result

    def test_empty_dict(self):
        result = fm._toml_simple_dumps({})
        assert result == ''
