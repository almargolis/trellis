from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file
from flask_login import login_required, current_user, login_user, logout_user
from trellis.models import User
from trellis.models.content_index import ContentIndex
from trellis.utils.markdown_handler import MarkdownHandler
from trellis.utils.date_manager import DateManager
from trellis.utils.git_handler import GitHandler
from trellis.utils.garden_manager import GardenManager
from trellis.utils.search_index import SearchIndex
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
    """Show all gardens, root-level pages, and recently updated pages"""
    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    gardens = garden_manager.get_gardens()

    # Get root-level pages (markdown files and .page directories at content root)
    content_path = Path(current_app.config['CONTENT_DIR'])
    handler = MarkdownHandler(content_path)
    root_items = []
    for item in handler.list_items():
        # Only include pages, not directories (those are gardens)
        if item.get('type') in ['markdown', 'page']:
            root_items.append(item)

    # Get recently updated pages from content index
    recent_pages = []
    try:
        content_index = ContentIndex(current_app.config['DATA_DIR'])
        recent_pages = content_index.get_recent_pages(limit=10)
    except Exception as e:
        print(f"Error getting recent pages: {e}")

    return render_template('gardens_index.html', gardens=gardens, root_items=root_items, recent_pages=recent_pages)


@main_bp.route('/page/<path:page_path>')
def root_page(page_path):
    """Show a root-level page (markdown or .page directory at content root)"""
    content_path = Path(current_app.config['CONTENT_DIR'])
    handler = MarkdownHandler(content_path)

    # Find the page
    articles = handler.list_items()
    article = next((a for a in articles if handler.generate_slug(a['filename']) == page_path), None)

    if not article or article.get('type') not in ['markdown', 'page']:
        return "Page not found", 404

    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    all_gardens = garden_manager.get_gardens()

    breadcrumbs = [
        ('Home', '/'),
        (article['metadata'].get('title', page_path), None)
    ]

    return render_template('article.html',
                         article=article,
                         garden=None,
                         all_gardens=all_gardens,
                         breadcrumbs=breadcrumbs)


@main_bp.route('/search')
def search():
    """Search across all content"""
    query = request.args.get('q', '').strip()

    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    all_gardens = garden_manager.get_gardens()

    results = []
    error = None

    if query:
        search_index = SearchIndex(current_app.config['DATA_DIR'])
        search_result = search_index.search(query)
        results = search_result['results']
        error = search_result['error']

    return render_template('search.html',
                         query=query,
                         results=results,
                         error=error,
                         all_gardens=all_gardens)


@main_bp.route('/garden/<garden_slug>')
def garden(garden_slug):
    """Show items in a specific garden (non-recursive directory listing)"""
    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    garden = garden_manager.get_garden_or_404(garden_slug)

    if not garden:
        return "Garden not found", 404

    # Get all gardens for navigation
    all_gardens = garden_manager.get_gardens()

    # Get items (directories, pages, markdown files) at this level
    garden_path = Path(current_app.config['CONTENT_DIR']) / garden_slug
    handler = MarkdownHandler(garden_path)
    items = handler.list_items()

    # Build breadcrumbs
    breadcrumbs = [
        ('Home', '/'),
        (garden['config'].get('title', garden_slug), None)
    ]

    return render_template('garden.html',
                         garden=garden,
                         items=items,
                         all_gardens=all_gardens,
                         breadcrumbs=breadcrumbs,
                         current_path='')

