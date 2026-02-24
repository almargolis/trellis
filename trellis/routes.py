from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file
from flask_login import login_required, current_user, login_user, logout_user
from trellis.models import User
from trellis.models.content_index import ContentIndex
from trellis.utils.markdown_handler import MarkdownHandler
from trellis.utils.git_handler import GitHandler
from trellis.utils.garden_manager import GardenManager
from trellis.utils.search_index import SearchIndex
from flask import current_app
from werkzeug.utils import secure_filename
from functools import wraps
import os
from pathlib import Path
from datetime import datetime

main_bp = Blueprint('main', __name__)
editor_bp = Blueprint('editor', __name__, url_prefix='/editor')
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@main_bp.app_context_processor
def inject_site_config():
    return {
        'site_name': current_app.config.get('SITE_NAME', 'Trellis'),
        'site_author': current_app.config.get('SITE_AUTHOR', ''),
        'now': datetime.now(),
    }

# ============================================================================
# Draft Visibility Helpers
# ============================================================================

def _is_draft(item):
    """Check if a content item has draft status"""
    return item.get('metadata', {}).get('status') == 'draft'

def _can_view_drafts():
    """Check if the current user can view draft content"""
    return current_user.is_authenticated and current_user.is_editor()

# ============================================================================
# Decorators
# ============================================================================

def editor_required(f):
    """Decorator to require editor or admin role for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.editor_login'))
        if not current_user.is_editor():
            return render_template('error.html',
                error="Access Denied",
                message="You need editor or admin privileges to access this page."), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# Main Routes
# ============================================================================

@main_bp.route('/')
def index():
    """Show all gardens, root-level pages, and recently updated pages"""
    garden_manager = GardenManager(current_app.config['GARDEN_DIR'])
    gardens = garden_manager.get_gardens()

    # Get root-level pages (markdown files and .page directories at content root)
    content_path = Path(current_app.config['GARDEN_DIR'])
    handler = MarkdownHandler(content_path, current_app.config.get('DATA_DIR'))
    root_items = []
    can_view = _can_view_drafts()
    for item in handler.list_items():
        # Only include pages, not directories (those are gardens)
        if item.get('type') in ['markdown', 'page']:
            if not _is_draft(item) or can_view:
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
    content_path = Path(current_app.config['GARDEN_DIR'])
    handler = MarkdownHandler(content_path, current_app.config.get('DATA_DIR'))

    # Find the page
    articles = handler.list_items()
    article = next((a for a in articles if handler.generate_slug(a['filename']) == page_path), None)

    if not article or article.get('type') not in ['markdown', 'page']:
        return "Page not found", 404

    if _is_draft(article) and not _can_view_drafts():
        return "Page not found", 404

    garden_manager = GardenManager(current_app.config['GARDEN_DIR'])
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

    garden_manager = GardenManager(current_app.config['GARDEN_DIR'])
    all_gardens = garden_manager.get_gardens()

    results = []
    error = None

    if query:
        search_index = SearchIndex(current_app.config['DATA_DIR'])
        search_result = search_index.search(query)
        results = search_result['results']
        error = search_result['error']

        # Hide drafts from non-editors
        if not _can_view_drafts():
            results = [r for r in results if r.get('status', 'published') != 'draft']

    return render_template('search.html',
                         query=query,
                         results=results,
                         error=error,
                         all_gardens=all_gardens)


@main_bp.route('/garden/<garden_slug>')
def garden(garden_slug):
    """Show items in a specific garden (non-recursive directory listing)"""
    garden_manager = GardenManager(current_app.config['GARDEN_DIR'])
    garden = garden_manager.get_garden_or_404(garden_slug)

    if not garden:
        return "Garden not found", 404

    # Get all gardens for navigation
    all_gardens = garden_manager.get_gardens()

    # Get items (directories, pages, markdown files) at this level
    garden_path = Path(current_app.config['GARDEN_DIR']) / garden_slug
    handler = MarkdownHandler(garden_path, current_app.config.get('DATA_DIR'))
    items = handler.list_items()

    # Filter out drafts for non-editors
    if not _can_view_drafts():
        items = [i for i in items if not _is_draft(i)]

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
    garden_manager = GardenManager(current_app.config['GARDEN_DIR'])
    garden = garden_manager.get_garden_or_404(garden_slug)

    if not garden:
        return "Garden not found", 404

    # Get all gardens for navigation
    all_gardens = garden_manager.get_gardens()

    # Check if this path refers to a content directory
    content_dir = Path(current_app.config['GARDEN_DIR']) / garden_slug
    potential_dir = content_dir / article_path

    if potential_dir.exists() and potential_dir.is_dir() and potential_dir.suffix != '.page':
        # This is a content directory - show directory listing
        handler = MarkdownHandler(potential_dir, current_app.config.get('DATA_DIR'))
        items = handler.list_items()

        # Filter out drafts for non-editors
        if not _can_view_drafts():
            items = [i for i in items if not _is_draft(i)]

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
    handler = MarkdownHandler(content_dir, current_app.config.get('DATA_DIR'))
    articles = handler.list_articles()

    # Match article by slug (which has .page extensions stripped)
    article = next((a for a in articles if handler.generate_slug(a['filename']) == article_path), None)
    if not article:
        return "Article not found", 404

    if _is_draft(article) and not _can_view_drafts():
        return "Article not found", 404

    # Build breadcrumbs
    breadcrumbs = garden_manager.get_breadcrumbs(garden_slug, article_path)

    # Load comments for this article
    from qdcomments.models import Comment
    from qdcomments.filters import CommentContentProcessor

    content_id = f"{garden_slug}/{article_path}"
    comments_raw = Comment.get_for_content(
        content_type='article',
        content_id=content_id,
        status='p'
    ).all()

    # Process comments for display
    processor = CommentContentProcessor(current_app.config.get('BLOCKED_WORDS_PATH'))

    comments = []
    for comment in comments_raw:
        processed_html, _, _ = processor.process_comment(comment.content, comment.user_comment_style)
        comment.content = processed_html  # Replace raw content with HTML
        comments.append(comment)

    return render_template('article.html',
                         article=article,
                         garden=garden,
                         all_gardens=all_gardens,
                         breadcrumbs=breadcrumbs,
                         comments_enabled=current_app.config.get('COMMENTS_ENABLED', True),
                         comments=comments,
                         content_type='article',
                         content_id=content_id)

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
    garden_dir = Path(current_app.config['GARDEN_DIR']) / garden_slug

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
def reader_login():
    """Reader login - for commenting and viewing"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.get_by_username(username)
        if user and user.is_active and user.check_password(password):
            login_user(user)
            user.update_last_login()

            # Redirect based on next parameter or role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))

        return render_template('reader_login.html', error="Invalid credentials"), 401

    return render_template('reader_login.html')

