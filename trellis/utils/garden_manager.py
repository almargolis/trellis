import yaml
import os
from pathlib import Path

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
                    'title': garden_config.get('title', item.name.replace('-', ' ').title()),
                    'description': garden_config.get('description', ''),
                    'config': garden_config
                })

        # Sort by title
        gardens.sort(key=lambda x: x['title'])
        return gardens

    def get_garden_config(self, garden_slug):
        """Load config.yaml for a specific garden"""
        config_path = self.content_dir / garden_slug / 'config.yaml'

        # Return default config if file doesn't exist
        if not config_path.exists():
            return {
                'title': garden_slug.replace('-', ' ').title(),
                'description': '',
                'created_date': None,
                'order': 999
            }

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                # Ensure title exists
                if 'title' not in config:
                    config['title'] = garden_slug.replace('-', ' ').title()
                return config
        except Exception as e:
            print(f"Error reading garden config {config_path}: {e}")
            return {
                'title': garden_slug.replace('-', ' ').title(),
                'description': '',
                'created_date': None,
                'order': 999
            }

    def create_garden_config(self, garden_slug, title=None, description=''):
        """Create a config.yaml for a garden"""
        garden_path = self.content_dir / garden_slug
        garden_path.mkdir(parents=True, exist_ok=True)

        config_path = garden_path / 'config.yaml'

        if title is None:
            title = garden_slug.replace('-', ' ').title()

        config = {
            'title': title,
            'description': description,
            'created_date': None,
            'order': 999
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
