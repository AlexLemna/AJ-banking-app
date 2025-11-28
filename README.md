# Chore & Allowance Tracker

A Flask web application for managing chores and allowances between parents and children with built-in daily submission limits.

## Features

### Child Account Features
- **Browse Available Chores**: See all chores defined by parent with values and availability
- **Submit Chore Completions**: Report completed chores from the available list
- **Daily Limits**: System automatically enforces daily submission limits per chore type
- **Track Earnings**: View pending (awaiting approval) and approved earnings separately
- **See Balance**: View current balance after approved earnings, fines, and payments
- **Submission History**: See all submitted chores and their approval status

### Parent Account Features
- **Define Chore Types**: Create chore templates with:
  - Chore name and description
  - Fixed monetary value
  - Daily submission limits for each day of the week (S/M/T/W/Th/F/S)
  - Active/inactive status
- **Approve Submissions**: Review and approve child's chore submissions
- **Levy Fines**: Add fines with descriptions for various offenses
- **Record Payments**: Log payments made to the child
- **View Balance**: See how much is currently owed to the child
- **Transaction History**: Complete history of all chores, fines, and payments
- **Manage Chore Types**: Edit, activate, or deactivate chore types as needed

### Smart Daily Limits
- Parents set how many times each chore can be submitted per day
- Different limits for each day of the week (e.g., "Take Out Trash" only on Sundays and Wednesdays)
- Set to 0 to make unlimited or disable for that day
- System automatically blocks children from over-submitting
- Child dashboard shows remaining submissions available for each chore

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
   - Sample chore types (Clean Room, Take Out Trash, Load Dishwasher, Wash Car, Yard Work)

   **⚠️ Important**: Change these passwords after first login!

## Running the Application

Start the Flask development server:

```bash
python main.py
```

The application will be available at `http://127.0.0.1:5000`

Or use the quick start script:
```bash
./start.sh
```

## Usage

### First Time Setup

1. Run `python setup.py` to initialize the database with sample data
2. Start the application with `python main.py`
3. Open your browser to `http://127.0.0.1:5000`
4. Log in with the default credentials

### As a Parent

1. Log in with parent account credentials
2. **Manage Chore Types** (from dashboard or via menu):
   - Create new chore types with name, description, and value
   - Set daily limits for each day of the week
   - Edit existing chore types
   - Activate/deactivate chores as needed
3. **Review Pending Submissions**: Approve chores submitted by child
4. **Add Fines**: Record fines if necessary
5. **Record Payments**: Log payments when you pay the child
6. View complete transaction history

### As a Child

1. Log in with child account credentials
2. **Browse Available Chores**: See what chores you can do and how much they're worth
3. **Check Daily Limits**: See which chores are still available today
4. **Submit Chores**: Select a chore from the dropdown and submit it for approval
5. **Track Your Earnings**:
   - Pending approval (waiting for parent)
   - Approved earnings
   - Current balance (after fines and payments)

### Example Daily Limit Setup

When creating a chore, you can set different limits for different days:

- **Take Out Trash**: Sun=1, Wed=1 (can do once on Sunday and once on Wednesday)
- **Load Dishwasher**: All days=2 (can do twice per day, any day)
- **Clean Room**: All days=1 (once per day maximum)
- **Yard Work**: Sat=1 (only available on Saturdays)
- **Homework Help Sibling**: All days=0 (unlimited - can do as many times as needed)

Setting a day to 0 means either unlimited submissions (if other days have limits) or the chore is not available that day.

## Database Schema

The application uses SQLite with four main tables:

- **User**: Stores account information (username, password_hash, role)
- **ChoreType**: Parent-defined chore templates with daily limits
- **ChoreSubmission**: Child's submitted chore instances awaiting/approved
- **Transaction**: Records all financial transactions (approved chores, fines, payments)

## Security Notes

- Passwords are hashed using Werkzeug's security functions
- Role-based access control prevents children from accessing parent features
- Login required for all dashboard pages
- Session management handled by Flask-Login
- Daily submission limits enforced server-side

## Customization

### Changing Default Credentials

Edit `setup.py` to change the default usernames and passwords before running it.

### Modifying Sample Chores

Edit the `sample_chores` list in `setup.py` to customize the initial chore types.

### Adding More Children

The app currently supports one parent and one child. To support multiple children, you would need to:
- Modify the parent dashboard to select which child to view
- Update queries to filter by selected child
- Add child selection UI

### Styling

All CSS is embedded in `templates/base.html`. Modify the `<style>` section to customize the appearance.

## Project Structure

```
AJ banking app/
├── main.py              # Main Flask application with all models and routes
├── setup.py             # Database initialization script
├── start.sh             # Quick start script
├── pyproject.toml       # Project dependencies
├── README.md            # This file
├── instance/
│   └── chores.db        # SQLite database (created after setup)
└── templates/           # HTML templates
    ├── base.html                # Base template with styling
    ├── login.html               # Login page
    ├── child_dashboard.html     # Child dashboard
    ├── parent_dashboard.html    # Parent dashboard
    └── manage_chore_types.html  # Chore type management
```

## Troubleshooting

### Database Issues

If you encounter database errors, run `python setup.py` again to drop and recreate all tables.

### Port Already in Use

If port 5000 is in use, modify the last line in `main.py` to use a different port:
```python
app.run(debug=True, port=5001)
```

### Daily Limits Not Working

The system uses the date from the server. Make sure your system clock is set correctly. Daily limits reset at midnight according to the server's timezone.

## Future Enhancements

Potential features to add:
- Password change functionality
- Support for multiple children
- Recurring/scheduled chores
- Chore categories and filtering
- Weekly/monthly earning goals
- Export transaction history to CSV
- Email/push notifications for pending approvals
- Mobile app version
- Photo uploads for chore completion proof
