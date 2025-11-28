# Chore & Allowance Tracker

A Flask web application for managing chores and allowances between parents and children.

## Features

### Child Account Features
- **Record Chores**: Log completed chores with description and amount
- **View Earnings**: See pending (unapproved) and approved earnings
- **Track Balance**: View current balance after fines and payments
- **Transaction History**: See all chores submitted

### Parent Account Features
- **Approve Chores**: Review and approve child's submitted chores
- **Levy Fines**: Add fines with descriptions for various offenses
- **Record Payments**: Log payments made to the child
- **View Balance**: See how much is currently owed to the child
- **Transaction History**: Complete history of all chores, fines, and payments
- **Dashboard Overview**: Quick stats on current balance and total payments

## Installation

1. **Install dependencies** (if not already installed):
   ```bash
   uv sync
   ```

2. **Initialize the database**:
   ```bash
   python setup.py
   ```

   This will create:
   - Parent account (username: `parent`, password: `parent123`)
   - Child account (username: `child`, password: `child123`)

   **⚠️ Important**: Change these passwords after first login!

## Running the Application

Start the Flask development server:

```bash
python main.py
```

The application will be available at `http://127.0.0.1:5000`

## Usage

### First Time Setup

1. Run `python setup.py` to initialize the database
2. Start the application with `python main.py`
3. Open your browser to `http://127.0.0.1:5000`
4. Log in with the default credentials

### As a Child

1. Log in with child account credentials
2. Add completed chores with description and amount
3. View pending chores (waiting for parent approval)
4. See your current balance and earnings

### As a Parent

1. Log in with parent account credentials
2. Review and approve pending chores
3. Add fines if necessary
4. Record payments when you pay the child
5. View complete transaction history
6. Monitor the current balance owed

## Database Schema

The application uses SQLite with three main tables:

- **User**: Stores account information (username, password_hash, role)
- **Chore**: Tracks chores (description, amount, status, dates)
- **Transaction**: Records all financial transactions (chores, fines, payments)

## Security Notes

- Passwords are hashed using Werkzeug's security functions
- Role-based access control prevents children from accessing parent features
- Login required for all dashboard pages
- Session management handled by Flask-Login

## Customization

### Changing Default Credentials

Edit `setup.py` to change the default usernames and passwords before running it.

### Adding More Children

You can modify the database models and application logic to support multiple children. Currently, the app is designed for one parent and one child.

### Styling

All CSS is embedded in `templates/base.html`. Modify the `<style>` section to customize the appearance.

## Project Structure

```
AJ banking app/
├── main.py              # Main Flask application
├── setup.py             # Database initialization script
├── pyproject.toml       # Project dependencies
├── README.md            # This file
├── chores.db            # SQLite database (created after setup)
└── templates/           # HTML templates
    ├── base.html        # Base template with styling
    ├── login.html       # Login page
    ├── child_dashboard.html   # Child dashboard
    └── parent_dashboard.html  # Parent dashboard
```

## Troubleshooting

### Database Issues

If you encounter database errors, try deleting `chores.db` and running `python setup.py` again.

### Port Already in Use

If port 5000 is in use, modify the last line in `main.py` to use a different port:
```python
app.run(debug=True, port=5001)
```

## Future Enhancements

Potential features to add:
- Password change functionality
- Support for multiple children
- Recurring chores
- Chore categories
- Export transaction history to CSV
- Email notifications
- Mobile-responsive design improvements
