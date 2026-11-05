#!/usr/bin/env python3
"""
trellis_source - Process markdown files and publish to a Trellis content tree.

Reads source configuration from ~/.trellis/config.toml, scans for markdown files,
ensures required frontmatter fields are present, and can publish files to a
Trellis content directory with git-aware move operations.

Supports YAML (---), TOML (+++), and Obsidian (--- with Obsidian field naming)
frontmatter formats.

Required fields and defaults:
    guid            auto-generated UUID
    date-created    from OS file creation time
    date-published  blank if publish=false; from 'date' tag or today if publish=true
    date-modified   from OS file modification time
    sensitive       per-source default (fallback: true)
    publish         per-source default (fallback: false)
    draft           per-source default (fallback: true)
    slug/permalink  derived from filename
    publish_path    from source config or parent directories
"""

import argparse
import hashlib
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import tomllib
import uuid
from datetime import date, datetime
from pathlib import Path

import yaml

# TOML write support (no stdlib writer exists)
_toml_dumps = None
try:
    import tomli_w
    _toml_dumps = tomli_w.dumps
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TRELLIS_DIR = Path.home() / '.trellis'
CONFIG_FILE = TRELLIS_DIR / 'config.toml'
SOURCES_FILE = TRELLIS_DIR / 'sources.txt'
PUBLISH_DB_PATH = TRELLIS_DIR / 'publish_map.db'

DEFAULT_CONFIG = 'default_front_matter_format = "toml"\n'


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config():
    """Read or create ~/.trellis/config.toml.

    Returns a dict with at least ``default_front_matter_format`` and a
    (possibly empty) ``source`` list.
    """
    TRELLIS_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(DEFAULT_CONFIG)
        print(f"Created {CONFIG_FILE}")
        print("  Configure source directories and destination_path in this file.")
        print("  See README or CLAUDE.md for the config schema.\n")

    with open(CONFIG_FILE, 'rb') as f:
        config = tomllib.load(f)

    config.setdefault('default_front_matter_format', 'toml')
    config.setdefault('source', [])

    # Fallback: read legacy sources.txt if no [[source]] entries in config
    if not config['source'] and SOURCES_FILE.exists():
        print(f"  Warning: ~/.trellis/sources.txt is deprecated. "
              f"Migrate entries to [[source]] in {CONFIG_FILE}\n")
        for line in SOURCES_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                config['source'].append({
                    'path': line,
                    'sensitive': True,
                    'publish': False,
                    'draft': True,
                })

    # Normalise source paths to resolved Path objects and store originals
    for src in config['source']:
        src['_resolved'] = Path(src['path']).expanduser().resolve()

    # Sort by path length descending (most-specific first) for matching
    config['source'].sort(key=lambda s: len(str(s['_resolved'])), reverse=True)

    return config


def match_source(config, filepath):
    """Return the most-specific ``[[source]]`` entry whose path is a parent
    of *filepath*, or ``None``."""
    resolved = Path(filepath).resolve()
    for src in config['source']:
        try:
            resolved.relative_to(src['_resolved'])
            return src
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Frontmatter parsing / writing
# ---------------------------------------------------------------------------

