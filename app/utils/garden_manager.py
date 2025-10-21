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
