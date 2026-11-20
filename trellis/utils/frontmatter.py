"""
Shared frontmatter parsing, writing, and validation for Trellis.

Supports YAML (---), TOML (+++), and JSON ({}) delimited frontmatter formats.
Obsidian-style YAML (--- with Obsidian field naming) is also supported.

This module is the single source of truth for frontmatter handling, used by
both the Trellis Garden web application and TrellisSources.
"""

import json
import os
import platform
import re
import socket
import tomllib
import uuid
from datetime import date, datetime
from pathlib import Path

import yaml

# TOML write support (no stdlib writer in Python 3.11+)
_toml_dumps = None
try:
    import tomli_w
    _toml_dumps = tomli_w.dumps
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Format constants
# ---------------------------------------------------------------------------

FMT_YAML = 'yaml'
FMT_TOML = 'toml'
FMT_JSON = 'json'
FMT_OBSIDIAN = 'obsidian'


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_file(filepath):
    """Parse frontmatter and body from a markdown file.

    Returns ``(fmt, metadata, body)`` where *fmt* is one of the ``FMT_*``
    constants, or ``None`` if no frontmatter was detected.
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
            return FMT_YAML, metadata, content[m.end():]

    # TOML frontmatter: +++\n ... \n+++
    if content.startswith('+++'):
        m = re.match(r'^\+\+\+[ \t]*\n(.*?)\n\+\+\+[ \t]*\n?', content, re.DOTALL)
        if m:
            try:
                metadata = tomllib.loads(m.group(1))
            except Exception as e:
                print(f"  TOML error in {filepath}: {e}")
                return None, {}, content
            return FMT_TOML, metadata, content[m.end():]

    # JSON frontmatter: { ... } (opening brace on first line)
    if content.startswith('{'):
        # Find the matching closing brace by tracking brace depth
        depth = 0
        end_pos = None
        in_string = False
        escape_next = False
        for i, ch in enumerate(content):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end_pos = i + 1
                    break
        if end_pos is not None:
            json_text = content[:end_pos]
            try:
                metadata = json.loads(json_text)
                if isinstance(metadata, dict):
                    # Skip optional trailing newline after the closing brace
                    body_start = end_pos
                    if body_start < len(content) and content[body_start] == '\n':
                        body_start += 1
                    return FMT_JSON, metadata, content[body_start:]
            except json.JSONDecodeError as e:
                print(f"  JSON error in {filepath}: {e}")
                return None, {}, content

    return None, {}, content


def parse_string(text):
    """Parse frontmatter and body from a string.

    Same as ``parse_file`` but operates on a string instead of a file path.
    Returns ``(fmt, metadata, body)``.
    """
    if not text.strip():
        return None, {}, ''

    # YAML
    if text.startswith('---'):
        m = re.match(r'^---[ \t]*\n(.*?)\n---[ \t]*\n?', text, re.DOTALL)
        if m:
            try:
                metadata = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError:
                return None, {}, text
            return FMT_YAML, metadata, text[m.end():]

    # TOML
    if text.startswith('+++'):
        m = re.match(r'^\+\+\+[ \t]*\n(.*?)\n\+\+\+[ \t]*\n?', text, re.DOTALL)
        if m:
            try:
                metadata = tomllib.loads(m.group(1))
            except Exception:
                return None, {}, text
            return FMT_TOML, metadata, text[m.end():]

    # JSON
    if text.startswith('{'):
        depth = 0
        end_pos = None
        in_string = False
        escape_next = False
        for i, ch in enumerate(text):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end_pos = i + 1
                    break
        if end_pos is not None:
            try:
                metadata = json.loads(text[:end_pos])
                if isinstance(metadata, dict):
                    body_start = end_pos
                    if body_start < len(text) and text[body_start] == '\n':
                        body_start += 1
                    return FMT_JSON, metadata, text[body_start:]
            except json.JSONDecodeError:
                return None, {}, text

    return None, {}, text


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

def write_file(filepath, fmt, metadata, body):
    """Write a markdown file with frontmatter in the given format.

    ``fmt=FMT_OBSIDIAN`` uses YAML delimiters (``---``) but Obsidian field
    naming conventions (e.g. ``permalink`` instead of ``slug``).
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(format_frontmatter(fmt, metadata))
        f.write(body)


