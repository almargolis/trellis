# ============================================================================
# File: migrate_content.py - Content Migration Script
# Run this to migrate Hugo content to Flask with intelligent date handling
# ============================================================================

import os
import shutil
import frontmatter
from pathlib import Path
from datetime import datetime
import yaml

class ContentMigrator:
    def __init__(self, hugo_dir, flask_dir):
        self.hugo_content = Path(hugo_dir) / 'content'
        self.flask_content = Path(flask_dir) / 'content'
        self.flask_content.mkdir(parents=True, exist_ok=True)
        self.migration_report = []
    
    def get_file_dates(self, filepath):
        """Get filesystem creation and modification dates"""
        stat = os.stat(filepath)
        return {
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime)
        }
    
    def parse_hugo_date(self, date_value):
        """Parse various date formats from Hugo"""
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            # Try common date formats
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
        
        return None
    
    def migrate_file(self, md_file):
        """Migrate a single markdown file with intelligent date mapping"""
        try:
            # Read the Hugo markdown file
            with open(md_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            
            # Get filesystem dates
            file_dates = self.get_file_dates(md_file)
            
            # Extract existing date from frontmatter
            hugo_date = None
            for date_field in ['date', 'publishDate', 'created', 'published']:
                if date_field in post.metadata:
                    hugo_date = self.parse_hugo_date(post.metadata[date_field])
                    if hugo_date:
                        break
            
            # Intelligent date mapping
            if hugo_date:
                # Use Hugo's date as the base
                created_date = hugo_date
                published_date = hugo_date
                updated_date = file_dates['modified']
            else:
                # Fall back to filesystem dates
                created_date = file_dates['created']
                published_date = file_dates['created']
                updated_date = file_dates['modified']
            
            # Format dates consistently
            new_metadata = {
                'title': post.metadata.get('title', md_file.stem),
                'created_date': created_date.strftime('%Y-%m-%d'),
                'published_date': published_date.strftime('%Y-%m-%d'),
                'updated_date': updated_date.strftime('%Y-%m-%d'),
            }
            
            # Preserve other metadata
            for key in ['tags', 'categories', 'description', 'draft']:
                if key in post.metadata:
                    new_metadata[key] = post.metadata[key]
            
            # Create new post with updated metadata
            new_post = frontmatter.Post(post.content, **new_metadata)
            
            # Determine output path (preserve directory structure)
            rel_path = md_file.relative_to(self.hugo_content)
            output_file = self.flask_content / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the migrated file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(new_post))
            
            # Add to migration report
            self.migration_report.append({
                'file': str(rel_path),
                'old_date': hugo_date.strftime('%Y-%m-%d') if hugo_date else 'N/A',
                'created': new_metadata['created_date'],
                'published': new_metadata['published_date'],
                'updated': new_metadata['updated_date']
            })
            
            return True
            
        except Exception as e:
            print(f"Error migrating {md_file}: {e}")
            return False
    
    def migrate_all(self):
        """Migrate all markdown files"""
        print("Starting content migration...\n")
        
        # Find all markdown files
        md_files = list(self.hugo_content.rglob('*.md'))
        
        if not md_files:
            print(f"No markdown files found in {self.hugo_content}")
            return
        
        print(f"Found {len(md_files)} markdown files")
        
        success_count = 0
        for md_file in md_files:
            print(f"Migrating: {md_file.name}...", end=' ')
            if self.migrate_file(md_file):
                print("✓")
                success_count += 1
            else:
                print("✗")
        
        print(f"\nMigration complete: {success_count}/{len(md_files)} files migrated")
        
        # Generate migration report
        self.generate_report()
    
    def generate_report(self):
        """Generate a detailed migration report"""
        report_file = Path('/Users/almargolis/projects/tmih_flask') / 'migration_report.txt'
        
        with open(report_file, 'w') as f:
            f.write("Content Migration Report\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Files Migrated: {len(self.migration_report)}\n\n")
            
            f.write("Date Mapping Details:\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'File':<40} {'Old Date':<12} {'Created':<12} {'Published':<12} {'Updated':<12}\n")
            f.write("-" * 80 + "\n")
            
            for entry in self.migration_report:
                f.write(f"{entry['file']:<40} {entry['old_date']:<12} "
                       f"{entry['created']:<12} {entry['published']:<12} {entry['updated']:<12}\n")
        
        print(f"\n✓ Migration report saved to: {report_file}")

def main():
    print("=== Hugo to Flask Content Migration ===\n")
    
    hugo_dir = Path('/Users/almargolis/projects/tmih_hugo')
    flask_dir = Path('/Users/almargolis/projects/tmih_flask')
    
    if not hugo_dir.exists():
        print(f"Error: Hugo directory not found at {hugo_dir}")
        return
    
    if not flask_dir.exists():
        print(f"Error: Flask directory not found at {flask_dir}")
        print("Please run setup.py first!")
        return
    
    migrator = ContentMigrator(hugo_dir, flask_dir)
    migrator.migrate_all()
    
    print("\nNext steps:")
    print("1. Review the migration_report.txt")
    print("2. Check a few migrated files in content/ to verify dates")
    print("3. Copy static assets (images, etc.) from Hugo to Flask")
    print("4. Extract logo colors and update colors.css")

if __name__ == '__main__':
    main()

