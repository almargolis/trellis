"""Tests for Phase 2 Garden Features.

Covers:
- Garden nicknames (validation, derivation, uniqueness)
- Public property on directories with inheritance
- Content index public/draft columns
- Search index public/draft filtering
- Theme presets and CSS generation
"""

import os
import sqlite3
import textwrap

import pytest
import yaml

from trellis.utils.garden_manager import (
    GardenManager,
    validate_nickname,
    derive_nickname,
    NICKNAME_PATTERN,
)
from trellis.models.content_index import ContentIndex
from trellis.themes import PRESETS, get_theme_css


# ============================================================================
# Nickname Validation
# ============================================================================


class TestNicknamePattern:
    def test_valid_simple(self):
        assert NICKNAME_PATTERN.match('garden')

    def test_valid_with_digits(self):
        assert NICKNAME_PATTERN.match('garden1')

    def test_valid_with_underscores(self):
        assert NICKNAME_PATTERN.match('my_garden')

    def test_invalid_starts_with_digit(self):
        assert not NICKNAME_PATTERN.match('1garden')

    def test_invalid_starts_with_underscore(self):
        assert not NICKNAME_PATTERN.match('_garden')

    def test_invalid_has_hyphen(self):
        assert not NICKNAME_PATTERN.match('my-garden')

    def test_invalid_has_uppercase(self):
        assert not NICKNAME_PATTERN.match('Garden')

    def test_invalid_empty(self):
        assert not NICKNAME_PATTERN.match('')


class TestValidateNickname:
    def test_valid_returns_nickname(self):
        assert validate_nickname('projects') == 'projects'

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match='Invalid nickname'):
            validate_nickname('123bad')

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            validate_nickname('')

    def test_none_raises(self):
        with pytest.raises(ValueError):
            validate_nickname(None)


class TestDeriveNickname:
    def test_simple_slug(self):
        assert derive_nickname('projects') == 'projects'

    def test_hyphens_to_underscores(self):
        assert derive_nickname('my-projects') == 'my_projects'

    def test_strips_leading_digits(self):
        assert derive_nickname('123abc') == 'abc'

    def test_all_digits_returns_garden(self):
        assert derive_nickname('123') == 'garden'

    def test_uppercase_lowered(self):
        assert derive_nickname('MyGarden') == 'mygarden'


# ============================================================================
# Garden Config with Nicknames
# ============================================================================


class TestGardenNickname:
    def test_get_garden_config_derives_nickname(self, tmp_path):
        """Config without nickname gets one derived from slug."""
        garden_dir = tmp_path / 'my-garden'
        garden_dir.mkdir()
        config_path = garden_dir / 'config.yaml'
        config_path.write_text(yaml.dump({'title': 'My Garden'}))

        gm = GardenManager(tmp_path)
        config = gm.get_garden_config('my-garden')
        assert config['nickname'] == 'my_garden'

    def test_get_garden_config_preserves_explicit_nickname(self, tmp_path):
        garden_dir = tmp_path / 'projects'
        garden_dir.mkdir()
        config_path = garden_dir / 'config.yaml'
        config_path.write_text(yaml.dump({
            'title': 'Projects',
            'nickname': 'proj',
        }))

        gm = GardenManager(tmp_path)
        config = gm.get_garden_config('projects')
        assert config['nickname'] == 'proj'

    def test_get_gardens_includes_nickname(self, tmp_path):
        garden_dir = tmp_path / 'notes'
        garden_dir.mkdir()
        config_path = garden_dir / 'config.yaml'
        config_path.write_text(yaml.dump({'title': 'Notes'}))

        gm = GardenManager(tmp_path)
        gardens = gm.get_gardens()
        assert len(gardens) == 1
        assert gardens[0]['nickname'] == 'notes'

    def test_create_garden_config_with_nickname(self, tmp_path):
        gm = GardenManager(tmp_path)
        config = gm.create_garden_config('blog', nickname='my_blog')
        assert config['nickname'] == 'my_blog'

        # Verify written to disk
        saved = gm.get_garden_config('blog')
        assert saved['nickname'] == 'my_blog'

    def test_create_garden_config_validates_nickname(self, tmp_path):
        gm = GardenManager(tmp_path)
        with pytest.raises(ValueError):
            gm.create_garden_config('blog', nickname='Bad-Name')

    def test_is_nickname_unique_true(self, tmp_path):
        (tmp_path / 'alpha').mkdir()
        (tmp_path / 'alpha' / 'config.yaml').write_text(
            yaml.dump({'title': 'Alpha', 'nickname': 'alpha'})
        )
        gm = GardenManager(tmp_path)
        assert gm.is_nickname_unique('beta') is True

    def test_is_nickname_unique_false(self, tmp_path):
        (tmp_path / 'alpha').mkdir()
        (tmp_path / 'alpha' / 'config.yaml').write_text(
            yaml.dump({'title': 'Alpha', 'nickname': 'alpha'})
        )
        gm = GardenManager(tmp_path)
        assert gm.is_nickname_unique('alpha') is False

    def test_is_nickname_unique_excludes_slug(self, tmp_path):
        (tmp_path / 'alpha').mkdir()
        (tmp_path / 'alpha' / 'config.yaml').write_text(
            yaml.dump({'title': 'Alpha', 'nickname': 'alpha'})
        )
        gm = GardenManager(tmp_path)
        # Same nickname is ok when editing the same garden
        assert gm.is_nickname_unique('alpha', exclude_slug='alpha') is True

    def test_missing_config_derives_nickname(self, tmp_path):
        """Garden directory without config.yaml still returns a nickname."""
        (tmp_path / 'my-notes').mkdir()
        gm = GardenManager(tmp_path)
        config = gm.get_garden_config('my-notes')
        assert config['nickname'] == 'my_notes'


