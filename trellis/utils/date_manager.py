from datetime import datetime
import os

class DateManager:
    @staticmethod
    def parse_dates(metadata):
        """Parse dates from frontmatter"""
        return {
            'created': metadata.get('created_date'),
            'published': metadata.get('published_date'),
            'updated': metadata.get('updated_date')
        }

    @staticmethod
    def update_date(metadata, date_type, new_date=None):
        """Update specific date in metadata"""
        if new_date is None:
            new_date = datetime.now().strftime('%Y-%m-%d')

        field_map = {
            'created': 'created_date',
            'published': 'published_date',
            'updated': 'updated_date'
        }

        metadata[field_map[date_type]] = new_date
        return metadata

    @staticmethod
    def auto_update_modified(metadata):
        """Automatically update modified date"""
        metadata['updated_date'] = datetime.now().strftime('%Y-%m-%d')
        return metadata

    @staticmethod
    def validate_dates(created, published, updated):
        """Ensure dates are in logical order"""
        dates = []
        for d in [created, published, updated]:
            if d:
                dates.append(datetime.strptime(str(d), '%Y-%m-%d'))

        if len(dates) >= 2:
            return dates == sorted(dates)
        return True

    @staticmethod
    def get_file_dates(filepath):
        """Get filesystem dates"""
        stat = os.stat(filepath)
        return {
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime)
        }
