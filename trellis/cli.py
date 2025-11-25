#!/usr/bin/env python3
"""
Trellis CLI Commands

Command-line utilities for Trellis sites.
"""
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def index_content():
    """CLI entry point for trellis-index command."""
    from trellis.models.content_index import ContentIndex
    from trellis.utils.markdown_handler import MarkdownHandler

    parser = argparse.ArgumentParser(description='Trellis Content Indexer')
    parser.add_argument('--clear', action='store_true',
                        help='Clear existing index before rebuilding')
    parser.add_argument('--stats', action='store_true',
                        help='Show index statistics')
    parser.add_argument('--data-dir', type=str,
                        help='Data directory (default: from DATA_DIR env)')
    parser.add_argument('--content-dir', type=str,
                        help='Content directory (default: from CONTENT_DIR env)')
    args = parser.parse_args()

    # Get paths from args or environment
    data_dir = args.data_dir or os.environ.get('DATA_DIR', '')
    content_dir = args.content_dir or os.environ.get('CONTENT_DIR', '')

    if not data_dir:
        print("Error: DATA_DIR not set. Use --data-dir or set DATA_DIR environment variable.")
        return 1

    if not content_dir:
        content_dir = os.path.join(data_dir, 'content')

    if args.stats:
        _show_stats(data_dir)
    else:
        _index_all_content(data_dir, content_dir, clear=args.clear)

    return 0


def _index_directory(content_index, base_content_dir, current_dir, garden_slug, url_prefix=''):
    """Recursively index a directory."""
    from trellis.utils.markdown_handler import MarkdownHandler

    indexed_count = 0
    handler = MarkdownHandler(current_dir)

    for item in sorted(current_dir.iterdir()):
        if item.name.startswith('.') or item.name in ['config.yaml', 'config.yml']:
            continue

        try:
            if item.is_file() and item.suffix == '.md':
                article = handler.parse_file(item.name)
                slug = handler.generate_slug(item.name)
                url = f"/garden/{garden_slug}/{url_prefix}{slug}" if url_prefix else f"/garden/{garden_slug}/{slug}"
                source_file = str(item.relative_to(base_content_dir))

                content_index.upsert_page(
                    url=url,
                    source_file=source_file,
                    metadata=article['metadata'],
                    content_dir=base_content_dir
                )
                indexed_count += 1
                print(f"  Indexed: {url}")

            elif item.is_dir() and item.suffix == '.page':
                page_md = item / 'page.md'
                if page_md.exists():
                    article = handler.parse_file(item.name)
                    slug = handler.generate_slug(item.name)
                    url = f"/garden/{garden_slug}/{url_prefix}{slug}" if url_prefix else f"/garden/{garden_slug}/{slug}"
                    source_file = str(item.relative_to(base_content_dir))

                    content_index.upsert_page(
                        url=url,
                        source_file=source_file,
                        metadata=article['metadata'],
                        content_dir=base_content_dir
                    )
                    indexed_count += 1
                    print(f"  Indexed: {url}")

            elif item.is_dir():
                new_prefix = f"{url_prefix}{item.name}/" if url_prefix else f"{item.name}/"
                indexed_count += _index_directory(
                    content_index,
                    base_content_dir,
                    item,
                    garden_slug,
                    new_prefix
                )

        except Exception as e:
            print(f"  Error indexing {item}: {e}")

    return indexed_count


def _index_all_content(data_dir, content_dir, clear=False):
    """Index all content in the content directory."""
    from trellis.models.content_index import ContentIndex

    content_index = ContentIndex(data_dir)
    content_path = Path(content_dir)

    if clear:
        print("Clearing existing index...")
        content_index.clear_index()

    print(f"Indexing content from: {content_path}")
    print(f"Database location: {content_index.db_path}")
    print()

    total_indexed = 0

    for garden_dir in sorted(content_path.iterdir()):
        if garden_dir.is_dir() and not garden_dir.name.startswith('.'):
            print(f"Garden: {garden_dir.name}")
            indexed = _index_directory(
                content_index,
                content_path,
                garden_dir,
                garden_dir.name
            )
            total_indexed += indexed
            print(f"  Subtotal: {indexed} pages")
            print()

    print(f"Total indexed: {total_indexed} pages")
    return total_indexed


def _show_stats(data_dir):
    """Show index statistics."""
    from trellis.models.content_index import ContentIndex

    content_index = ContentIndex(data_dir)

    print(f"Database: {content_index.db_path}")
    print(f"Total pages: {content_index.get_page_count()}")
    print()

    print("Recent updates:")
    for page in content_index.get_recent_pages(10):
        print(f"  {page['updated_date']} - {page['title'] or page['url']}")


def init_db():
    """CLI entry point for trellis-init-db command."""
    from trellis import create_app
    from trellis.models import db, User

    parser = argparse.ArgumentParser(description='Initialize Trellis database')
    parser.add_argument('--admin-password', type=str, default='admin',
                        help='Password for default admin user (default: admin)')
    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        admin = User.get_by_username('admin')

        if admin:
            print("Admin user already exists")
        else:
            print("Creating default admin user...")
            admin = User(username='admin', role='admin')
            admin.set_password(args.admin_password)

            db.session.add(admin)
            db.session.commit()

            print("Admin user created successfully")
            print("  Username: admin")
            print(f"  Password: {args.admin_password}")
            print("  Role: admin")
            if args.admin_password == 'admin':
                print("\n  IMPORTANT: Change the default password after first login!")

        print("\nDatabase initialization complete")

    return 0


def rebuild_search():
    """CLI entry point for trellis-search command."""
    from trellis.utils.search_index import SearchIndex

    parser = argparse.ArgumentParser(description='Trellis Search Index Manager')
    parser.add_argument('--rebuild', action='store_true',
                        help='Rebuild the search index from scratch')
    parser.add_argument('--stats', action='store_true',
                        help='Show search index statistics')
    parser.add_argument('--data-dir', type=str,
                        help='Data directory (default: from DATA_DIR env)')
    parser.add_argument('--content-dir', type=str,
                        help='Content directory (default: from CONTENT_DIR env)')
    args = parser.parse_args()

    # Get paths from args or environment
    data_dir = args.data_dir or os.environ.get('DATA_DIR', '')
    content_dir = args.content_dir or os.environ.get('CONTENT_DIR', '')

    if not data_dir:
        print("Error: DATA_DIR not set. Use --data-dir or set DATA_DIR environment variable.")
        return 1

    if not content_dir:
        content_dir = os.path.join(data_dir, 'content')

    search_index = SearchIndex(data_dir)

    if args.stats:
        print(f"Search index: {search_index.index_dir}")
        print(f"Documents indexed: {search_index.get_document_count()}")
        return 0

    if args.rebuild:
        print(f"Rebuilding search index from: {content_dir}")
        print(f"Index location: {search_index.index_dir}")
        print()

        try:
            count = search_index.rebuild_index(content_dir)
            print(f"\nSuccessfully indexed {count} documents")
        except Exception as e:
            print(f"Error rebuilding search index: {e}")
            return 1
    else:
        print("Use --rebuild to rebuild the search index")
        print("Use --stats to show index statistics")

    return 0


if __name__ == '__main__':
    index_content()