def parse_file(filepath):
    """Parse frontmatter and body from a markdown file.

    Returns ``(fmt, metadata, body)`` where *fmt* is ``'yaml'``, ``'toml'``,
    or ``None``.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.strip():
        return None, {}, ''

    # YAML frontmatter: ---\n ... \n---
    if content.startswith('---'):
        m = re.match(r'^---[ \t]*\n(.*?)\n---[ \t]*\n?', content, re.DOTALL)
        if m:
            try:
                metadata = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError as e:
                print(f"  YAML error in {filepath}: {e}")
                return None, {}, content
            return 'yaml', metadata, content[m.end():]

    # TOML frontmatter: +++\n ... \n+++
    if content.startswith('+++'):
        m = re.match(r'^\+\+\+[ \t]*\n(.*?)\n\+\+\+[ \t]*\n?', content, re.DOTALL)
        if m:
            try:
                metadata = tomllib.loads(m.group(1))
            except Exception as e:
                print(f"  TOML error in {filepath}: {e}")
                return None, {}, content
            return 'toml', metadata, content[m.end():]

    return None, {}, content


def write_file(filepath, fmt, metadata, body):
    """Write a markdown file with frontmatter in the given format.

    ``fmt='obsidian'`` uses YAML delimiters (``---``) but Obsidian field
    naming conventions (e.g. ``permalink`` instead of ``slug``).
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        if fmt in ('yaml', 'obsidian'):
            f.write('---\n')
            f.write(yaml.dump(
                metadata,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            ))
            f.write('---\n')
        elif fmt == 'toml':
            f.write('+++\n')
            if _toml_dumps:
                f.write(_toml_dumps(metadata))
            else:
                _write_toml_simple(f, metadata)
            f.write('+++\n')
        f.write(body)


def _write_toml_simple(f, data):
    """Minimal TOML serializer for flat frontmatter (fallback)."""
    for key, value in data.items():
        if isinstance(value, bool):
            f.write(f'{key} = {str(value).lower()}\n')
        elif isinstance(value, (int, float)):
            f.write(f'{key} = {value}\n')
        elif isinstance(value, (date, datetime)):
            f.write(f'{key} = {value.isoformat()}\n')
        elif isinstance(value, list):
            items = ', '.join(
                f'"{v}"' if isinstance(v, str) else str(v) for v in value
            )
            f.write(f'{key} = [{items}]\n')
        else:
            f.write(f'{key} = "{value}"\n')


# ---------------------------------------------------------------------------
# Field helpers
# ---------------------------------------------------------------------------

