"""Tests for trellis.utils.garden_manager.

All tests use tmp_path fixtures so production content is never touched.
"""

import yaml
from pathlib import Path

import pytest

from trellis.utils.garden_manager import (
    GardenManager, validate_nickname, derive_nickname, NICKNAME_PATTERN,
)


# ===================================================================
# Standalone functions
# ===================================================================

class TestValidateNickname:

    def test_valid_simple(self):
        assert validate_nickname('garden') == 'garden'

    def test_valid_with_digits(self):
        assert validate_nickname('garden1') == 'garden1'

    def test_valid_with_underscores(self):
        assert validate_nickname('my_garden') == 'my_garden'

    def test_rejects_uppercase(self):
        with pytest.raises(ValueError):
            validate_nickname('Garden')

    def test_rejects_leading_digit(self):
        with pytest.raises(ValueError):
            validate_nickname('1garden')

    def test_rejects_hyphen(self):
        with pytest.raises(ValueError):
            validate_nickname('my-garden')

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            validate_nickname('')

    def test_rejects_none(self):
        with pytest.raises(ValueError):
            validate_nickname(None)


class TestDeriveNickname:

    def test_simple_slug(self):
        assert derive_nickname('projects') == 'projects'

    def test_hyphens_to_underscores(self):
        assert derive_nickname('my-garden') == 'my_garden'

    def test_uppercase_lowered(self):
        assert derive_nickname('MyGarden') == 'mygarden'

    def test_leading_digits_stripped(self):
        assert derive_nickname('123garden') == 'garden'

    def test_all_digits_fallback(self):
        assert derive_nickname('123') == 'garden'

    def test_special_chars_removed(self):
        assert derive_nickname('my@garden!') == 'mygarden'


# ===================================================================
# GardenManager
# ===================================================================

class TestGetGardens:

    def test_empty_content_dir(self, content_dir):
        gm = GardenManager(content_dir / 'garden')
        gardens = gm.get_gardens()
        assert gardens == []

    def test_finds_garden_dirs(self, content_dir, make_garden):
        make_garden('alpha', title='Alpha Garden')
        make_garden('beta', title='Beta Garden')

        gm = GardenManager(content_dir / 'garden')
        gardens = gm.get_gardens()
        titles = [g['title'] for g in gardens]
        assert 'Alpha Garden' in titles
        assert 'Beta Garden' in titles

    def test_sorted_by_title(self, content_dir, make_garden):
        make_garden('z-last', title='Zebra')
        make_garden('a-first', title='Apple')

        gm = GardenManager(content_dir / 'garden')
        gardens = gm.get_gardens()
        assert gardens[0]['title'] == 'Apple'
        assert gardens[1]['title'] == 'Zebra'

    def test_skips_hidden_dirs(self, content_dir):
        hidden = content_dir / 'garden' / '.hidden'
        hidden.mkdir()
        (hidden / 'config.yaml').write_text('title: Hidden\n')

        gm = GardenManager(content_dir / 'garden')
        gardens = gm.get_gardens()
        assert not any(g['slug'] == '.hidden' for g in gardens)


class TestGetGardenConfig:

    def test_loads_existing_config(self, content_dir, make_garden):
        make_garden('test', title='Test Title', description='A test')

        gm = GardenManager(content_dir / 'garden')
        config = gm.get_garden_config('test')
        assert config['title'] == 'Test Title'
        assert config['description'] == 'A test'

    def test_returns_defaults_when_missing(self, content_dir):
        gd = content_dir / 'garden' / 'no-config'
        gd.mkdir(parents=True)

        gm = GardenManager(content_dir / 'garden')
        config = gm.get_garden_config('no-config')
        assert config['title'] == 'No Config'
        assert 'nickname' in config

    def test_always_has_nickname(self, content_dir, make_garden):
        gd = make_garden('my-garden')
        gm = GardenManager(content_dir / 'garden')
        config = gm.get_garden_config('my-garden')
        assert 'nickname' in config


class TestCreateGardenConfig:

    def test_creates_config_file(self, content_dir):
        gm = GardenManager(content_dir / 'garden')
        config = gm.create_garden_config('new-garden', title='New Garden')

        config_path = content_dir / 'garden' / 'new-garden' / 'config.yaml'
        assert config_path.exists()
        assert config['title'] == 'New Garden'

    def test_validates_nickname(self, content_dir):
        gm = GardenManager(content_dir / 'garden')
        with pytest.raises(ValueError):
            gm.create_garden_config('test', nickname='INVALID')

    def test_derives_nickname_from_slug(self, content_dir):
        gm = GardenManager(content_dir / 'garden')
        config = gm.create_garden_config('my-garden')
        assert config['nickname'] == 'my_garden'


class TestIsNicknameUnique:

    def test_unique_when_no_gardens(self, content_dir):
        gm = GardenManager(content_dir / 'garden')
        assert gm.is_nickname_unique('anything') is True

    def test_duplicate_detected(self, content_dir, make_garden):
        make_garden('test', nickname='taken')
        gm = GardenManager(content_dir / 'garden')
        assert gm.is_nickname_unique('taken') is False

    def test_exclude_self(self, content_dir, make_garden):
        make_garden('test', nickname='taken')
        gm = GardenManager(content_dir / 'garden')
        assert gm.is_nickname_unique('taken', exclude_slug='test') is True


