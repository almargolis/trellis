"""
Trellis Models

Trellis uses the canonical db and User model from qdflask.models to ensure
all Flask modules share the same database instance.

Note: qdflask owns the User model and authentication. Trellis imports and uses it.
"""

from qdflask.models import db, User

__all__ = ['db', 'User']
