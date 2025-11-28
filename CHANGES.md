# Chore App Update Summary

## What Changed

The application has been completely restructured to implement a **chore template system** with daily submission limits.

### Old System vs New System

#### OLD (Free-form chores):
- Child could enter any chore description and amount
- No limits on what or how many chores could be submitted
- Parent had to verify each custom entry

#### NEW (Template-based chores):
- Parent defines **Chore Types** (templates) with:
  - Fixed name, description, and value
  - Daily submission limits per day of week (S/M/T/W/Th/F/S)
  - Active/inactive status
- Child selects from available chores and submits completions
- System automatically enforces daily limits
- "Pending approval" earnings shown separately from approved balance

## New Features

### For Parents:
1. **Chore Type Management Page** (`/parent/chore_types`)
   - Create new chore types with all parameters
   - Edit existing chore types
   - Activate/deactivate chores
   - Set different daily limits for each day of week

2. **Enhanced Dashboard**
   - View pending submissions (not just chores)
   - See which specific chore types were completed
   - View child's notes on submissions

### For Children:
1. **Chore Selection Interface**
   - Dropdown menu of available chores
   - Shows value and remaining daily submissions
   - Disabled options when daily limit reached

2. **Available Chores Table**
   - See all active chore types
   - Value for each chore
   - Days available (with day abbreviations)
   - Current availability status

3. **Improved Balance Display**
   - Pending approval amount shown separately
   - Clear breakdown of earnings, fines, and balance

## Database Changes

### New Tables:
- `ChoreType` - Parent-defined chore templates
- `ChoreSubmission` - Child's submissions of chore types

### Removed Tables:
- `Chore` (old free-form chores)

### Relationships:
```
User (child) -> ChoreSubmission -> ChoreType
                      ↓
                 Transaction (when approved)
```

## Daily Limit System

### How It Works:
1. Parent sets limit for each day (0-99)
   - 0 = disabled/unlimited (context dependent)
   - 1+ = max submissions per day
2. System counts submissions for current date
3. Child can only submit if under limit
4. Limits reset at midnight (server time)

### Example Use Cases:
- **Take Out Trash**: Sun=1, Wed=1 (only those days)
- **Load Dishwasher**: All days=2 (twice daily max)
- **Clean Room**: All days=1 (once per day)
- **Yard Work**: Sat=1 (weekends only)

## File Changes

### Modified:
- `main.py` - Complete rewrite of models and routes
- `templates/child_dashboard.html` - New chore submission interface
- `templates/parent_dashboard.html` - Updated for submissions
- `setup.py` - Creates sample chore types
- `README.md` - Updated documentation

### Added:
- `templates/manage_chore_types.html` - Chore type management UI

## Sample Data

The setup script now creates 5 sample chore types:
1. Clean Your Room - $5.00 (daily)
2. Take Out Trash - $2.00 (Sun, Wed only)
3. Load Dishwasher - $3.00 (twice per day)
4. Wash Car - $10.00 (weekends only)
5. Yard Work - $15.00 (Saturdays only)

## Running the Updated App

```bash
# Reinitialize database (drops old data!)
python setup.py

# Start server
python main.py
```

Login credentials unchanged:
- Parent: `parent` / `parent123`
- Child: `child` / `child123`

## Key Benefits

1. **Consistency** - All chores have standardized names and values
2. **Control** - Parents set exactly what chores are available and when
3. **Automation** - System prevents over-submission automatically
4. **Clarity** - Child knows exactly what they can do and earn
5. **Flexibility** - Different limits per day accommodate real schedules
