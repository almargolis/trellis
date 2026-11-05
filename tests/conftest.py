"""Shared fixtures for trellis_source tests.

All fixtures use tmp_path to ensure production ~/.trellis and content
directories are never touched.
"""

import textwrap

import pytest

import trellis.utils.trellis_source as ts


@pytest.fixture
def trellis_env(tmp_path, monkeypatch):
    """Redirect all module-level paths to tmp_path/.trellis/.

    Returns a dict with keys: dir, config, sources, publish_db.
    """
    trellis_dir = tmp_path / '.trellis'
    trellis_dir.mkdir()

    config_file = trellis_dir / 'config.toml'
    sources_file = trellis_dir / 'sources.txt'
    publish_db = trellis_dir / 'publish_map.db'

    monkeypatch.setattr(ts, 'TRELLIS_DIR', trellis_dir)
    monkeypatch.setattr(ts, 'CONFIG_FILE', config_file)
    monkeypatch.setattr(ts, 'SOURCES_FILE', sources_file)
    monkeypatch.setattr(ts, 'PUBLISH_DB_PATH', publish_db)

    return {
        'dir': trellis_dir,
        'config': config_file,
        'sources': sources_file,
        'publish_db': publish_db,
    }


@pytest.fixture
def source_dir(tmp_path):
    """Create and return a source directory."""
    d = tmp_path / 'source'
    d.mkdir()
    return d


@pytest.fixture
def dest_dir(tmp_path):
    """Create and return a destination directory with garden/ subdirectory."""
    d = tmp_path / 'dest'
    d.mkdir()
    (d / 'garden').mkdir()
    return d


@pytest.fixture
def sample_config(source_dir, dest_dir):
    """Return a minimal config dict with one source and destination_path."""
    return {
        'default_front_matter_format': 'toml',
        'destination_path': str(dest_dir),
        'source': [
            {
                'path': str(source_dir),
                '_resolved': source_dir.resolve(),
                'publish_path': 'test',
                'sensitive': False,
                'publish': True,
                'draft': False,
            },
        ],
    }


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
            import yaml
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
