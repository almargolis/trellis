import re
import yaml
import os
from pathlib import Path

# Nicknames must be lowercase, start with a letter, and contain only
# alphanumeric characters and underscores (valid Python identifiers and
# safe directory names).
NICKNAME_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


def validate_nickname(nickname):
    """Validate a garden nickname.

    Returns the nickname if valid, raises ValueError otherwise.
    """
    if not nickname or not NICKNAME_PATTERN.match(nickname):
        raise ValueError(
            f"Invalid nickname '{nickname}'. Must start with a lowercase "
            f"letter and contain only lowercase letters, digits, and underscores."
        )
    return nickname


def derive_nickname(slug):
    """Derive a valid nickname from a garden slug.

    Replaces hyphens with underscores and validates.
    """
    candidate = slug.lower().replace('-', '_')
    # Strip leading digits/underscores
    candidate = re.sub(r'^[^a-z]+', '', candidate)
    if not candidate:
        candidate = 'garden'
    # Remove invalid characters
    candidate = re.sub(r'[^a-z0-9_]', '', candidate)
    return candidate


class GardenManager:
    def __init__(self, content_dir):
        self.content_dir = Path(content_dir)

    def get_gardens(self):
        """Get all gardens (subdirectories under content/)"""
        gardens = []

        if not self.content_dir.exists():
            return gardens

        for item in self.content_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                garden_config = self.get_garden_config(item.name)
                gardens.append({
                    'slug': item.name,
                    'nickname': garden_config.get('nickname', derive_nickname(item.name)),
                    'title': garden_config.get('title', item.name.replace('-', ' ').title()),
                    'description': garden_config.get('description', ''),
                    'config': garden_config
                })

        # Sort by title
        gardens.sort(key=lambda x: x['title'])
        return gardens

    def is_nickname_unique(self, nickname, exclude_slug=None):
        """Check if a nickname is unique among all gardens.

        Args:
            nickname: The nickname to check.
            exclude_slug: Optional garden slug to exclude (for edits).

        Returns:
            True if the nickname is unique.
        """
        for garden in self.get_gardens():
            if garden['slug'] == exclude_slug:
                continue
            if garden['nickname'] == nickname:
                return False
        return True

    def get_garden_config(self, garden_slug):
        """Load config.yaml for a specific garden.

        Ensures the returned config always has a ``nickname`` field.
        If missing from the file, one is derived from the slug.
        """
        config_path = self.content_dir / garden_slug / 'config.yaml'

        default = {
            'title': garden_slug.replace('-', ' ').title(),
            'description': '',
            'created_date': None,
            'order': 999,
            'nickname': derive_nickname(garden_slug),
        }

        if not config_path.exists():
            return default

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                if 'title' not in config:
                    config['title'] = default['title']
                if 'nickname' not in config:
                    config['nickname'] = derive_nickname(garden_slug)
                return config
        except Exception as e:
            print(f"Error reading garden config {config_path}: {e}")
            return default

    def create_garden_config(self, garden_slug, title=None, description='',
                              nickname=None):
        """Create a config.yaml for a garden.

        Args:
            garden_slug: Directory name for the garden.
            title: Display title (defaults to slug with hyphens replaced).
            description: Garden description.
            nickname: Unique identifier (validated, defaults to derived from slug).
        """
        garden_path = self.content_dir / garden_slug
        garden_path.mkdir(parents=True, exist_ok=True)

        config_path = garden_path / 'config.yaml'

        if title is None:
            title = garden_slug.replace('-', ' ').title()

        if nickname is None:
            nickname = derive_nickname(garden_slug)
        else:
            validate_nickname(nickname)

        config = {
            'title': title,
            'description': description,
            'nickname': nickname,
            'created_date': None,
            'order': 999,
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        return config

    def get_or_create_config(self, directory_name):
        """Get config for a directory, creating default if it doesn't exist

        Args:
            directory_name: Name of the directory (relative to content_dir)

        Returns:
            Dictionary with config data
        """
        config_path = self.content_dir / directory_name / 'config.yaml'

        # If config exists, load it
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    # Ensure title exists
                    if 'title' not in config:
                        config['title'] = directory_name.replace('-', ' ').replace('_', ' ').title()
                    return config
            except Exception as e:
                print(f"Error reading config {config_path}: {e}")

        # Create default config
        return self.create_garden_config(directory_name)

    def ensure_garden_configs(self):
        """Ensure all garden directories have config.yaml files"""
        gardens = []

        if not self.content_dir.exists():
            return gardens

        for item in self.content_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                config_path = item / 'config.yaml'
                if not config_path.exists():
                    # Create default config
                    self.create_garden_config(item.name)
                gardens.append(item.name)

        return gardens

    def get_garden_or_404(self, garden_slug):
        """Get garden config or return None"""
        garden_path = self.content_dir / garden_slug
        if not garden_path.exists() or not garden_path.is_dir():
            return None

        return {
            'slug': garden_slug,
            'config': self.get_garden_config(garden_slug),
            'path': garden_path
        }

    def get_hierarchy(self, garden_slug, max_depth=None):
        """Build hierarchical structure of content in a garden

        Args:
            garden_slug: The garden to analyze
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            Nested dictionary representing the directory structure
        """
        garden_path = self.content_dir / garden_slug
        if not garden_path.exists():
            return None

        def build_tree(path, current_depth=0):
            if max_depth is not None and current_depth >= max_depth:
                return None

            tree = {
                'name': path.name,
                'path': str(path.relative_to(self.content_dir)),
                'is_page': path.suffix == '.page',
                'children': []
            }

            if path.is_dir():
                for item in sorted(path.iterdir()):
                    # Skip hidden files and page.md files (they're implicit)
                    if item.name.startswith('.') or item.name == 'page.md':
                        continue

                    # Skip config files
                    if item.name in ['config.yaml', 'config.yml']:
                        continue

                    # Recurse into directories and .page directories
                    if item.is_dir():
                        subtree = build_tree(item, current_depth + 1)
                        if subtree:
                            tree['children'].append(subtree)
                    # Include .md files at this level
                    elif item.suffix == '.md':
                        tree['children'].append({
                            'name': item.name,
                            'path': str(item.relative_to(self.content_dir)),
                            'is_page': False,
                            'children': []
                        })

            return tree

        return build_tree(garden_path)

    def get_breadcrumbs(self, garden_slug, article_path):
        """Generate breadcrumb trail for an article path

        Args:
            garden_slug: The garden slug
            article_path: Path to the article (e.g., "project/subpage")

        Returns:
            List of (name, url) tuples for breadcrumb navigation
        """
        from trellis.utils.markdown_handler import MarkdownHandler

        breadcrumbs = [('Home', '/')]

        # Add garden
        garden = self.get_garden_or_404(garden_slug)
        if garden:
            garden_title = garden['config'].get('title', garden_slug)
            breadcrumbs.append((garden_title, f'/garden/{garden_slug}'))

        # Add path components
        if article_path:
            parts = article_path.split('/')
            accumulated_path = ''
            for part in parts[:-1]:  # All but the last
                accumulated_path += ('/' if accumulated_path else '') + part
                # Clean up the part for display (remove .page extension if present)
                display_name = part.replace('.page', '').replace('-', ' ').title()
                breadcrumbs.append((display_name, f'/garden/{garden_slug}/{accumulated_path}'))

            # Last part is the current article (no link)
            last_part = parts[-1].replace('.page', '').replace('-', ' ').title()
            breadcrumbs.append((last_part, None))

        return breadcrumbs

    def get_directory_public(self, dir_path):
        """Read the ``public`` setting from a directory's config.yaml.

        Returns True, False, or None (not specified).
        """
        config_path = Path(dir_path) / 'config.yaml'
        if not config_path.exists():
            return None
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            value = config.get('public')
            if value is None:
                return None
            return bool(value)
        except Exception:
            return None

    def compute_effective_public(self, garden_slug, article_path='',
                                  file_public=None):
        """Compute the effective public status for a path within a garden.

        Inheritance rules:
        - Default is ``False`` (not public) if nothing specifies it.
        - ``public: false`` on any ancestor directory overrides everything
          beneath it -- nothing under a non-public directory can be public.
        - ``public: true`` on a directory does NOT override children or files
          that are explicitly marked ``public: false``.

        Args:
            garden_slug: The garden directory name.
            article_path: Slash-separated path to the article within the garden.
            file_public: The ``public`` value from the file's own frontmatter
                (True, False, or None if not set).

        Returns:
            ``(public_specified, public_effective)`` where *public_specified*
            is *file_public* (the value on the leaf file), and
            *public_effective* is the computed boolean.
        """
        garden_path = self.content_dir / garden_slug

        # Walk from the garden root down to the target, collecting directory
        # public settings at each level.
        dirs_to_check = [garden_path]
        if article_path:
            parts = article_path.split('/')
            for part in parts:
                candidate = dirs_to_check[-1] / part
                candidate_page = dirs_to_check[-1] / (part + '.page')
                if candidate_page.is_dir():
                    dirs_to_check.append(candidate_page)
                elif candidate.is_dir():
                    dirs_to_check.append(candidate)
                # else: it's a leaf file -- handled below

        # Phase 1: check if any ancestor directory is explicitly non-public.
        # If so, effective is forced False regardless of anything else.
        inherited = None  # tracks most recent explicit dir setting
        for dir_path in dirs_to_check:
            specified = self.get_directory_public(dir_path)
            if specified is False:
                # Forced non-public -- nothing beneath can be public
                return file_public, False
            if specified is not None:
                inherited = specified

        # Phase 2: no ancestor forced non-public.  Determine effective value.
        # Priority: file's own setting > nearest ancestor setting > default
        if file_public is not None:
            effective = file_public
        elif inherited is not None:
            effective = inherited
        else:
            effective = False  # default not public

        return file_public, effective