@auth_bp.route('/editor-login', methods=['GET', 'POST'])
def editor_login():
    """Editor/Admin login - for content editing"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.get_by_username(username)
        if user and user.is_active and user.check_password(password):
            # Check if user has editor or admin role
            if not user.is_editor():
                return render_template('editor_login.html', error="You don't have permission to access the editor"), 403

            login_user(user)
            user.update_last_login()
            return redirect(url_for('editor.dashboard'))

        return render_template('editor_login.html', error="Invalid credentials"), 401

    return render_template('editor_login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Reader registration - create account for commenting"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email_address = request.form.get('email_address', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # Preserve form data for error cases
        form_data = {
            'username': username,
            'email_address': email_address
        }

        # Validation
        if not username or not email_address or not password:
            return render_template('register.html', error="All fields are required", form=form_data)

        if password != password_confirm:
            return render_template('register.html', error="Passwords do not match", form=form_data)

        if len(password) < 6:
            return render_template('register.html', error="Password must be at least 6 characters", form=form_data)

        if not User.validate_email(email_address):
            return render_template('register.html', error="Invalid email address", form=form_data)

        if User.get_by_username(username):
            return render_template('register.html', error="Username already exists", form=form_data)

        if User.get_by_email(email_address):
            return render_template('register.html', error="Email already registered", form=form_data)

        # Create reader account
        new_user = User(username=username, email_address=email_address, role='reader')
        new_user.set_password(password)

        from trellis.models import db
        db.session.add(new_user)
        db.session.commit()

        # Auto-login after registration
        login_user(new_user)
        new_user.update_last_login()

        return redirect(url_for('main.index'))

    return render_template('register.html', form={})

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
        email_address = request.form.get('email_address')
        password = request.form.get('password')
        role = request.form.get('role', 'editor')

        # Validation
        if not username or not password or not email_address:
            return render_template('add_user.html', error="Username, email, and password are required")

        if not User.validate_email(email_address):
            return render_template('add_user.html', error="Invalid email address")

        if User.get_by_username(username):
            return render_template('add_user.html', error="Username already exists")

        if User.get_by_email(email_address):
            return render_template('add_user.html', error="Email already exists")

        if len(password) < 6:
            return render_template('add_user.html', error="Password must be at least 6 characters")

        if role not in ['admin', 'editor', 'reader']:
            role = 'reader'

        # Create user
        new_user = User(username=username, email_address=email_address, role=role)
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
        email_address = request.form.get('email_address', '').strip()
        email_verified = request.form.get('email_verified') == 'on'
        role = request.form.get('role', 'reader')
        is_active = request.form.get('is_active') == 'on'
        new_password = request.form.get('new_password')

        # Handle email address update
        if email_address:
            # Validate email format
            if not User.validate_email(email_address):
                return render_template('edit_user.html', user=user, error="Invalid email address")
            # Check for duplicate email (excluding current user)
            existing = User.get_by_email(email_address)
            if existing and existing.id != user.id:
                return render_template('edit_user.html', user=user, error="Email already exists")
            user.email_address = email_address
        else:
            # Allow clearing email address
            user.email_address = None

        # Update email verification status
        user.email_verified = 'Y' if email_verified else 'N'

        if role in ['admin', 'editor', 'reader']:
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
@editor_required
def dashboard():
    """Show all gardens and their articles"""
    garden_manager = GardenManager(current_app.config['GARDEN_DIR'])
    gardens = garden_manager.get_gardens()

    # Get articles for each garden
    gardens_with_articles = []
    for garden in gardens:
        garden_path = Path(current_app.config['GARDEN_DIR']) / garden['slug']
        handler = MarkdownHandler(garden_path, current_app.config.get('DATA_DIR'))
        articles = handler.list_articles()
        gardens_with_articles.append({
            'garden': garden,
            'articles': articles
        })

    return render_template('editor_dashboard.html', gardens=gardens_with_articles)

@editor_bp.route('/browse')
@editor_bp.route('/browse/<path:dir_path>')
@editor_required
def browse(dir_path=''):
    """Browse directory contents with hierarchical navigation"""
    content_dir = Path(current_app.config['GARDEN_DIR'])
    current_dir = content_dir / dir_path if dir_path else content_dir

    # Security: ensure we're within content_dir
    try:
        current_dir = current_dir.resolve()
        if not str(current_dir).startswith(str(content_dir.resolve())):
            return "Invalid path", 403
    except:
        return "Invalid path", 404

    if not current_dir.exists():
        return "Directory not found", 404

    # Build breadcrumbs
    breadcrumbs = [{'name': 'Content', 'path': ''}]
    if dir_path:
        parts = Path(dir_path).parts
        for i, part in enumerate(parts):
            path = '/'.join(parts[:i+1])
            breadcrumbs.append({'name': part, 'path': path})

    # Categorize directory contents
    gardens = []  # Regular directories (not .page)
    complex_pages = []  # .page directories
    basic_content = []  # Files (.md, .yaml, etc.)

    # Define editable extensions
    editable_extensions = {'.md', '.yaml', '.yml', '.py', '.js', '.css', '.html', '.txt', '.json', '.sh', '.xml'}

    try:
        for item in sorted(current_dir.iterdir()):
            # Skip hidden files and __pycache__
            if item.name.startswith('.') or item.name == '__pycache__':
                continue

            if item.is_dir():
                if item.suffix == '.page':
                    # Complex page directory
                    page_md = item / 'page.md'
                    has_page_md = page_md.exists()
                    complex_pages.append({
                        'name': item.stem,  # Remove .page extension
                        'full_name': item.name,
                        'path': str(Path(dir_path) / item.name) if dir_path else item.name,
                        'has_page_md': has_page_md
                    })
                else:
                    # Regular directory (garden or subdirectory)
                    config_path = item / 'config.yaml'
                    has_config = config_path.exists()

                    # Try to read title from config
                    title = item.name.replace('-', ' ').replace('_', ' ').title()
                    if has_config:
                        try:
                            import yaml
                            with open(config_path) as f:
                                config = yaml.safe_load(f)
                                title = config.get('title', title)
                        except:
                            pass

                    gardens.append({
                        'name': item.name,
                        'title': title,
                        'path': str(Path(dir_path) / item.name) if dir_path else item.name,
                        'has_config': has_config
                    })
            else:
                # File
                is_editable = item.suffix in editable_extensions
                file_type = item.suffix[1:] if item.suffix else 'file'

                basic_content.append({
                    'name': item.name,
                    'path': str(Path(dir_path) / item.name) if dir_path else item.name,
                    'is_editable': is_editable,
                    'file_type': file_type,
                    'size': item.stat().st_size
                })

    except Exception as e:
        return f"Error reading directory: {e}", 500

    return render_template('editor_browse.html',
                          breadcrumbs=breadcrumbs,
                          current_path=dir_path,
                          gardens=gardens,
                          complex_pages=complex_pages,
                          basic_content=basic_content)

@editor_bp.route('/create/garden', methods=['POST'])
@editor_required
def create_garden():
    """Create a new garden (directory with config.yaml)"""
    import yaml
    name = request.json.get('name', '').strip()
    parent_path = request.json.get('parent_path', '')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Sanitize name (convert to slug)
    slug = name.lower().replace(' ', '-').replace('_', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')

    content_dir = Path(current_app.config['GARDEN_DIR'])
    parent_dir = content_dir / parent_path if parent_path else content_dir
    new_dir = parent_dir / slug

    if new_dir.exists():
        return jsonify({'error': f'Directory "{slug}" already exists'}), 400

    try:
        # Create directory
        new_dir.mkdir(parents=True, exist_ok=True)

        # Create config.yaml
        config = {
            'title': name,
            'description': '',
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'order': 999
        }
        config_path = new_dir / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Post-creation work (non-fatal)
    try:
        from trellis.utils.git_handler import GitHandler
        git = GitHandler(current_app.config.get('GITLAB_REPO_PATH', '.'))
        git.auto_commit(str(config_path), f"Created garden: {slug}")
    except Exception as e:
        print(f"Git commit failed for new garden {slug}: {e}")

    new_path = str(Path(parent_path) / slug) if parent_path else slug
    return jsonify({'success': True, 'path': new_path})

@editor_bp.route('/create/page', methods=['POST'])
@editor_required
def create_page():
    """Create a new complex page (.page directory with page.md)"""
    import frontmatter
    name = request.json.get('name', '').strip()
    parent_path = request.json.get('parent_path', '')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Sanitize name
    slug = name.lower().replace(' ', '-').replace('_', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')

    content_dir = Path(current_app.config['GARDEN_DIR'])
    parent_dir = content_dir / parent_path if parent_path else content_dir
    new_dir = parent_dir / f"{slug}.page"

    if new_dir.exists():
        return jsonify({'error': f'Page "{slug}" already exists'}), 400

    try:
        # Create .page directory
        new_dir.mkdir(parents=True, exist_ok=True)

        # Create page.md with frontmatter
        metadata = {
            'title': name,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'published_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'draft'
        }
        post = frontmatter.Post('# ' + name + '\n\nYour content here.', **metadata)

        page_md = new_dir / 'page.md'
        with open(page_md, 'w') as f:
            f.write(frontmatter.dumps(post))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    new_path = str(Path(parent_path) / f"{slug}.page") if parent_path else f"{slug}.page"

    # Post-creation work (non-fatal)
    try:
        from trellis.utils.git_handler import GitHandler
        git = GitHandler(current_app.config.get('GITLAB_REPO_PATH', '.'))
        git.auto_commit(str(page_md), f"Created page: {slug}")
    except Exception as e:
        print(f"Git commit failed for new page {slug}: {e}")

    try:
        from trellis.utils.index_manager import IndexManager
        path_parts = Path(new_path).parts
        garden_slug = path_parts[0] if len(path_parts) > 1 else None

        index_mgr = IndexManager(
            content_dir=current_app.config['GARDEN_DIR'],
            data_dir=current_app.config['DATA_DIR']
        )
        index_mgr.update_file(new_path, garden_slug)
    except Exception as e:
        print(f"Index update failed for new page {slug}: {e}")

    return jsonify({'success': True, 'path': new_path})

@editor_bp.route('/create/file', methods=['POST'])
@editor_required
def create_file():
    """Create a new text file"""
    import frontmatter
    name = request.json.get('name', '').strip()
    extension = request.json.get('extension', '.md').strip()
    parent_path = request.json.get('parent_path', '')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Ensure extension starts with dot
    if not extension.startswith('.'):
        extension = '.' + extension

    # Sanitize name
    filename = name if name.endswith(extension) else name + extension

    content_dir = Path(current_app.config['GARDEN_DIR'])
    parent_dir = content_dir / parent_path if parent_path else content_dir
    new_file = parent_dir / filename

    if new_file.exists():
        return jsonify({'error': f'File "{filename}" already exists'}), 400

    try:
        # Create file with appropriate content
        if extension == '.md':
            # Markdown with frontmatter
            metadata = {
                'title': name,
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'published_date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'draft'
            }
            post = frontmatter.Post(f'# {name}\n\nYour content here.', **metadata)
            content = frontmatter.dumps(post)
        elif extension in ['.yaml', '.yml']:
            # YAML template
            content = f"# {name}\n# Created: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        elif extension == '.py':
            # Python template
            content = f'"""\n{name}\n\nCreated: {datetime.now().strftime("%Y-%m-%d")}\n"""\n\n'
        else:
            # Generic text file
            content = f"# {name}\n# Created: {datetime.now().strftime('%Y-%m-%d')}\n\n"

        new_file.write_text(content)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    new_path = str(Path(parent_path) / filename) if parent_path else filename

    # Post-creation work (non-fatal)
    try:
        from trellis.utils.git_handler import GitHandler
        git = GitHandler(current_app.config.get('GITLAB_REPO_PATH', '.'))
        git.auto_commit(str(new_file), f"Created file: {filename}")
    except Exception as e:
        print(f"Git commit failed for new file {filename}: {e}")

    if extension == '.md':
        try:
            from trellis.utils.index_manager import IndexManager
            path_parts = Path(new_path).parts
            garden_slug = path_parts[0] if len(path_parts) > 1 else None

            index_mgr = IndexManager(
                content_dir=current_app.config['GARDEN_DIR'],
                data_dir=current_app.config['DATA_DIR']
            )
            index_mgr.update_file(new_path, garden_slug)
        except Exception as e:
            print(f"Index update failed for new file {filename}: {e}")

    return jsonify({'success': True, 'path': new_path})

@editor_bp.route('/edit-file/<path:file_path>')
@editor_required
def edit_file(file_path):
    """Edit any file (markdown, YAML, code, etc.)"""
    content_dir = Path(current_app.config['GARDEN_DIR'])
    full_path = content_dir / file_path

    # Security check
    try:
        full_path = full_path.resolve()
        if not str(full_path).startswith(str(content_dir.resolve())):
            return "Invalid path", 403
    except:
        return "Invalid path", 404

    if not full_path.exists():
        return "File not found", 404

    if not full_path.is_file():
        return "Path is not a file", 400

    # Read file content
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {e}", 500

    # Determine file type and editor mode
    extension = full_path.suffix
    editor_mode = {
        '.md': 'markdown',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.py': 'python',
        '.js': 'javascript',
        '.json': 'json',
        '.html': 'html',
        '.css': 'css',
        '.xml': 'xml',
        '.sh': 'shell',
    }.get(extension, 'text')

    # For markdown, parse frontmatter
    metadata = {}
    raw_content = content
    if extension == '.md':
        try:
            import frontmatter
            post = frontmatter.loads(content)
            metadata = post.metadata
            raw_content = post.content
        except:
            pass

    # Build breadcrumbs
    breadcrumbs = [{'name': 'Content', 'path': ''}]
    path_parts = Path(file_path).parts

    # Add directory breadcrumbs
    for i in range(len(path_parts) - 1):  # Exclude the filename
        path = '/'.join(path_parts[:i+1])
        breadcrumbs.append({'name': path_parts[i], 'path': path})

    # Add filename as current (non-clickable)
    breadcrumbs.append({'name': full_path.name, 'path': None})

    return render_template('editor_edit_file.html',
                          file_path=file_path,
                          filename=full_path.name,
                          content=content,
                          raw_content=raw_content,
                          metadata=metadata,
                          editor_mode=editor_mode,
                          is_markdown=extension == '.md',
                          breadcrumbs=breadcrumbs)

@editor_bp.route('/save-file', methods=['POST'])
@editor_required
def save_file():
    """Save any file type"""
    file_path = request.json.get('file_path', '')
    content = request.json.get('content', '')

    if not file_path:
        return jsonify({'error': 'File path is required'}), 400

    content_dir = Path(current_app.config['GARDEN_DIR'])
    full_path = content_dir / file_path

    # Security check
    try:
        full_path = full_path.resolve()
        if not str(full_path).startswith(str(content_dir.resolve())):
            return jsonify({'error': 'Invalid path'}), 403
    except:
        return jsonify({'error': 'Invalid path'}), 404

    try:
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Post-save work (non-fatal)
    try:
        from trellis.utils.git_handler import GitHandler
        git = GitHandler(current_app.config.get('GITLAB_REPO_PATH', '.'))
        git.auto_commit(str(full_path), f"Updated: {full_path.name}")
    except Exception as e:
        print(f"Git commit failed for {full_path.name}: {e}")

    if full_path.suffix == '.md':
        try:
            from trellis.utils.index_manager import IndexManager
            path_parts = Path(file_path).parts
            garden_slug = path_parts[0] if len(path_parts) > 1 else None

            index_mgr = IndexManager(
                content_dir=current_app.config['GARDEN_DIR'],
                data_dir=current_app.config['DATA_DIR']
            )
            index_mgr.update_file(file_path, garden_slug)
        except Exception as e:
            print(f"Index update failed for {full_path.name}: {e}")

    return jsonify({'success': True})