# ============================================================================
# Directory Public Property
# ============================================================================


class TestDirectoryPublic:
    def test_get_directory_public_true(self, tmp_path):
        config_path = tmp_path / 'config.yaml'
        config_path.write_text(yaml.dump({'public': True}))

        gm = GardenManager(tmp_path)
        assert gm.get_directory_public(tmp_path) is True

    def test_get_directory_public_false(self, tmp_path):
        config_path = tmp_path / 'config.yaml'
        config_path.write_text(yaml.dump({'public': False}))

        gm = GardenManager(tmp_path)
        assert gm.get_directory_public(tmp_path) is False

    def test_get_directory_public_missing(self, tmp_path):
        gm = GardenManager(tmp_path)
        assert gm.get_directory_public(tmp_path) is None

    def test_get_directory_public_not_specified(self, tmp_path):
        config_path = tmp_path / 'config.yaml'
        config_path.write_text(yaml.dump({'title': 'Test'}))

        gm = GardenManager(tmp_path)
        assert gm.get_directory_public(tmp_path) is None


class TestComputeEffectivePublic:
    """Tests for the public inheritance algorithm."""

    def _setup_garden(self, tmp_path, garden_slug, dir_configs=None):
        """Create a garden with optional directory configs.

        Args:
            dir_configs: dict mapping relative paths to config dicts.
                e.g. {'': {'public': True}, 'sub': {'public': False}}
        """
        garden_dir = tmp_path / garden_slug
        garden_dir.mkdir(parents=True, exist_ok=True)
        if dir_configs:
            for rel_path, config in dir_configs.items():
                target = garden_dir / rel_path if rel_path else garden_dir
                target.mkdir(parents=True, exist_ok=True)
                (target / 'config.yaml').write_text(yaml.dump(config))
        return GardenManager(tmp_path)

    def test_default_is_not_public(self, tmp_path):
        gm = self._setup_garden(tmp_path, 'g1')
        _, effective = gm.compute_effective_public('g1')
        assert effective is False

    def test_garden_public_true(self, tmp_path):
        gm = self._setup_garden(tmp_path, 'g1', {'': {'public': True}})
        _, effective = gm.compute_effective_public('g1')
        assert effective is True

    def test_file_overrides_inherited(self, tmp_path):
        """File-level public=False overrides garden public=True."""
        gm = self._setup_garden(tmp_path, 'g1', {'': {'public': True}})
        _, effective = gm.compute_effective_public('g1', 'article', file_public=False)
        assert effective is False

    def test_file_public_true_in_public_garden(self, tmp_path):
        gm = self._setup_garden(tmp_path, 'g1', {'': {'public': True}})
        _, effective = gm.compute_effective_public('g1', 'article', file_public=True)
        assert effective is True

    def test_ancestor_false_overrides_everything(self, tmp_path):
        """public=False on ancestor forces effective=False regardless."""
        gm = self._setup_garden(tmp_path, 'g1', {
            '': {'public': False},
        })
        # Even with file_public=True, ancestor false wins
        _, effective = gm.compute_effective_public('g1', 'article', file_public=True)
        assert effective is False

    def test_nested_dir_false_overrides_child(self, tmp_path):
        """A subdirectory with public=False blocks children."""
        gm = self._setup_garden(tmp_path, 'g1', {
            '': {'public': True},
            'private': {'public': False},
        })
        _, effective = gm.compute_effective_public(
            'g1', 'private/article', file_public=True
        )
        assert effective is False

    def test_file_inherits_from_nearest_ancestor(self, tmp_path):
        """When file has no public setting, inherits from nearest dir."""
        gm = self._setup_garden(tmp_path, 'g1', {
            '': {'public': True},
        })
        _, effective = gm.compute_effective_public('g1', 'article', file_public=None)
        assert effective is True

    def test_returns_file_public_as_specified(self, tmp_path):
        """First element of return tuple is the file's own setting."""
        gm = self._setup_garden(tmp_path, 'g1')
        specified, _ = gm.compute_effective_public('g1', 'article', file_public=True)
        assert specified is True

    def test_page_directory_checked(self, tmp_path):
        """Directories with .page suffix are checked for public setting."""
        garden_dir = tmp_path / 'g1'
        page_dir = garden_dir / 'article.page'
        page_dir.mkdir(parents=True)
        (page_dir / 'config.yaml').write_text(yaml.dump({'public': True}))

        gm = GardenManager(tmp_path)
        _, effective = gm.compute_effective_public('g1', 'article')
        assert effective is True


