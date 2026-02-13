"""
Trellis Application Factory

Flask application factory for Trellis digital garden CMS.

Note: Trellis uses qdflask for authentication and database management.
qdflask owns the canonical db instance and User model, which are shared
across all Flask modules (qdflask, qdcomments, trellis, etc.).
"""
from flask import Flask

__all__ = ['create_app', 'init_trellis']


def init_trellis(app, content_dir=''):
    """Initialize Trellis on a Flask app.

    Called by qd_create_app.py with content_dir resolved from
    conf/trellis.toml at generation time.
    """
    import os
    if content_dir:
        app.config['CONTENT_DIR'] = content_dir
        garden_dir = os.path.join(content_dir, 'garden')
        app.config['GARDEN_DIR'] = garden_dir
        os.makedirs(garden_dir, exist_ok=True)

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

    # Initialize Trellis (sets CONTENT_DIR/GARDEN_DIR, creates garden dir)
    init_trellis(app, app.config.get('CONTENT_DIR', ''))

    # Initialize authentication (qdflask owns db and User model)
    from qdflask import init_auth
    init_auth(app, roles=['admin', 'editor', 'reader'], login_view='auth.reader_login')

    # Initialize commenting system (shares qdflask's db)
    from qdcomments import init_comments
    init_comments(app, config={
        'COMMENTS_ENABLED': app.config.get('COMMENTS_ENABLED', True),
        'BLOCKED_WORDS_PATH': os.path.join(app.config.get('DATA_DIR', '.'), 'blocked_words.yaml'),
    })

    from trellis import routes
    app.register_blueprint(routes.main_bp)
    app.register_blueprint(routes.editor_bp)
    app.register_blueprint(routes.auth_bp)

    # Error handlers for production
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors by redirecting to home page"""
        from flask import redirect, url_for, request
        # In production, silently redirect to home instead of showing error
        if not app.debug:
            return redirect(url_for('main.index'))
        # In debug mode, show the error for developers
        return f"404 Error: {e}<br>Path: {request.path}", 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle uncaught exceptions gracefully in production"""
        from flask import redirect, url_for
        from werkzeug.routing.exceptions import BuildError

        # Handle BuildError (missing route) by redirecting to home
        if isinstance(e, BuildError):
            if not app.debug:
                app.logger.warning(f"BuildError for endpoint: {e.endpoint}")
                return redirect(url_for('main.index'))

        # In production, redirect to home for other errors
        if not app.debug:
            app.logger.error(f"Unhandled exception: {e}", exc_info=True)
            return redirect(url_for('main.index'))

        # In debug mode, let Flask show the full error
        raise e

    # Initialize email notifications
    from qdflask.email import init_mail
    init_mail(app)

    # Register Flask CLI commands
    @app.cli.command('send-comment-digest')
    def send_comment_digest():
        """Send daily digest of new comments to admins (run via cron at 1 PM Pacific)."""
        from datetime import datetime, timedelta
        from qdcomments.models import Comment
        from qdflask.email import send_to_admins

        # Count comments from last 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)
        new_comments = Comment.query.filter(Comment.created_at >= yesterday).count()

        if new_comments == 0:
            print("No new comments in last 24 hours - skipping digest")
            return

        # Count by status
        pending = Comment.query.filter(
            Comment.created_at >= yesterday,
            Comment.status == 'm'
        ).count()
        posted = Comment.query.filter(
            Comment.created_at >= yesterday,
            Comment.status == 'p'
        ).count()

        # Send digest
        body = f"""Daily Comment Digest

New comments in the last 24 hours: {new_comments}

Breakdown:
- Posted: {posted}
- Pending moderation: {pending}

Review moderation queue: {app.config.get('SERVER_NAME', 'your-site')}/comments/moderation/queue
View all activity: {app.config.get('SERVER_NAME', 'your-site')}/comments/moderation/activity
"""

        success = send_to_admins(
            subject=f"Daily Digest: {new_comments} New Comment{'s' if new_comments != 1 else ''}",
            body=body
        )

        if success:
            print(f"Digest sent: {new_comments} new comments")
        else:
            print("No verified admin emails found - digest not sent")

    return app