def to_date(value):
    """Coerce various date representations to ``datetime.date`` (or ``None``)."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%m-%d-%Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def get_creation_date(filepath):
    """Get file creation date. Uses st_birthtime on macOS, st_ctime on Linux."""
    stat = os.stat(filepath)
    if platform.system() == 'Darwin':
        ts = stat.st_birthtime
    else:
        ts = getattr(stat, 'st_birthtime', stat.st_ctime)
    return datetime.fromtimestamp(ts).date()


def get_modified_date(filepath):
    """Get file last-modification date."""
    return datetime.fromtimestamp(os.stat(filepath).st_mtime).date()


def derive_slug(filepath):
    """Derive a URL slug from *filepath*.

    Strips ``.md`` / ``.page``, lowercases, replaces spaces with hyphens.
    """
    name = Path(filepath).stem  # removes .md
    if name.endswith('.page'):
        name = name[:-5]
    return name.lower().replace(' ', '-')


def derive_publish_path(filepath, source):
    """Determine the ``publish_path`` for a file.

    Priority:
    1. Matched source has ``publish_path`` → use that.
    2. Last 2 parent directories of the file.
    """
    if source and source.get('publish_path'):
        return source['publish_path']

    parts = Path(filepath).resolve().parent.parts
    if len(parts) >= 2:
        return '/'.join(parts[-2:])
    elif len(parts) == 1:
        return parts[0]
    return ''


# ---------------------------------------------------------------------------
# Slug / permalink helpers
# ---------------------------------------------------------------------------

def _get_slug_value(metadata):
    """Return the current slug/permalink value from metadata, or None."""
    return metadata.get('slug') or metadata.get('permalink') or None


def _set_slug_value(metadata, value, fmt):
    """Set the slug/permalink field using the correct key for *fmt*.

    - obsidian → ``permalink``
    - yaml/toml → ``slug``
    """
    if fmt == 'obsidian':
        metadata['permalink'] = value
    else:
        metadata['slug'] = value


# ---------------------------------------------------------------------------
# File processing
# ---------------------------------------------------------------------------

def process_file(filepath, config, source=None):
    """Process a markdown file, adding any missing frontmatter fields.

    Returns ``True`` if the file was modified.
    """
    fmt, metadata, body = parse_file(filepath)

    default_fmt = config.get('default_front_matter_format', 'toml')

    # No frontmatter — will add in the configured default format
    if fmt is None:
        if not body.strip():
            return False  # skip empty files
        fmt = default_fmt

    changed = False

    # guid
    if 'guid' not in metadata:
        metadata['guid'] = str(uuid.uuid4())
        changed = True

    # date-created (from OS)
    if 'date-created' not in metadata:
        metadata['date-created'] = get_creation_date(filepath)
        changed = True

    # date-modified (from OS)
    if 'date-modified' not in metadata:
        metadata['date-modified'] = get_modified_date(filepath)
        changed = True

    # Per-source defaults for sensitive, publish, draft
    src_sensitive = source.get('sensitive', True) if source else True
    src_publish = source.get('publish', False) if source else False
    src_draft = source.get('draft', True) if source else True

    if 'sensitive' not in metadata:
        metadata['sensitive'] = src_sensitive
        changed = True

    if 'publish' not in metadata:
        metadata['publish'] = src_publish
        changed = True

    if 'draft' not in metadata:
        metadata['draft'] = src_draft
        changed = True

    # date-published (conditional)
    if 'date-published' not in metadata:
        if metadata.get('publish'):
            if 'date' in metadata and metadata['date']:
                d = to_date(metadata['date'])
                metadata['date-published'] = d if d else metadata['date']
            else:
                metadata['date-published'] = date.today()
        else:
            metadata['date-published'] = ''
        changed = True

    # slug / permalink
    if _get_slug_value(metadata) is None:
        _set_slug_value(metadata, derive_slug(filepath), fmt)
        changed = True

    # publish_path
    if 'publish_path' not in metadata:
        metadata['publish_path'] = derive_publish_path(filepath, source)
        changed = True

    if changed:
        write_file(filepath, fmt, metadata, body)

    return changed


# ---------------------------------------------------------------------------
# Publish tracking database
# ---------------------------------------------------------------------------

def _ensure_publish_db():
    """Create ``~/.trellis/publish_map.db`` if it doesn't exist.

    Returns a ``sqlite3.Connection``.
    """
    TRELLIS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PUBLISH_DB_PATH))
    conn.execute('''
        CREATE TABLE IF NOT EXISTS published (
            guid TEXT PRIMARY KEY,
            source_path TEXT NOT NULL,
            dest_path TEXT NOT NULL,
            publish_path TEXT NOT NULL,
            slug TEXT NOT NULL,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            content_hash TEXT
        )
    ''')
    conn.commit()
    return conn


def _content_hash(filepath):
    """Return SHA-256 hex digest of file content."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _lookup_published(conn, guid):
    """Look up a guid in the publish map. Returns a dict or None."""
    conn.row_factory = sqlite3.Row
    cur = conn.execute('SELECT * FROM published WHERE guid = ?', (guid,))
    row = cur.fetchone()
    return dict(row) if row else None


def _upsert_published(conn, guid, source_path, dest_path, publish_path, slug, content_hash):
    """Insert or update a record in the publish map."""
    conn.execute('''
        INSERT INTO published (guid, source_path, dest_path, publish_path, slug, published_at, content_hash)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        ON CONFLICT(guid) DO UPDATE SET
            source_path = excluded.source_path,
            dest_path = excluded.dest_path,
            publish_path = excluded.publish_path,
            slug = excluded.slug,
            published_at = CURRENT_TIMESTAMP,
            content_hash = excluded.content_hash
    ''', (guid, str(source_path), str(dest_path), publish_path, slug, content_hash))
    conn.commit()


# ---------------------------------------------------------------------------
# Scan helpers
# ---------------------------------------------------------------------------

