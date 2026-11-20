"""Shared fixtures for trellis tests.

All fixtures use tmp_path to ensure production directories are never touched.
"""

import yaml
import pytest


@pytest.fixture
def make_md(tmp_path):
    """Factory fixture to create markdown files with optional frontmatter.

    Usage:
        f = make_md("article.md", body="Hello", fmt="yaml", title="Test")
        f = make_md("sub/deep.md", body="World", fmt="toml", publish=True)
        f = make_md("bare.md", body="No frontmatter")
    """

    def _make(name, body='', fmt=None, parent=None, **fields):
        if parent is None:
            parent = tmp_path
        path = parent / name
        path.parent.mkdir(parents=True, exist_ok=True)

        content = ''
        if fmt == 'yaml' or fmt == 'obsidian':
            content += '---\n'
            content += yaml.dump(fields, default_flow_style=False,
                                 sort_keys=False, allow_unicode=True)
            content += '---\n'
        elif fmt == 'toml':
            content += '+++\n'
            for k, v in fields.items():
                if isinstance(v, bool):
                    content += f'{k} = {str(v).lower()}\n'
                elif isinstance(v, str):
                    content += f'{k} = "{v}"\n'
                else:
                    content += f'{k} = {v}\n'
            content += '+++\n'
        content += body

        path.write_text(content, encoding='utf-8')
        return path

    return _make


@pytest.fixture
def content_dir(tmp_path):
    """Create and return a content directory with a garden/ subdirectory."""
    d = tmp_path / 'content'
    d.mkdir()
    (d / 'garden').mkdir()
    return d


@pytest.fixture
def data_dir(tmp_path):
    """Create and return a data directory for indexes and databases."""
    d = tmp_path / 'data'
    d.mkdir()
    return d


@pytest.fixture
def garden_dir(content_dir):
    """Create a sample garden directory with config.yaml.

    Returns the garden directory path (content_dir / 'garden' / 'test-garden').
    """
    gd = content_dir / 'garden' / 'test-garden'
    gd.mkdir(parents=True, exist_ok=True)
    config = {
        'title': 'Test Garden',
        'description': 'A test garden',
        'nickname': 'test_garden',
        'created_date': None,
        'order': 1,
    }
    with open(gd / 'config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    return gd


@pytest.fixture
def make_garden(content_dir):
    """Factory fixture to create garden directories with config.yaml.

    Usage:
        gd = make_garden("my-garden", title="My Garden", public=True)
    """

    def _make(name, parent=None, **config_fields):
        if parent is None:
            parent = content_dir / 'garden'
        gd = parent / name
        gd.mkdir(parents=True, exist_ok=True)

        config = {
            'title': config_fields.pop('title', name.replace('-', ' ').title()),
            'description': config_fields.pop('description', ''),
            'nickname': config_fields.pop('nickname', name.lower().replace('-', '_')),
            'created_date': None,
            'order': config_fields.pop('order', 999),
        }
        config.update(config_fields)

        with open(gd / 'config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return gd

    return _make