# ============================================================================
# Content Index Public/Draft Fields
# ============================================================================


class TestContentIndexPublicDraft:
    def test_upsert_stores_public_effective(self, tmp_path):
        ci = ContentIndex(tmp_path)
        ci.upsert_page('/test', 'test.md', {'title': 'Test'},
                       public_effective=True, draft=False)

        with ci._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT public_effective, draft FROM pages WHERE url = ?',
                ('/test',)
            ).fetchone()

        assert row['public_effective'] == 1
        assert row['draft'] == 0

    def test_upsert_stores_public_specified(self, tmp_path):
        ci = ContentIndex(tmp_path)
        ci.upsert_page('/test', 'test.md', {'title': 'T'},
                       public_specified=True, public_effective=True, draft=False)

        with ci._get_connection() as conn:
            row = conn.execute(
                'SELECT public_specified FROM pages WHERE url = ?',
                ('/test',)
            ).fetchone()

        assert row[0] == 1

    def test_upsert_null_public_specified(self, tmp_path):
        ci = ContentIndex(tmp_path)
        ci.upsert_page('/test', 'test.md', {'title': 'T'},
                       public_specified=None, draft=True)

        with ci._get_connection() as conn:
            row = conn.execute(
                'SELECT public_specified FROM pages WHERE url = ?',
                ('/test',)
            ).fetchone()

        assert row[0] is None

    def test_get_recent_pages_public_only(self, tmp_path):
        ci = ContentIndex(tmp_path)
        ci.upsert_page('/public', 'pub.md',
                       {'title': 'Public', 'updated_date': '2026-01-01'},
                       public_effective=True, draft=False)
        ci.upsert_page('/private', 'priv.md',
                       {'title': 'Private', 'updated_date': '2026-01-02'},
                       public_effective=False, draft=False)
        ci.upsert_page('/draft', 'draft.md',
                       {'title': 'Draft', 'updated_date': '2026-01-03'},
                       public_effective=True, draft=True)

        # Public only: should return only /public
        results = ci.get_recent_pages(public_only=True)
        urls = [r['url'] for r in results]
        assert '/public' in urls
        assert '/private' not in urls
        assert '/draft' not in urls

    def test_get_recent_pages_all(self, tmp_path):
        ci = ContentIndex(tmp_path)
        ci.upsert_page('/public', 'pub.md',
                       {'title': 'Public', 'updated_date': '2026-01-01'},
                       public_effective=True, draft=False)
        ci.upsert_page('/private', 'priv.md',
                       {'title': 'Private', 'updated_date': '2026-01-02'},
                       public_effective=False, draft=False)

        results = ci.get_recent_pages(public_only=False)
        urls = [r['url'] for r in results]
        assert '/public' in urls
        assert '/private' in urls

    def test_get_all_pages_public_only(self, tmp_path):
        ci = ContentIndex(tmp_path)
        ci.upsert_page('/a', 'a.md', {'title': 'A'},
                       public_effective=True, draft=False)
        ci.upsert_page('/b', 'b.md', {'title': 'B'},
                       public_effective=False, draft=False)

        results = ci.get_all_pages(public_only=True)
        urls = [r['url'] for r in results]
        assert '/a' in urls
        assert '/b' not in urls

    def test_is_page_visible_true(self, tmp_path):
        ci = ContentIndex(tmp_path)
        ci.upsert_page('/v', 'v.md', {'title': 'V'},
                       public_effective=True, draft=False)
        assert ci.is_page_visible('/v') is True

    def test_is_page_visible_draft(self, tmp_path):
        ci = ContentIndex(tmp_path)
        ci.upsert_page('/d', 'd.md', {'title': 'D'},
                       public_effective=True, draft=True)
        assert ci.is_page_visible('/d') is False

    def test_is_page_visible_private(self, tmp_path):
        ci = ContentIndex(tmp_path)
        ci.upsert_page('/p', 'p.md', {'title': 'P'},
                       public_effective=False, draft=False)
        assert ci.is_page_visible('/p') is False

    def test_is_page_visible_missing(self, tmp_path):
        ci = ContentIndex(tmp_path)
        assert ci.is_page_visible('/missing') is False