class TestGetGardenOr404:

    def test_returns_garden_info(self, content_dir, make_garden):
        make_garden('exists')
        gm = GardenManager(content_dir / 'garden')
        result = gm.get_garden_or_404('exists')
        assert result is not None
        assert result['slug'] == 'exists'

    def test_returns_none_when_missing(self, content_dir):
        gm = GardenManager(content_dir / 'garden')
        assert gm.get_garden_or_404('nope') is None


class TestGetHierarchy:

    def test_flat_garden(self, content_dir, make_garden, make_md):
        gd = make_garden('flat')
        make_md('article.md', body='Content', parent=gd, fmt='yaml', title='Article')

        gm = GardenManager(content_dir / 'garden')
        tree = gm.get_hierarchy('flat')
        assert tree is not None
        assert len(tree['children']) == 1
        assert tree['children'][0]['name'] == 'article.md'

    def test_nested_garden(self, content_dir, make_garden, make_md):
        gd = make_garden('nested')
        sub = gd / 'project.page'
        sub.mkdir()
        make_md('page.md', body='Project', parent=sub, fmt='yaml', title='Project')

        gm = GardenManager(content_dir / 'garden')
        tree = gm.get_hierarchy('nested')
        assert len(tree['children']) == 1
        assert tree['children'][0]['is_page'] is True

    def test_returns_none_for_missing_garden(self, content_dir):
        gm = GardenManager(content_dir / 'garden')
        assert gm.get_hierarchy('nope') is None

    def test_max_depth(self, content_dir, make_garden, make_md):
        gd = make_garden('deep')
        level1 = gd / 'a'
        level1.mkdir()
        level2 = level1 / 'b'
        level2.mkdir()
        make_md('deep.md', body='Deep', parent=level2, fmt='yaml', title='Deep')

        gm = GardenManager(content_dir / 'garden')
        tree = gm.get_hierarchy('deep', max_depth=1)
        # At depth 1, children of root should not recurse
        assert tree is not None


class TestGetBreadcrumbs:

    def test_root_breadcrumb(self, content_dir, make_garden):
        make_garden('test')
        gm = GardenManager(content_dir / 'garden')
        crumbs = gm.get_breadcrumbs('test', '')
        assert crumbs[0] == ('Home', '/')
        assert crumbs[1][0] == 'Test'

    def test_nested_breadcrumb(self, content_dir, make_garden):
        make_garden('test')
        gm = GardenManager(content_dir / 'garden')
        crumbs = gm.get_breadcrumbs('test', 'sub/article')
        assert len(crumbs) == 4  # Home, garden, sub, article
        assert crumbs[-1][1] is None  # last item has no link


class TestDirectoryPublic:

    def test_reads_public_true(self, content_dir, make_garden):
        gd = make_garden('test', public=True)
        gm = GardenManager(content_dir / 'garden')
        assert gm.get_directory_public(gd) is True

    def test_reads_public_false(self, content_dir, make_garden):
        gd = make_garden('test', public=False)
        gm = GardenManager(content_dir / 'garden')
        assert gm.get_directory_public(gd) is False

    def test_returns_none_when_unset(self, content_dir, make_garden):
        gd = make_garden('test')
        gm = GardenManager(content_dir / 'garden')
        assert gm.get_directory_public(gd) is None

    def test_returns_none_when_no_config(self, tmp_path):
        gm = GardenManager(tmp_path)
        assert gm.get_directory_public(tmp_path / 'nope') is None


class TestComputeEffectivePublic:

    def test_default_is_not_public(self, content_dir, make_garden):
        make_garden('test')
        gm = GardenManager(content_dir / 'garden')
        specified, effective = gm.compute_effective_public('test')
        assert effective is False

    def test_file_public_true(self, content_dir, make_garden):
        make_garden('test')
        gm = GardenManager(content_dir / 'garden')
        specified, effective = gm.compute_effective_public('test', file_public=True)
        assert effective is True

    def test_ancestor_false_overrides_file(self, content_dir, make_garden):
        make_garden('test', public=False)
        gm = GardenManager(content_dir / 'garden')
        specified, effective = gm.compute_effective_public(
            'test', article_path='article', file_public=True
        )
        assert effective is False

    def test_ancestor_true_inherited(self, content_dir, make_garden):
        make_garden('test', public=True)
        gm = GardenManager(content_dir / 'garden')
        specified, effective = gm.compute_effective_public('test')
        assert effective is True

    def test_file_false_not_overridden_by_ancestor(self, content_dir, make_garden):
        make_garden('test', public=True)
        gm = GardenManager(content_dir / 'garden')
        specified, effective = gm.compute_effective_public(
            'test', file_public=False
        )
        assert effective is False


class TestEnsureGardenConfigs:

    def test_creates_missing_configs(self, content_dir):
        gd = content_dir / 'garden' / 'no-config'
        gd.mkdir(parents=True)

        gm = GardenManager(content_dir / 'garden')
        gardens = gm.ensure_garden_configs()
        assert 'no-config' in gardens
        assert (gd / 'config.yaml').exists()

    def test_does_not_overwrite_existing(self, content_dir, make_garden):
        gd = make_garden('existing', title='Custom Title')

        gm = GardenManager(content_dir / 'garden')
        gm.ensure_garden_configs()

        with open(gd / 'config.yaml') as f:
            config = yaml.safe_load(f)
        assert config['title'] == 'Custom Title'
