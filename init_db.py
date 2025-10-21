#!/usr/bin/env python3
"""
Database initialization script
Creates the database and adds a default admin user
"""

from app import create_app
from app.models import db, User

def init_database():
    """Initialize the database with tables and default admin user"""
    app = create_app()

    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()

        # Check if admin user exists
        admin = User.get_by_username('admin')

        if admin:
            print("Admin user already exists")
        else:
            # Create default admin user
            print("Creating default admin user...")
            admin = User(username='admin', role='admin')
            admin.set_password('admin')

            db.session.add(admin)
            db.session.commit()

            print("✓ Admin user created successfully")
            print("  Username: admin")
            print("  Password: admin")
            print("  Role: admin")
            print("\n⚠️  IMPORTANT: Change the default password after first login!")

        print("\n✓ Database initialization complete")

if __name__ == '__main__':
    init_database()
