from flask import Flask
from flask_login import LoginManager
from config import DevelopmentConfig

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.get(user_id)

def create_app(config_class=DevelopmentConfig):
    # Use data directory for instance path in production
    import os
    data_dir = os.environ.get('DATA_DIR')

    if data_dir and os.path.isabs(data_dir):
        app = Flask(__name__, instance_path=data_dir)
    else:
        app = Flask(__name__)

    app.config.from_object(config_class)

    # Initialize extensions
    from app.models import db
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Create tables
    with app.app_context():
        db.create_all()

    from app import routes
    app.register_blueprint(routes.main_bp)
    app.register_blueprint(routes.editor_bp)
    app.register_blueprint(routes.auth_bp)

    return app
