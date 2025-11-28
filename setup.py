#!/usr/bin/env python3
"""
Setup script to initialize the database with parent and child accounts.
Run this script once to set up your accounts.
"""

from main import app, db, User, ChoreType

def init_database():
    """Initialize the database with parent and child accounts."""
    with app.app_context():
        # Drop all tables and recreate (for fresh start)
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Create parent account
        parent = User(username='parent', role='parent')
        parent.set_password('parent123')  # Change this password!
        db.session.add(parent)
        
        # Create child account
        child = User(username='child', role='child')
        child.set_password('child123')  # Change this password!
        db.session.add(child)
        
        # Create some sample chore types
        sample_chores = [
            {
                'name': 'Clean Your Room',
                'description': 'Vacuum, make bed, organize desk, and put away clothes',
                'value': 5.00,
                'sunday': 1, 'monday': 1, 'tuesday': 1, 'wednesday': 1,
                'thursday': 1, 'friday': 1, 'saturday': 1
            },
            {
                'name': 'Take Out Trash',
                'description': 'Empty all trash cans and take bins to curb',
                'value': 2.00,
                'sunday': 1, 'monday': 0, 'tuesday': 0, 'wednesday': 1,
                'thursday': 0, 'friday': 0, 'saturday': 0
            },
            {
                'name': 'Load Dishwasher',
                'description': 'Load dirty dishes and run dishwasher',
                'value': 3.00,
                'sunday': 2, 'monday': 2, 'tuesday': 2, 'wednesday': 2,
                'thursday': 2, 'friday': 2, 'saturday': 2
            },
            {
                'name': 'Wash Car',
                'description': 'Wash and vacuum the family car',
                'value': 10.00,
                'sunday': 1, 'monday': 0, 'tuesday': 0, 'wednesday': 0,
                'thursday': 0, 'friday': 0, 'saturday': 1
            },
            {
                'name': 'Yard Work',
                'description': 'Mow lawn, rake leaves, or pull weeds',
                'value': 15.00,
                'sunday': 0, 'monday': 0, 'tuesday': 0, 'wednesday': 0,
                'thursday': 0, 'friday': 0, 'saturday': 1
            }
        ]
        
        for chore_data in sample_chores:
            chore = ChoreType(
                name=chore_data['name'],
                description=chore_data['description'],
                value=chore_data['value'],
                sunday_limit=chore_data['sunday'],
                monday_limit=chore_data['monday'],
                tuesday_limit=chore_data['tuesday'],
                wednesday_limit=chore_data['wednesday'],
                thursday_limit=chore_data['thursday'],
                friday_limit=chore_data['friday'],
                saturday_limit=chore_data['saturday']
            )
            db.session.add(chore)
        
        # Commit changes
        db.session.commit()
        
        print("\n" + "="*60)
        print("Database initialized successfully!")
        print("="*60)
        print("\nDefault accounts created:")
        print("  Parent account:")
        print("    Username: parent")
        print("    Password: parent123")
        print("\n  Child account:")
        print("    Username: child")
        print("    Password: child123")
        print("\n" + "="*60)
        print("Sample chore types created:")
        for chore_data in sample_chores:
            print(f"  • {chore_data['name']} - ${chore_data['value']:.2f}")
        print("="*60)
        print("\n⚠️  IMPORTANT: Change these passwords after first login!")
        print("\nYou can now run the app with: python main.py")

if __name__ == '__main__':
    init_database()
