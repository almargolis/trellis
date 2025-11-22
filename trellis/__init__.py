"""
Trellis Application Factory

Flask application factory for Trellis digital garden CMS.
"""
from flask import Flask
from flask_login import LoginManager

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from trellis.models import User
    return User.get(user_id)

def create_app(config_class=None):
    """Create and configure the Trellis Flask application.

    Args:
        config_class: Configuration class to use. If None, uses default TrellisConfig.
    """
    from trellis.config import TrellisConfig
    import os

    if config_class is None:
        config_class = TrellisConfig

    # Use data directory for instance path in production
    data_dir = os.environ.get('DATA_DIR')

    if data_dir and os.path.isabs(data_dir):
        app = Flask(__name__, instance_path=data_dir)
    else:
        app = Flask(__name__)

    app.config.from_object(config_class)

    # Initialize extensions
    from trellis.models import db
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Create tables
    with app.app_context():
        db.create_all()

    from trellis import routes
    app.register_blueprint(routes.main_bp)
    app.register_blueprint(routes.editor_bp)
    app.register_blueprint(routes.auth_bp)

    # Inject site branding into all templates
    @app.context_processor
    def inject_site_config():
        from datetime import datetime
        return {
            'site_name': app.config.get('SITE_NAME', 'Trellis'),
            'site_author': app.config.get('SITE_AUTHOR', ''),
            'now': datetime.now(),
        }

    return app