@main_bp.route('/garden/<garden_slug>/<path:article_path>')
def article(garden_slug, article_path):
    """Show a specific article or directory (supports nested paths)

    This route handles two cases:
    1. Content directory - show directory listing
    2. Article/Page - show the article content

    Examples:
        /garden/projects/docs -> content directory listing
        /garden/projects/my-project -> article or page content
        /garden/projects/my-project/setup -> nested article or page
    """
    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    garden = garden_manager.get_garden_or_404(garden_slug)

    if not garden:
        return "Garden not found", 404

    # Get all gardens for navigation
    all_gardens = garden_manager.get_gardens()

    # Check if this path refers to a content directory
    content_dir = Path(current_app.config['CONTENT_DIR']) / garden_slug
    potential_dir = content_dir / article_path

    if potential_dir.exists() and potential_dir.is_dir() and potential_dir.suffix != '.page':
        # This is a content directory - show directory listing
        handler = MarkdownHandler(potential_dir)
        items = handler.list_items()

        # Get config for this directory
        config = garden_manager.get_or_create_config(f"{garden_slug}/{article_path}")

        # Build breadcrumbs
        breadcrumbs = garden_manager.get_breadcrumbs(garden_slug, article_path)

        return render_template('garden.html',
                             garden={'slug': garden_slug, 'config': config},
                             items=items,
                             all_gardens=all_gardens,
                             breadcrumbs=breadcrumbs,
                             current_path=article_path)

    # Not a directory, try to find as article/page
    handler = MarkdownHandler(content_dir)
    articles = handler.list_articles()

    # Match article by slug (which has .page extensions stripped)
    article = next((a for a in articles if handler.generate_slug(a['filename']) == article_path), None)
    if not article:
        return "Article not found", 404

    # Build breadcrumbs
    breadcrumbs = garden_manager.get_breadcrumbs(garden_slug, article_path)

    return render_template('article.html',
                         article=article,
                         garden=garden,
                         all_gardens=all_gardens,
                         breadcrumbs=breadcrumbs)

@main_bp.route('/garden/<garden_slug>/<path:article_path>/assets/<filename>')
def page_asset(garden_slug, article_path, filename):
    """Serve static assets from .page directories

    Example:
        /garden/projects/my-project/assets/screenshot.png
        -> serves projects/my-project.page/screenshot.png
    """
    from werkzeug.utils import safe_join

    # Reconstruct the .page directory path
    # article_path might be "my-project" which maps to "my-project.page"
    garden_dir = Path(current_app.config['CONTENT_DIR']) / garden_slug

    # Try to find the .page directory
    # Convert slug path back to file path with .page extensions
    parts = article_path.split('/')
    search_path = garden_dir
    for part in parts:
        # Try with .page extension first
        page_dir = search_path / f"{part}.page"
        if page_dir.exists() and page_dir.is_dir():
            search_path = page_dir
        else:
            # Try as regular directory
            regular_dir = search_path / part
            if regular_dir.exists() and regular_dir.is_dir():
                search_path = regular_dir
            else:
                return "Asset directory not found", 404

    # Now look for the file in search_path
    asset_path = search_path / filename
    if not asset_path.exists() or not asset_path.is_file():
        return "Asset not found", 404

    # Security: ensure the file is within the expected directory
    try:
        asset_path.resolve().relative_to(garden_dir.resolve())
    except ValueError:
        return "Access denied", 403

    return send_file(asset_path)

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
        from trellis.models import db
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

        from trellis.models import db
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

        from trellis.models import db
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

@editor_bp.route('/edit/<garden_slug>/<path:article_path>')
@login_required
def edit(garden_slug, article_path):
    """Edit a specific article (supports nested paths)"""
    garden_manager = GardenManager(current_app.config['CONTENT_DIR'])
    garden = garden_manager.get_garden_or_404(garden_slug)

    if not garden:
        return "Garden not found", 404

    garden_path = Path(current_app.config['CONTENT_DIR']) / garden_slug
    handler = MarkdownHandler(garden_path)
    articles = handler.list_articles()
    article = next((a for a in articles if handler.generate_slug(a['filename']) == article_path), None)

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

    # For .page directories, save to page.md inside the directory
    # filename might be "project.page" -> save to "project.page/page.md"
    save_path = filename
    if filename.endswith('.page'):
        save_path = str(Path(filename) / 'page.md')
    elif Path(garden_path / filename).is_dir() and (Path(garden_path / filename)).suffix == '.page':
        save_path = str(Path(filename) / 'page.md')

    handler.save_file(save_path, metadata, content)

    # Update content index
    try:
        content_index = ContentIndex(current_app.config['DATA_DIR'])
        slug = handler.generate_slug(filename)
        url = f"/garden/{garden_slug}/{slug}" if garden_slug else f"/garden/{slug}"
        source_file = os.path.join(garden_slug, filename) if garden_slug else filename
        content_index.upsert_page(
            url=url,
            source_file=source_file,
            metadata=metadata,
            content_dir=current_app.config['CONTENT_DIR']
        )
    except Exception as e:
        print(f"Error updating content index: {e}")

    # Git commit
    git_handler = GitHandler(current_app.config['GITLAB_REPO_PATH'])
    file_path = os.path.join('content', garden_slug, save_path) if garden_slug else os.path.join('content', save_path)
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