def _collect_source_files(config):
    """Yield ``(filepath, source_entry)`` for every ``.md`` file under all
    configured sources."""
    seen = set()
    for src in config['source']:
        src_path = src['_resolved']
        if not src_path.is_dir():
            print(f"  Warning: source not found, skipping: {src['path']}")
            continue
        for md_file in sorted(src_path.rglob('*.md')):
            resolved = md_file.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            # Re-match to get most-specific source
            matched = match_source(config, resolved)
            yield resolved, matched


def _publishable_files(config):
    """Yield ``(filepath, source, metadata)`` for files with publish=true
    and draft=false."""
    for filepath, source in _collect_source_files(config):
        fmt, metadata, _body = parse_file(filepath)
        if metadata.get('publish') and not metadata.get('draft'):
            yield filepath, source, metadata


# ---------------------------------------------------------------------------
# Check command
# ---------------------------------------------------------------------------

def _compute_dest(dest_root, publish_path, slug):
    """Compute destination file path."""
    return Path(dest_root) / publish_path / f"{slug}.md"


def cmd_check(config):
    """Report publishing status without making changes."""
    dest_root = config.get('destination_path')
    if not dest_root:
        print("Error: destination_path not set in config.toml")
        return 1

    dest_root = Path(dest_root).expanduser().resolve()

    conn = _ensure_publish_db()

    counts = {'new': 0, 'updated': 0, 'conflict': 0, 'moved': 0, 'ok': 0, 'orphan': 0}
    seen_guids = set()

    for filepath, source, metadata in _publishable_files(config):
        guid = metadata.get('guid')
        if not guid:
            continue
        seen_guids.add(guid)

        slug = _get_slug_value(metadata) or derive_slug(filepath)
        pub_path = metadata.get('publish_path', '')
        dest = _compute_dest(dest_root, pub_path, slug)

        record = _lookup_published(conn, guid)
        if record is None:
            print(f"  NEW:      {filepath} -> {dest}")
            counts['new'] += 1
        elif record['dest_path'] != str(dest):
            print(f"  MOVED:    {record['dest_path']} -> {dest}")
            counts['moved'] += 1
        else:
            src_hash = _content_hash(filepath)
            if src_hash != record['content_hash']:
                # Source changed — check if dest also changed
                if dest.exists():
                    dest_hash = _content_hash(dest)
                    if dest_hash != record['content_hash']:
                        print(f"  CONFLICT: {dest} modified in trellis")
                        counts['conflict'] += 1
                        continue
                print(f"  UPDATED:  {filepath} has changes to publish")
                counts['updated'] += 1
            else:
                print(f"  OK:       {filepath}")
                counts['ok'] += 1

    # Check for orphans
    cur = conn.execute('SELECT guid, dest_path FROM published')
    for row in cur.fetchall():
        if row[0] not in seen_guids:
            print(f"  ORPHAN:   {row[1]} source no longer exists")
            counts['orphan'] += 1

    conn.close()

    print()
    print(f"Summary: {counts['new']} new, {counts['updated']} updated, "
          f"{counts['moved']} moved, {counts['conflict']} conflicts, "
          f"{counts['orphan']} orphans, {counts['ok']} ok")
    return 0


# ---------------------------------------------------------------------------
# Move command
# ---------------------------------------------------------------------------

