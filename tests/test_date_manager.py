"""Tests for trellis.utils.date_manager.

All tests use tmp_path fixtures so production content is never touched.
"""

from datetime import datetime

import pytest

from trellis.utils.date_manager import DateManager


# ===================================================================
# parse_dates
# ===================================================================

class TestParseDates:

    def test_all_dates_present(self):
        metadata = {
            'created_date': '2024-01-01',
            'published_date': '2024-06-01',
            'updated_date': '2024-09-01',
        }
        result = DateManager.parse_dates(metadata)
        assert result['created'] == '2024-01-01'
        assert result['published'] == '2024-06-01'
        assert result['updated'] == '2024-09-01'

    def test_missing_dates_are_none(self):
        result = DateManager.parse_dates({})
        assert result['created'] is None
        assert result['published'] is None
        assert result['updated'] is None

    def test_partial_dates(self):
        metadata = {'published_date': '2024-06-01'}
        result = DateManager.parse_dates(metadata)
        assert result['created'] is None
        assert result['published'] == '2024-06-01'
        assert result['updated'] is None


# ===================================================================
# update_date
# ===================================================================

class TestUpdateDate:

    def test_update_created(self):
        metadata = {}
        DateManager.update_date(metadata, 'created', '2024-01-01')
        assert metadata['created_date'] == '2024-01-01'

    def test_update_published(self):
        metadata = {}
        DateManager.update_date(metadata, 'published', '2024-06-01')
        assert metadata['published_date'] == '2024-06-01'

    def test_update_updated(self):
        metadata = {}
        DateManager.update_date(metadata, 'updated', '2024-09-01')
        assert metadata['updated_date'] == '2024-09-01'

    def test_defaults_to_today(self):
        metadata = {}
        DateManager.update_date(metadata, 'updated')
        today = datetime.now().strftime('%Y-%m-%d')
        assert metadata['updated_date'] == today

    def test_returns_metadata(self):
        metadata = {'title': 'Test'}
        result = DateManager.update_date(metadata, 'created', '2024-01-01')
        assert result is metadata
        assert result['title'] == 'Test'


# ===================================================================
# auto_update_modified
# ===================================================================

class TestAutoUpdateModified:

    def test_sets_updated_date(self):
        metadata = {}
        DateManager.auto_update_modified(metadata)
        today = datetime.now().strftime('%Y-%m-%d')
        assert metadata['updated_date'] == today

    def test_overwrites_existing(self):
        metadata = {'updated_date': '2020-01-01'}
        DateManager.auto_update_modified(metadata)
        today = datetime.now().strftime('%Y-%m-%d')
        assert metadata['updated_date'] == today

    def test_returns_metadata(self):
        metadata = {'title': 'Keep'}
        result = DateManager.auto_update_modified(metadata)
        assert result is metadata
        assert result['title'] == 'Keep'


# ===================================================================
# validate_dates
# ===================================================================

class TestValidateDates:

    def test_valid_order(self):
        assert DateManager.validate_dates(
            '2024-01-01', '2024-06-01', '2024-09-01') is True

    def test_invalid_order(self):
        assert DateManager.validate_dates(
            '2024-09-01', '2024-06-01', '2024-01-01') is False

    def test_equal_dates_valid(self):
        assert DateManager.validate_dates(
            '2024-01-01', '2024-01-01', '2024-01-01') is True

    def test_single_date_valid(self):
        assert DateManager.validate_dates('2024-01-01', None, None) is True

    def test_no_dates_valid(self):
        assert DateManager.validate_dates(None, None, None) is True

    def test_two_dates_valid(self):
        assert DateManager.validate_dates(
            '2024-01-01', None, '2024-06-01') is True

    def test_two_dates_invalid(self):
        assert DateManager.validate_dates(
            '2024-06-01', None, '2024-01-01') is False


# ===================================================================
# get_file_dates
# ===================================================================

class TestGetFileDates:

    def test_returns_dates(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_text('hello')
        result = DateManager.get_file_dates(f)
        assert 'created' in result
        assert 'modified' in result
        assert isinstance(result['created'], datetime)
        assert isinstance(result['modified'], datetime)
