#!/usr/bin/env python3
"""
Setup script to initialize the database with parent and child accounts.
Run this script once to set up your accounts.
"""

from main import app, db, User

def init_database():
    """Initialize the database with parent and child accounts."""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if users already exist
        if User.query.first():
            print("Database already contains users. Skipping initialization.")
            print("\nExisting users:")
            for user in User.query.all():
                print(f"  - {user.username} ({user.role})")
            return
        
        # Create parent account
        parent = User(username='parent', role='parent')
        parent.set_password('parent123')  # Change this password!
        db.session.add(parent)
        
        # Create child account
        child = User(username='child', role='child')
        child.set_password('child123')  # Change this password!
        db.session.add(child)
        
        # Commit changes
        db.session.commit()
        
        print("Database initialized successfully!")
        print("\nDefault accounts created:")
        print("  Parent account:")
        print("    Username: parent")
        print("    Password: parent123")
        print("\n  Child account:")
        print("    Username: child")
        print("    Password: child123")
        print("\n⚠️  IMPORTANT: Change these passwords after first login!")
        print("\nYou can now run the app with: python main.py")

if __name__ == '__main__':
    init_database()