def format_frontmatter(fmt, metadata):
    """Serialize metadata dict into a frontmatter string with delimiters."""
    if fmt in (FMT_YAML, FMT_OBSIDIAN):
        header = '---\n'
        header += yaml.dump(
            metadata,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        header += '---\n'
        return header

    if fmt == FMT_TOML:
        header = '+++\n'
        if _toml_dumps:
            header += _toml_dumps(metadata)
        else:
            header += _toml_simple_dumps(metadata)
        header += '+++\n'
        return header

    if fmt == FMT_JSON:
        header = json.dumps(
            metadata, indent=2, default=_json_default, ensure_ascii=False
        )
        header += '\n'
        return header

    return ''


def _json_default(obj):
    """JSON serializer for objects not handled by default json encoder."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _toml_simple_dumps(data):
    """Minimal TOML serializer for flat frontmatter (fallback when tomli_w
    is not installed)."""
    lines = []
    for key, value in data.items():
        if isinstance(value, bool):
            lines.append(f'{key} = {str(value).lower()}')
        elif isinstance(value, (int, float)):
            lines.append(f'{key} = {value}')
        elif isinstance(value, (date, datetime)):
            lines.append(f'{key} = {value.isoformat()}')
        elif isinstance(value, list):
            items = ', '.join(
                f'"{v}"' if isinstance(v, str) else str(v) for v in value
            )
            lines.append(f'{key} = [{items}]')
        else:
            lines.append(f'{key} = "{value}"')
    return '\n'.join(lines) + '\n' if lines else ''


# ---------------------------------------------------------------------------
# Date helpers
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


# ---------------------------------------------------------------------------
# Slug / permalink helpers
# ---------------------------------------------------------------------------

def derive_slug(filepath):
    """Derive a URL slug from *filepath*.

    Strips ``.md`` / ``.page``, lowercases, replaces spaces with hyphens.
    """
    name = Path(filepath).stem  # removes .md
    if name.endswith('.page'):
        name = name[:-5]
    return name.lower().replace(' ', '-')


def get_slug_value(metadata):
    """Return the current slug/permalink value from metadata, or None."""
    return metadata.get('slug') or metadata.get('permalink') or None


def set_slug_value(metadata, value, fmt):
    """Set the slug/permalink field using the correct key for *fmt*.

    - obsidian -> ``permalink``
    - yaml/toml/json -> ``slug``
    """
    if fmt == FMT_OBSIDIAN:
        metadata['permalink'] = value
    else:
        metadata['slug'] = value


# ---------------------------------------------------------------------------
# GUID
# ---------------------------------------------------------------------------

def generate_guid():
    """Generate a new UUID4 string for use as a document GUID."""
    return str(uuid.uuid4())


def get_source_computer():
    """Return the hostname of this machine for the source_computer field."""
    return platform.node()


# ---------------------------------------------------------------------------
# Field validation and defaults
# ---------------------------------------------------------------------------

def ensure_required_fields(filepath, metadata, fmt, default_fmt=FMT_TOML,
                           source_defaults=None):
    """Ensure all required Trellis frontmatter fields are present.

    Adds missing fields with appropriate defaults. Returns ``(fmt, changed)``
    where *changed* is ``True`` if any fields were added or modified.

    Args:
        filepath: Path to the markdown file (for deriving dates, slug, etc.)
        metadata: Mutable metadata dict to update in place.
        fmt: Current frontmatter format, or None if file had no frontmatter.
        default_fmt: Format to use when creating frontmatter for a file that
            had none.
        source_defaults: Optional dict with keys ``public``, ``publish``,
            ``draft``, ``publish_path`` providing per-source default values.
    """
    if fmt is None:
        fmt = default_fmt

    if source_defaults is None:
        source_defaults = {}

    changed = False

    # guid
    if 'guid' not in metadata:
        metadata['guid'] = generate_guid()
        changed = True

    # date-created (from OS)
    if 'date-created' not in metadata:
        metadata['date-created'] = get_creation_date(filepath)
        changed = True

    # date-modified (from OS)
    if 'date-modified' not in metadata:
        metadata['date-modified'] = get_modified_date(filepath)
        changed = True

    # Auto-migrate: sensitive -> public (inverted)
    if 'sensitive' in metadata and 'public' not in metadata:
        metadata['public'] = not metadata['sensitive']
        del metadata['sensitive']
        changed = True

    # Per-source defaults for public, publish, draft
    src_public = source_defaults.get('public', False)
    src_publish = source_defaults.get('publish', False)
    src_draft = source_defaults.get('draft', True)

    if 'public' not in metadata:
        metadata['public'] = src_public
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
    if get_slug_value(metadata) is None:
        set_slug_value(metadata, derive_slug(filepath), fmt)
        changed = True

    return fmt, changed
