"""
Trellis Configuration

Default Flask configuration for Trellis digital garden CMS.
Configuration is read from conf/trellis.toml via the qdbase conf object.
"""
import os
from qdbase.qdconf import get_conf

_conf = get_conf()
_data_dir = _conf.get('trellis.content_dpath', '')


class TrellisConfig:
    """Base configuration for Trellis applications.

    Path configuration comes from conf/trellis.toml via get_conf().
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # Site branding - override these for your site
    SITE_NAME = os.environ.get('SITE_NAME', 'Trellis')
    SITE_AUTHOR = os.environ.get('SITE_AUTHOR', '')
    SITE_LOGO = _conf.get('trellis.site_logo', '')

    # Theme preset: 'default', 'forest', 'ocean', 'sunset', 'slate'
    THEME = _conf.get('trellis.theme', 'default')

    # Data and content directories - from conf object
    DATA_DIR = _data_dir
    CONTENT_DIR = _data_dir
    GARDEN_DIR = os.path.join(_data_dir, 'garden') if _data_dir else ''

    # Default frontmatter format for new files: 'yaml', 'toml', or 'json'
    DEFAULT_FRONT_MATTER_FORMAT = _conf.get(
        'trellis.default_front_matter_format', 'yaml'
    )

    # Git repository path for auto-commits
    GITLAB_REPO_PATH = os.environ.get('GITLAB_REPO_PATH', '.')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'


class DevelopmentConfig(TrellisConfig):
    """Development configuration with debug enabled."""
    DEBUG = True


class ProductionConfig(TrellisConfig):
    """Production configuration."""
    DEBUG = False