# ============================================================================
# Search Index Public/Draft Fields
# ============================================================================


class TestSearchIndexPublicDraft:
    def test_add_document_with_public_draft(self, tmp_path):
        from trellis.utils.search_index import SearchIndex
        si = SearchIndex(tmp_path)
        si.add_document(
            url='/test', source_file='test.md',
            title='Test', description='Desc', content='Body',
            public_effective=True, draft=False,
        )
        # Should not raise; verify via search
        result = si.search('Test')
        assert len(result['results']) == 1

    def test_search_public_only_filters_private(self, tmp_path):
        from trellis.utils.search_index import SearchIndex
        si = SearchIndex(tmp_path)
        si.add_document(
            url='/pub', source_file='pub.md',
            title='Public Article', description='', content='content',
            public_effective=True, draft=False,
        )
        si.add_document(
            url='/priv', source_file='priv.md',
            title='Private Article', description='', content='content',
            public_effective=False, draft=False,
        )

        result = si.search('Article', public_only=True)
        urls = [r['url'] for r in result['results']]
        assert '/pub' in urls
        assert '/priv' not in urls

    def test_search_public_only_filters_drafts(self, tmp_path):
        from trellis.utils.search_index import SearchIndex
        si = SearchIndex(tmp_path)
        si.add_document(
            url='/pub', source_file='pub.md',
            title='Published Article', description='', content='content',
            public_effective=True, draft=False,
        )
        si.add_document(
            url='/draft', source_file='draft.md',
            title='Draft Article', description='', content='content',
            public_effective=True, draft=True,
        )

        result = si.search('Article', public_only=True)
        urls = [r['url'] for r in result['results']]
        assert '/pub' in urls
        assert '/draft' not in urls

    def test_search_no_filter_returns_all(self, tmp_path):
        from trellis.utils.search_index import SearchIndex
        si = SearchIndex(tmp_path)
        si.add_document(
            url='/pub', source_file='pub.md',
            title='Public Article', description='', content='',
            public_effective=True, draft=False,
        )
        si.add_document(
            url='/priv', source_file='priv.md',
            title='Private Article', description='', content='',
            public_effective=False, draft=True,
        )

        result = si.search('Article', public_only=False)
        assert len(result['results']) == 2


# ============================================================================
# Theme Presets
# ============================================================================


class TestThemePresets:
    def test_all_presets_have_primary(self):
        for name, colors in PRESETS.items():
            assert '--primary-color' in colors, f'{name} missing --primary-color'

    def test_all_presets_have_secondary(self):
        for name, colors in PRESETS.items():
            assert '--secondary-color' in colors, f'{name} missing --secondary-color'

    def test_all_presets_have_accent(self):
        for name, colors in PRESETS.items():
            assert '--accent-color' in colors, f'{name} missing --accent-color'

    def test_preset_names(self):
        assert 'default' in PRESETS
        assert 'forest' in PRESETS
        assert 'ocean' in PRESETS
        assert 'sunset' in PRESETS
        assert 'slate' in PRESETS


class TestGetThemeCss:
    def test_default_returns_empty(self):
        assert get_theme_css('default') == ''

    def test_none_returns_empty(self):
        assert get_theme_css(None) == ''

    def test_unknown_returns_empty(self):
        assert get_theme_css('nonexistent') == ''

    def test_forest_returns_css(self):
        css = get_theme_css('forest')
        assert ':root {' in css
        assert '--primary-color' in css
        assert '#2d6a4f' in css

    def test_all_presets_produce_valid_css(self):
        for name in PRESETS:
            if name == 'default':
                continue
            css = get_theme_css(name)
            assert css.startswith(':root {'), f'{name} CSS malformed'
            assert css.endswith('}'), f'{name} CSS malformed'
