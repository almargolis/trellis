import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # Data directory - writable location outside git repo
    DATA_DIR = os.environ.get('DATA_DIR') or os.path.join(os.path.dirname(__file__), 'data')

    # Content directory - can be in data dir for production
    CONTENT_DIR = os.environ.get('CONTENT_DIR') or os.path.join(os.path.dirname(__file__), 'content')

    GITLAB_REPO_PATH = os.environ.get('GITLAB_REPO_PATH', '.')

    # Database - now in data directory
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(
            os.environ.get('DATA_DIR') or os.path.join(os.path.dirname(__file__), 'data'),
            'blog.db'
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
