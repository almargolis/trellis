"""
Trellis Configuration

Default Flask configuration for Trellis digital garden CMS.
Sites can override by creating their own config class.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class TrellisConfig:
    """Base configuration for Trellis applications.

    Sites should either:
    1. Set environment variables (DATA_DIR, CONTENT_DIR, SECRET_KEY)
    2. Subclass TrellisConfig and override values
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # Site branding - override these for your site
    SITE_NAME = os.environ.get('SITE_NAME', 'Trellis')
    SITE_AUTHOR = os.environ.get('SITE_AUTHOR', '')

    # Data directory - writable location for databases
    # Must be set via environment or subclass
    DATA_DIR = os.environ.get('DATA_DIR', '')

    # Content directory - defaults to DATA_DIR/content
    CONTENT_DIR = os.environ.get('CONTENT_DIR') or (
        os.path.join(DATA_DIR, 'content') if DATA_DIR else ''
    )

    # Git repository path for auto-commits
    GITLAB_REPO_PATH = os.environ.get('GITLAB_REPO_PATH', '.')

    # Database at root of data directory
    # Computed from DATA_DIR - override in subclass if needed
    @classmethod
    def get_database_uri(cls):
        """Get database URI from environment or DATA_DIR."""
        data_dir = os.environ.get('DATA_DIR', cls.DATA_DIR or '')
        return os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(data_dir, 'trellis_admin.db')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        'sqlite:///' + os.path.join(DATA_DIR, 'trellis_admin.db') if DATA_DIR else ''
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'


class DevelopmentConfig(TrellisConfig):
    """Development configuration with debug enabled."""
    DEBUG = True


class ProductionConfig(TrellisConfig):
    """Production configuration."""
    DEBUG = False