def cmd_move(config, force=False):
    """Publish/move files to the Trellis content tree."""
    dest_root = config.get('destination_path')
    if not dest_root:
        print("Error: destination_path not set in config.toml")
        return 1

    dest_root = Path(dest_root).expanduser().resolve()
    if not dest_root.is_dir():
        print(f"Error: destination_path does not exist: {dest_root}")
        return 1

    conn = _ensure_publish_db()
    counts = {'published': 0, 'updated': 0, 'moved': 0, 'skipped': 0}

    for filepath, source, metadata in _publishable_files(config):
        guid = metadata.get('guid')
        if not guid:
            continue

        slug = _get_slug_value(metadata) or derive_slug(filepath)
        pub_path = metadata.get('publish_path', '')
        dest = _compute_dest(dest_root, pub_path, slug)

        record = _lookup_published(conn, guid)

        if record is None:
            # NEW: copy to destination
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(filepath), str(dest))
            _upsert_published(conn, guid, filepath, dest, pub_path, slug,
                              _content_hash(filepath))
            print(f"  PUBLISHED: {filepath} -> {dest}")
            counts['published'] += 1

        elif record['dest_path'] != str(dest):
            # MOVED: git mv in the content tree
            old_dest = Path(record['dest_path'])
            if old_dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                result = subprocess.run(
                    ['git', 'mv', str(old_dest), str(dest)],
                    cwd=str(dest_root),
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    # Fallback: manual move if git mv fails
                    shutil.move(str(old_dest), str(dest))
                # Also update content from source
                shutil.copy2(str(filepath), str(dest))
                _upsert_published(conn, guid, filepath, dest, pub_path, slug,
                                  _content_hash(filepath))
                print(f"  MOVED:     {old_dest} -> {dest}")
                counts['moved'] += 1
            else:
                # Old dest missing, treat as new
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(filepath), str(dest))
                _upsert_published(conn, guid, filepath, dest, pub_path, slug,
                                  _content_hash(filepath))
                print(f"  PUBLISHED: {filepath} -> {dest}")
                counts['published'] += 1

        else:
            # Same path — check for updates
            src_hash = _content_hash(filepath)
            if src_hash == record['content_hash']:
                continue  # no change

            if dest.exists() and not force:
                dest_hash = _content_hash(dest)
                if dest_hash != record['content_hash']:
                    print(f"  CONFLICT:  {dest} modified in trellis (use --force to overwrite)")
                    counts['skipped'] += 1
                    continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(filepath), str(dest))
            _upsert_published(conn, guid, filepath, dest, pub_path, slug, src_hash)
            print(f"  UPDATED:   {filepath} -> {dest}")
            counts['updated'] += 1

    conn.close()

    print()
    print(f"Done. {counts['published']} published, {counts['updated']} updated, "
          f"{counts['moved']} moved, {counts['skipped']} skipped (conflicts).")
    return 0


# ---------------------------------------------------------------------------
# Default (frontmatter processing) command
# ---------------------------------------------------------------------------

def cmd_process(config):
    """Process frontmatter in all source files (default command)."""
    total = 0
    updated = 0

    for filepath, source in _collect_source_files(config):
        total += 1
        try:
            if process_file(filepath, config, source):
                updated += 1
                print(f"    Updated: {filepath}")
            else:
                print(f"    OK:      {filepath}")
        except Exception as e:
            print(f"    Error:   {filepath} — {e}")

    print(f"\nDone. Processed {total} file(s), updated {updated}.")
    return 0


# ---------------------------------------------------------------------------
# Main / CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog='trellis-source',
        description='Process markdown frontmatter and publish to a Trellis content tree.',
    )
    sub = parser.add_subparsers(dest='command')

    sub.add_parser('process', help='Process frontmatter in source files (default)')
    sub.add_parser('check', help='Report publishing status without changes')

    move_parser = sub.add_parser('move', help='Publish/move files to Trellis content tree')
    move_parser.add_argument('--force', action='store_true',
                             help='Overwrite even if trellis copy is newer')

    args = parser.parse_args()

    print("trellis-source — markdown frontmatter processor\n")

    config = load_config()

    if not config['source']:
        print("No source directories configured.")
        print(f"Add [[source]] entries to {CONFIG_FILE}")
        return 1

    command = args.command or 'process'

    if command == 'process':
        return cmd_process(config)
    elif command == 'check':
        return cmd_check(config)
    elif command == 'move':
        return cmd_move(config, force=args.force)

    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
