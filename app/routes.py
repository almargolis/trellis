from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file
from flask_login import login_required, current_user, login_user, logout_user
from app.models import User
from app.utils.markdown_handler import MarkdownHandler
from app.utils.date_manager import DateManager
from app.utils.git_handler import GitHandler
from app.utils.garden_manager import GardenManager
from flask import current_app
from werkzeug.utils import secure_filename
import os
from pathlib import Path

main_bp = Blueprint('main', __name__)
editor_bp = Blueprint('editor', __name__, url_prefix='/editor')
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ============================================================================
# Main Routes
# ============================================================================

@main_bp.route('/')
def index():
    """Show all gardens"""
    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    gardens = garden_manager.get_gardens()
    return render_template('gardens_index.html', gardens=gardens)

@main_bp.route('/garden/<garden_slug>')
def garden(garden_slug):
    """Show articles in a specific garden"""
    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    garden = garden_manager.get_garden_or_404(garden_slug)

    if not garden:
        return "Garden not found", 404

    # Get all gardens for navigation
    all_gardens = garden_manager.get_gardens()

    # Get articles for this garden
    garden_path = Path(current_app.config['CONTENT_DIR']) / garden_slug
    handler = MarkdownHandler(garden_path)
    articles = handler.list_articles()

    return render_template('garden.html',
                         garden=garden,
                         articles=articles,
                         all_gardens=all_gardens)

@main_bp.route('/garden/<garden_slug>/<slug>')
def article(garden_slug, slug):
    """Show a specific article"""
    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    garden = garden_manager.get_garden_or_404(garden_slug)

    if not garden:
        return "Garden not found", 404

    # Get all gardens for navigation
    all_gardens = garden_manager.get_gardens()

    # Get the article
    garden_path = Path(current_app.config['CONTENT_DIR']) / garden_slug
    handler = MarkdownHandler(garden_path)
    articles = handler.list_articles()

    article = next((a for a in articles if handler.generate_slug(a['filename']) == slug), None)
    if not article:
        return "Article not found", 404

    return render_template('article.html',
                         article=article,
                         garden=garden,
                         all_gardens=all_gardens)

# ============================================================================
# Authentication Routes
# ============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.get_by_username(username)
        if user and user.is_active and user.check_password(password):
            login_user(user)
            user.update_last_login()
            return redirect(url_for('editor.dashboard'))

        return render_template('login.html', error="Invalid credentials"), 401

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_user.check_password(current_password):
            return render_template('change_password.html', error="Current password is incorrect")

        if new_password != confirm_password:
            return render_template('change_password.html', error="New passwords do not match")

        if len(new_password) < 6:
            return render_template('change_password.html', error="Password must be at least 6 characters")

        current_user.set_password(new_password)
        from app.models import db
        db.session.commit()

        return render_template('change_password.html', success="Password changed successfully")

    return render_template('change_password.html')

# ============================================================================
# User Management Routes (Admin Only)
# ============================================================================

@auth_bp.route('/users')
@login_required
def list_users():
    if not current_user.is_admin():
        return "Access denied", 403

    users = User.query.all()
    return render_template('user_management.html', users=users)

@auth_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin():
        return "Access denied", 403

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'editor')

        # Validation
        if not username or not password:
            return render_template('add_user.html', error="Username and password are required")

        if User.get_by_username(username):
            return render_template('add_user.html', error="Username already exists")

        if len(password) < 6:
            return render_template('add_user.html', error="Password must be at least 6 characters")

        if role not in ['admin', 'editor']:
            role = 'editor'

        # Create user
        new_user = User(username=username, role=role)
        new_user.set_password(password)

        from app.models import db
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('auth.list_users'))

    return render_template('add_user.html')

@auth_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin():
        return "Access denied", 403

    user = User.get(user_id)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        role = request.form.get('role', 'editor')
        is_active = request.form.get('is_active') == 'on'
        new_password = request.form.get('new_password')

        if role in ['admin', 'editor']:
            user.role = role

        user.is_active = is_active

        if new_password:
            if len(new_password) < 6:
                return render_template('edit_user.html', user=user, error="Password must be at least 6 characters")
            user.set_password(new_password)

        from app.models import db
        db.session.commit()

        return redirect(url_for('auth.list_users'))

    return render_template('edit_user.html', user=user)

@auth_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        return "Access denied", 403

    # Prevent deleting yourself
    if user_id == current_user.id:
        return "Cannot delete your own account", 400

    user = User.get(user_id)
    if not user:
        return "User not found", 404

    from app.models import db
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('auth.list_users'))

# ============================================================================
# Editor Routes
# ============================================================================

@editor_bp.route('/')
@login_required
def dashboard():
    """Show all gardens and their articles"""
    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    gardens = garden_manager.get_gardens()

    # Get articles for each garden
    gardens_with_articles = []
    for garden in gardens:
        garden_path = Path(current_app.config['CONTENT_DIR']) / garden['slug']
        handler = MarkdownHandler(garden_path)
        articles = handler.list_articles()
        gardens_with_articles.append({
            'garden': garden,
            'articles': articles
        })

    return render_template('editor_dashboard.html', gardens=gardens_with_articles)

@editor_bp.route('/edit/<garden_slug>/<slug>')
@login_required
def edit(garden_slug, slug):
    """Edit a specific article"""
    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    garden = garden_manager.get_garden_or_404(garden_slug)

    if not garden:
        return "Garden not found", 404

    garden_path = Path(current_app.config['CONTENT_DIR']) / garden_slug
    handler = MarkdownHandler(garden_path)
    articles = handler.list_articles()
    article = next((a for a in articles if handler.generate_slug(a['filename']) == slug), None)

    if not article:
        return "Article not found", 404

    return render_template('editor.html', article=article, garden=garden)

@editor_bp.route('/save', methods=['POST'])
@login_required
def save():
    data = request.json
    filename = data.get('filename')
    garden_slug = data.get('garden_slug')
    metadata = data.get('metadata')
    content = data.get('content')

    # Auto-update modified date
    metadata = DateManager.auto_update_modified(metadata)

    # Save file
    garden_path = Path(current_app.config['CONTENT_DIR']) / garden_slug if garden_slug else current_app.config['CONTENT_DIR']
    handler = MarkdownHandler(garden_path)
    handler.save_file(filename, metadata, content)

    # Git commit
    git_handler = GitHandler(current_app.config['GITLAB_REPO_PATH'])
    file_path = os.path.join('content', garden_slug, filename) if garden_slug else os.path.join('content', filename)
    git_handler.auto_commit(
        file_path,
        f"Update: {metadata.get('title', filename)}"
    )

    return jsonify({'success': True, 'metadata': metadata})

@editor_bp.route('/preview', methods=['POST'])
@login_required
def preview():
    content = request.json.get('content', '')
    handler = MarkdownHandler(current_app.config['CONTENT_DIR'])
    html = handler.md.convert(content)
    return jsonify({'html': html})
