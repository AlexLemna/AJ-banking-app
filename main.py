# ============================================================================
# IMPORTS - External libraries we need for this application
# ============================================================================

# Built-in Python datetime tools for working with dates and times
from datetime import date, datetime

# functools.wraps is used when creating decorator functions to preserve metadata
from functools import wraps

# Type hints for better code editor support (not required for the app to run)
from typing import TYPE_CHECKING, Optional

# Flask is a "web framework" - it handles HTTP requests, routing URLs to functions,
# and rendering HTML templates. Think of it as the foundation that lets us build a website.
from flask import Flask, flash, redirect, render_template, request, url_for

# Flask-Login handles user authentication (login/logout) and sessions.
# It remembers who is logged in and provides decorators to protect pages.
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)

# SQLAlchemy is an "ORM" (Object-Relational Mapper). It lets us work with database
# tables as if they were Python objects/classes. Instead of writing SQL queries,
# we can just say things like User.query.filter_by(username='bob').first()
from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy's func lets us use SQL functions like COUNT, DATE, etc. in our queries
from sqlalchemy import func

# Security functions for password hashing. We never store passwords in plain text!
# generate_password_hash() converts "password123" -> random scrambled string
# check_password_hash() can verify if a password matches the hash without storing the actual password
from werkzeug.security import check_password_hash, generate_password_hash

# TYPE_CHECKING is always False at runtime, but True when type checkers analyze code
# This lets us import things only for type hints without affecting runtime
if TYPE_CHECKING:
    from typing import ClassVar


# ============================================================================
# FLASK APP SETUP
# ============================================================================

# Create the Flask application instance. __name__ tells Flask where to find templates/static files
app = Flask(__name__)

# Configuration settings for our Flask app
# SECRET_KEY: Used to encrypt session cookies and flash messages. Must be random and secret in production!
app.config["SECRET_KEY"] = "your-secret-key-change-this-in-production"

# SQLALCHEMY_DATABASE_URI: Tells SQLAlchemy where our database is
# sqlite:/// means use SQLite (a simple file-based database)
# chores.db is the filename where all our data will be stored
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chores.db"

# SQLALCHEMY_TRACK_MODIFICATIONS: Disables a feature we don't need (saves memory)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create the database interface object. This is how we'll interact with our database.
db = SQLAlchemy(app)

# Create the login manager. This handles all the authentication stuff.
login_manager = LoginManager(app)

# Tell login_manager which page to redirect to when someone tries to access a protected page
# while not logged in. 'login' refers to our login() function below.
login_manager.login_view = "login"  # type: ignore

# ============================================================================
# DATABASE MODELS - These classes define our database tables
# ============================================================================
# Think of each class as a blueprint for a table. Each instance of the class
# represents one row in that table. SQLAlchemy handles converting between
# Python objects and database rows automatically.


# ----------------------------------------------------------------------------
# USER MODEL - Stores information about each person who can log in
# ----------------------------------------------------------------------------
class User(UserMixin, db.Model):  # type: ignore[name-defined]
    # UserMixin gives us login-related methods like is_authenticated, is_active, etc.
    # db.Model is the base class that makes this a database table

    # __tablename__ explicitly sets the table name in the database (optional but clear)
    __tablename__ = "user"

    # Define the columns in our table:
    # db.Column() creates a column. The first argument is the data type.
    # primary_key=True means this is the unique identifier for each row
    id: int = db.Column(db.Integer, primary_key=True)  # type: ignore

    # String(80) means text up to 80 characters
    # unique=True means no two users can have the same username
    # nullable=False means this field is required (can't be empty/None)
    username: str = db.Column(db.String(80), unique=True, nullable=False)  # type: ignore

    # We store the hashed (encrypted) password, never the actual password
    password_hash: str = db.Column(db.String(255), nullable=False)  # type: ignore

    # role can be 'parent' or 'child' - determines what they can do in the app
    role: str = db.Column(db.String(20), nullable=False)  # type: ignore

    # db.relationship() creates a connection to another table
    # This says "a User can have many ChoreSubmissions"
    # backref='user' means we can access submission.user to get the User who made it
    # lazy=True means don't load the submissions until we actually access them
    chore_submissions = db.relationship("ChoreSubmission", backref="user", lazy=True)  # type: ignore

    def set_password(self, password: str) -> None:
        # Take a plain text password and convert it to a hash
        # The hash is a one-way function - you can't reverse it to get the original password
        # This is why password resets exist instead of password recovery
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        # Check if a plain text password matches our stored hash
        # Returns True if it matches, False if it doesn't
        return check_password_hash(self.password_hash, password)


# ----------------------------------------------------------------------------
# CHORETYPE MODEL - Templates for chores (defined by parent)
# ----------------------------------------------------------------------------
class ChoreType(db.Model):  # type: ignore[name-defined]
    # A ChoreType is like a recipe or template. It defines WHAT a chore is,
    # how much it pays, and when it can be done. Kids submit instances of these.

    __tablename__ = "chore_type"

    id: int = db.Column(db.Integer, primary_key=True)  # type: ignore

    # The name of the chore (e.g., "Clean Your Room")
    name: str = db.Column(db.String(100), nullable=False)  # type: ignore

    # A detailed description of what the chore involves
    description: str = db.Column(db.String(500), nullable=False)  # type: ignore

    # db.Float stores decimal numbers. This is how much money the chore pays.
    value: float = db.Column(db.Float, nullable=False)  # type: ignore

    # Daily limits for each day of the week
    # These control how many times a kid can submit this chore on each day
    # 0 means unlimited (or disabled, depending on context)
    # 1 means once per day, 2 means twice, etc.
    sunday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    monday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    tuesday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    wednesday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    thursday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    friday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    saturday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore

    # db.Boolean stores True/False. active=False means the chore is temporarily disabled.
    active: bool = db.Column(db.Boolean, nullable=False, default=True)  # type: ignore

    # db.DateTime stores date+time. default=datetime.utcnow means automatically set
    # to the current time when a new ChoreType is created
    date_created: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # type: ignore

    # Relationship: One ChoreType can have many ChoreSubmissions
    submissions = db.relationship("ChoreSubmission", backref="chore_type", lazy=True)  # type: ignore

    def __init__(self, **kwargs) -> None:  # type: ignore
        # __init__ is called when creating a new ChoreType instance
        # **kwargs means "accept any keyword arguments" (name=..., value=..., etc.)
        # We pass them to the parent class (db.Model) which handles actual initialization
        super().__init__(**kwargs)

    def get_limit_for_day(self, day_of_week: int) -> int:
        # Helper method to get the limit for a specific day
        # day_of_week: 0=Sunday, 1=Monday, ... 6=Saturday
        # We use this format because Python's datetime.weekday() uses Monday=0
        # but we need Sunday=0 for our database fields
        limits = [
            self.sunday_limit,
            self.monday_limit,
            self.tuesday_limit,
            self.wednesday_limit,
            self.thursday_limit,
            self.friday_limit,
            self.saturday_limit,
        ]
        return limits[day_of_week]

    def get_day_abbreviations(self) -> str:
        # Returns a string like "SMTWThFS" showing which days this chore is available
        # Only includes days where the limit is greater than 0
        # Used for display in the UI
        days = ["S", "M", "T", "W", "Th", "F", "S"]
        limits = [
            self.sunday_limit,
            self.monday_limit,
            self.tuesday_limit,
            self.wednesday_limit,
            self.thursday_limit,
            self.friday_limit,
            self.saturday_limit,
        ]
        # List comprehension: for each (day, limit) pair, include day only if limit > 0
        # Then join all the days into a single string
        return "".join(day for day, limit in zip(days, limits) if limit > 0)


# ----------------------------------------------------------------------------
# CHORESUBMISSION MODEL - An instance of a kid completing a chore
# ----------------------------------------------------------------------------
class ChoreSubmission(db.Model):  # type: ignore[name-defined]
    # When a kid says "I did this chore", we create a ChoreSubmission
    # It starts as 'pending' and waits for parent approval

    __tablename__ = "chore_submission"

    id: int = db.Column(db.Integer, primary_key=True)  # type: ignore

    # db.ForeignKey('user.id') creates a link to the User table
    # This stores which user (kid) submitted this chore
    user_id: int = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # type: ignore

    # Links to which ChoreType template was used
    chore_type_id: int = db.Column(db.Integer, db.ForeignKey("chore_type.id"), nullable=False)  # type: ignore

    # Status: 'pending' means waiting for approval, 'approved' means parent approved it
    status: str = db.Column(db.String(20), nullable=False, default="pending")  # type: ignore

    # When the kid submitted this chore (automatically set to now)
    date_submitted: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # type: ignore

    # Optional[datetime] means this can be None or a datetime
    # It's None until the parent approves it, then we set it to the approval time
    date_approved: Optional[datetime] = db.Column(db.DateTime)  # type: ignore

    # Optional notes from the kid (like "I also organized the closet")
    notes: Optional[str] = db.Column(db.String(500))  # type: ignore

    # Because of the backref in User and ChoreType, we automatically get:
    # - submission.user (the User object who submitted this)
    # - submission.chore_type (the ChoreType object this submission is based on)
    # These aren't actual database columns, they're relationships SQLAlchemy creates

    def __init__(self, **kwargs) -> None:  # type: ignore
        super().__init__(**kwargs)


# ----------------------------------------------------------------------------
# TRANSACTION MODEL - Records of money flow (chores, fines, payments)
# ----------------------------------------------------------------------------
class Transaction(db.Model):  # type: ignore[name-defined]
    # Transactions are our ledger/record book. Every time money changes hands
    # (chore approved, fine levied, payment made), we create a Transaction

    __tablename__ = "transaction"

    id: int = db.Column(db.Integer, primary_key=True)  # type: ignore

    # Which user (usually the child) this transaction affects
    user_id: int = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # type: ignore

    # Type can be: 'chore' (money earned), 'fine' (money deducted), 'payment' (money paid out)
    type: str = db.Column(db.String(20), nullable=False)  # type: ignore

    # Human-readable description like "Approved: Clean Room" or "Fine: Didn't do homework"
    description: str = db.Column(db.String(200), nullable=False)  # type: ignore

    # The amount of money (positive for earnings, but we track the type separately)
    amount: float = db.Column(db.Float, nullable=False)  # type: ignore

    # When this transaction happened
    date: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # type: ignore

    def __init__(self, **kwargs) -> None:  # type: ignore
        super().__init__(**kwargs)


# ============================================================================
# LOGIN MANAGEMENT
# ============================================================================


@login_manager.user_loader
def load_user(user_id):
    # This function is required by Flask-Login
    # It's called whenever Flask-Login needs to reload a user from the session
    # (like when checking if someone is logged in on a new page)
    # We look up the user by ID and return the User object (or None if not found)
    return User.query.get(int(user_id))


# ============================================================================
# DECORATORS - Functions that wrap other functions to add functionality
# ============================================================================
# Decorators are a Python feature that let you "wrap" functions
# Think of them like a security guard: they check something before letting
# the actual function run


def parent_required(f):
    # This decorator ensures only parents can access certain pages
    # @wraps(f) preserves the original function's name and metadata
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check two things:
        # 1. Is anyone logged in? (current_user.is_authenticated)
        # 2. Is their role 'parent'?
        if not current_user.is_authenticated or current_user.role != "parent":
            # If either check fails, show an error message
            flash("Access denied. Parent account required.")
            # Redirect them to the login page
            return redirect(url_for("login"))
        # If checks pass, run the actual function
        return f(*args, **kwargs)

    return decorated_function


def child_required(f):
    # Same as parent_required, but for child accounts
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "child":
            flash("Access denied. Child account required.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# ROUTES - URL endpoints that handle web requests
# ============================================================================
# In Flask, @app.route() creates a "route" - a URL path that triggers a function
# When someone visits that URL, Flask calls the associated function


# ----------------------------------------------------------------------------
# ROOT/HOME PAGE - Redirects based on who's logged in
# ----------------------------------------------------------------------------
@app.route("/")
def index():
    # This handles requests to the root URL (http://yoursite.com/)
    # We check if someone is logged in
    if current_user.is_authenticated:
        # current_user is a special object Flask-Login provides
        # It represents whoever is currently logged in (or an anonymous user if not)
        if current_user.role == "parent":
            # redirect() sends the user to a different URL
            # url_for('parent_dashboard') converts the function name to its URL
            return redirect(url_for("parent_dashboard"))
        else:
            # Must be a child (we only have two roles)
            return redirect(url_for("child_dashboard"))
    # Not logged in, send them to the login page
    return redirect(url_for("login"))


# ----------------------------------------------------------------------------
# LOGIN PAGE - Handles both showing the form (GET) and processing it (POST)
# ----------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    # methods=['GET', 'POST'] means this route handles both:
    # - GET: When someone just visits the page (shows the login form)
    # - POST: When someone submits the form (processes the login)

    # If already logged in, no need to show the login page
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # request is a Flask object that contains information about the current web request
    # request.method tells us if this is a GET (viewing) or POST (submitting) request
    if request.method == "POST":
        # User submitted the login form
        # request.form is like a dictionary containing all the form fields
        # .get('username') safely gets the username field (returns None if missing)
        username = request.form.get("username")
        password = request.form.get("password")

        # Query the database to find a user with this username
        # User.query gives us access to database queries for the User table
        # .filter_by(username=username) finds rows where username matches
        # .first() returns the first match (or None if no match)
        user = User.query.filter_by(username=username).first()

        # Check if we found a user AND the password is correct
        if user and user.check_password(password):
            # Success! Log them in
            # login_user() is a Flask-Login function that:
            # - Creates a session cookie in their browser
            # - Marks them as logged in for future requests
            login_user(user)
            return redirect(url_for("index"))
        else:
            # Invalid username or password
            # flash() stores a message to show on the next page
            flash("Invalid username or password")

    # If GET request (just viewing), or POST with invalid login, show the login form
    # render_template() loads an HTML file from the templates/ folder
    return render_template("login.html")


# ----------------------------------------------------------------------------
# LOGOUT - Ends the user's session
# ----------------------------------------------------------------------------
@app.route("/logout")
@login_required  # This decorator ensures the user is logged in before allowing logout
def logout():
    # logout_user() is a Flask-Login function that:
    # - Removes the session cookie
    # - Marks the user as logged out
    logout_user()
    return redirect(url_for("login"))


# ============================================================================
# CHILD ROUTES - Pages and actions for child accounts
# ============================================================================


# ----------------------------------------------------------------------------
# CHILD DASHBOARD - Main page for kids to see and submit chores
# ----------------------------------------------------------------------------
@app.route("/child/dashboard")
@login_required  # Must be logged in
@child_required  # Must be a child account (not parent)
def child_dashboard():
    # This page shows:
    # 1. Available chores the child can submit
    # 2. Their submitted chores (pending and approved)
    # 3. Their earnings and balance

    # ---- Get all active chore types ----
    # ChoreType.query starts a database query on the ChoreType table
    # .filter_by(active=True) only gets chores where active=True
    # .order_by(ChoreType.name) sorts them alphabetically by name
    # .all() executes the query and returns a list of ChoreType objects
    chore_types = ChoreType.query.filter_by(active=True).order_by(ChoreType.name).all()

    # ---- Get all submissions by this child ----
    # current_user.id is the ID of whoever is logged in
    # .order_by(ChoreSubmission.date_submitted.desc()) sorts newest first
    # .desc() means descending order (newest to oldest)
    submissions = ChoreSubmission.query.filter_by(user_id=current_user.id).order_by(ChoreSubmission.date_submitted.desc()).all()  # type: ignore[attr-defined]

    # ---- Calculate earnings ----
    # sum() is a Python built-in that adds up numbers
    # We use a generator expression to iterate through submissions
    # For pending submissions, add up their value
    pending_earnings = sum(
        sub.chore_type.value for sub in submissions if sub.status == "pending"
    )
    # For approved submissions, add up their value
    approved_earnings = sum(
        sub.chore_type.value for sub in submissions if sub.status == "approved"
    )

    # ---- Get fines ----
    # Transaction records can have type='fine', 'chore', or 'payment'
    # We only want fines for this child
    fines = Transaction.query.filter_by(user_id=current_user.id, type="fine").all()
    total_fines = sum(fine.amount for fine in fines)

    # ---- Get payments received ----
    # These are payments the parent has given to the child
    payments = Transaction.query.filter_by(
        user_id=current_user.id, type="payment"
    ).all()
    total_payments = sum(payment.amount for payment in payments)

    # ---- Calculate final balance ----
    # Money earned (approved) minus fines minus payments already made
    balance = approved_earnings - total_fines - total_payments

    # ---- Check daily limits for each chore type ----
    # We need to know which chores the child can still submit today

    # Get today's date (just the date, not the time)
    today = date.today()

    # Python's weekday() gives: Monday=0, Tuesday=1, ... Sunday=6
    # But our database uses: Sunday=0, Monday=1, ... Saturday=6
    # So we need to convert: add 1 and use modulo 7 to wrap Sunday (6+1=7) to 0
    today_weekday = today.weekday()  # Python's format: Monday=0
    db_weekday = (today_weekday + 1) % 7  # Our format: Sunday=0

    # Create a dictionary to store availability info for each chore type
    # Dictionary = {key: value} pairs, like {1: {...}, 2: {...}}
    chore_availability = {}

    # Loop through each chore type
    for chore_type in chore_types:
        # Count how many times this child has submitted this chore today
        # ChoreSubmission.query.filter() allows multiple conditions (not just equality)
        # func.date() is a SQL function that extracts just the date part
        # .count() counts rows instead of returning them
        today_submissions = ChoreSubmission.query.filter(
            ChoreSubmission.user_id == current_user.id,
            ChoreSubmission.chore_type_id == chore_type.id,
            func.date(ChoreSubmission.date_submitted) == today,
        ).count()

        # Get the limit for today's day of the week
        limit = chore_type.get_limit_for_day(db_weekday)

        # Can submit if limit is 0 (unlimited) OR haven't reached the limit yet
        can_submit = limit == 0 or today_submissions < limit

        # Calculate how many more submissions are allowed
        # If limit is 0 (unlimited), remaining is None
        # Otherwise, it's the limit minus what's been submitted (minimum 0)
        remaining = None if limit == 0 else max(0, limit - today_submissions)

        # Store this info in our dictionary using chore_type.id as the key
        chore_availability[chore_type.id] = {
            "can_submit": can_submit,  # Boolean: can they submit this chore now?
            "today_count": today_submissions,  # How many times submitted today
            "limit": limit,  # The daily limit for this chore type
            "remaining": remaining,  # How many more times can be submitted (or None for unlimited)
        }

    # Render the template with all our calculated data
    # render_template() loads the HTML file and fills in the variables
    # All the variables we pass here become available in the template
    return render_template(
        "child_dashboard.html",
        chore_types=chore_types,
        submissions=submissions,
        pending_earnings=pending_earnings,
        approved_earnings=approved_earnings,
        total_fines=total_fines,
        balance=balance,
        chore_availability=chore_availability,
    )


# ----------------------------------------------------------------------------
# SUBMIT CHORE - Handle when a child submits completed chores
# ----------------------------------------------------------------------------
@app.route("/child/submit_chore", methods=["POST"])
@login_required
@child_required
def submit_chore():
    # This route handles POST requests from the integrated chore submission form
    # It can process multiple chores submitted at once

    # Get today's date and convert weekday format
    today = date.today()
    today_weekday = today.weekday()  # Python: Monday=0
    db_weekday = (today_weekday + 1) % 7  # DB: Sunday=0

    # Get all active chore types
    chore_types = ChoreType.query.filter_by(active=True).all()

    # Track successful submissions
    submitted_chores = []
    errors = []

    # Process each chore type
    for chore_type in chore_types:
        # Get the count field for this chore (either checkbox or number input)
        count_field = f"chore_{chore_type.id}_count"
        count_value = request.form.get(count_field)

        # Skip if no count provided or count is 0
        if not count_value:
            continue

        # Handle checkbox (value is "1" string) or number input
        try:
            if count_value == "on":  # Checkbox checked
                count = 1
            else:
                count = int(count_value)
        except ValueError:
            continue

        # Skip if count is 0 or negative
        if count <= 0:
            continue

        # Get the notes for this chore
        notes_field = f"chore_{chore_type.id}_notes"
        notes = request.form.get(notes_field, "").strip()

        # ---- Check daily limit for this chore type ----
        limit = chore_type.get_limit_for_day(db_weekday)

        # Count how many times they've already submitted this chore today
        today_submissions = ChoreSubmission.query.filter(
            ChoreSubmission.user_id == current_user.id,
            ChoreSubmission.chore_type_id == chore_type.id,
            func.date(ChoreSubmission.date_submitted) == today,
        ).count()

        # Calculate how many more can be submitted
        if limit > 0:
            remaining = limit - today_submissions
            if count > remaining:
                if remaining > 0:
                    errors.append(
                        f"{chore_type.name}: Only {remaining} more allowed today (tried to submit {count})"
                    )
                else:
                    errors.append(f"{chore_type.name}: Daily limit already reached")
                continue

        # ---- Create submissions for each count ----
        for i in range(count):
            submission = ChoreSubmission(
                user_id=current_user.id,
                chore_type_id=chore_type.id,
                notes=notes if notes else None,
            )
            db.session.add(submission)
            submitted_chores.append(chore_type.name)

    # Save all submissions to database
    if submitted_chores:
        db.session.commit()
        if len(submitted_chores) == 1:
            flash(
                f'Chore "{submitted_chores[0]}" submitted! Waiting for parent approval.'
            )
        else:
            flash(
                f"{len(submitted_chores)} chore(s) submitted! Waiting for parent approval."
            )

    # Show any errors
    for error in errors:
        flash(error, "error")

    # If nothing was submitted and no errors, show a message
    if not submitted_chores and not errors:
        flash("Please select at least one chore to submit.")

    return redirect(url_for("child_dashboard"))


# ============================================================================
# PARENT ROUTES - Pages and actions for parent accounts
# ============================================================================


# ----------------------------------------------------------------------------
# PARENT DASHBOARD - Main page for parents to see everything
# ----------------------------------------------------------------------------
@app.route("/parent/dashboard")
@login_required  # Must be logged in
@parent_required  # Must be a parent account
def parent_dashboard():
    # This page shows:
    # 1. Pending chore submissions waiting for approval
    # 2. Recently approved chores
    # 3. Child's balance (earnings - fines - payments)
    # 4. Transaction history

    # ---- Get the child user ----
    # For simplicity, this app assumes there's only one child account
    # .first() returns the first match or None if no match
    child = User.query.filter_by(role="child").first()

    # If no child exists, show a message
    if not child:
        flash("No child account found")
        return render_template("parent_dashboard.html", child=None)

    # ---- Get pending submissions ----
    # These are chores the child submitted that need parent approval
    pending_submissions = (
        ChoreSubmission.query.filter_by(
            user_id=child.id,  # Only this child's submissions
            status="pending",  # Only ones waiting for approval
        )
        .order_by(ChoreSubmission.date_submitted.desc())  # type: ignore[attr-defined]
        .all()
    )  # type: ignore[attr-defined]  # Newest first

    # ---- Get recently approved submissions ----
    # Show the last 20 approved chores
    # .limit(20) restricts the query to only return 20 rows
    approved_submissions = (
        ChoreSubmission.query.filter_by(user_id=child.id, status="approved")
        .order_by(ChoreSubmission.date_approved.desc())  # type: ignore[attr-defined]
        .limit(20)
        .all()
    )  # type: ignore[attr-defined]

    # ---- Calculate approved earnings ----
    # Get all approved chores (not just the last 20) to calculate total earnings
    all_approved = ChoreSubmission.query.filter_by(
        user_id=child.id, status="approved"
    ).all()
    # Sum up the value of each chore
    approved_earnings = sum(sub.chore_type.value for sub in all_approved)

    # ---- Get fines ----
    # Fines are negative transactions (money owed)
    fines = Transaction.query.filter_by(user_id=child.id, type="fine").all()
    total_fines = sum(fine.amount for fine in fines)

    # ---- Get payments ----
    # Payments are when the parent gives money to the child
    payments = Transaction.query.filter_by(user_id=child.id, type="payment").all()
    total_payments = sum(payment.amount for payment in payments)

    # ---- Get all transactions for history ----
    # This includes chores, fines, and payments
    # Sorted by date, newest first
    transactions = (
        Transaction.query.filter_by(user_id=child.id)
        .order_by(Transaction.date.desc()) # type: ignore[attr-defined]
        .all()
    )

    # ---- Calculate current balance ----
    # Balance = money earned - fines - payments already made
    current_balance = approved_earnings - total_fines - total_payments

    # ---- Get all chore types for management ----
    # These are shown in the chore management section
    chore_types = ChoreType.query.order_by(ChoreType.name).all()

    # Render the template with all the data
    return render_template(
        "parent_dashboard.html",
        child=child,
        pending_submissions=pending_submissions,
        approved_submissions=approved_submissions,
        transactions=transactions,
        current_balance=current_balance,
        total_payments=total_payments,
        chore_types=chore_types,
    )


# ----------------------------------------------------------------------------
# MANAGE CHORE TYPES - Page to view all chore templates
# ----------------------------------------------------------------------------
@app.route("/parent/chore_types")
@login_required
@parent_required
def manage_chore_types():
    # Get all chore types (templates), sorted alphabetically by name
    chore_types = ChoreType.query.order_by(ChoreType.name).all()

    # Render the chore management page
    # This page shows all chore types and allows adding/editing/toggling them
    return render_template("manage_chore_types.html", chore_types=chore_types)


# ----------------------------------------------------------------------------
# ADD CHORE TYPE - Create a new chore template
# ----------------------------------------------------------------------------
@app.route("/parent/add_chore_type", methods=["POST"])
@login_required
@parent_required
def add_chore_type():
    # This route handles the form submission for creating a new chore type

    # Get basic chore info from the form
    name = request.form.get("name")  # e.g., "Take out trash"
    description = request.form.get(
        "description"
    )  # e.g., "Take trash and recycling to curb"
    value = request.form.get("value")  # e.g., "2.50" (money amount)

    # Get the daily limits for each day of the week
    # .get('sunday', '0') means: get 'sunday' from the form, or use '0' if not present
    # int() converts the string to an integer
    # 0 means unlimited, any other number is the max submissions per day
    sunday = int(request.form.get("sunday", "0"))
    monday = int(request.form.get("monday", "0"))
    tuesday = int(request.form.get("tuesday", "0"))
    wednesday = int(request.form.get("wednesday", "0"))
    thursday = int(request.form.get("thursday", "0"))
    friday = int(request.form.get("friday", "0"))
    saturday = int(request.form.get("saturday", "0"))

    # Validate that required fields are filled
    # all() returns True only if all items in the list are truthy (not empty/None)
    if not all([name, description, value]):
        flash("Please fill all required fields")
        return redirect(url_for("manage_chore_types"))

    # Try to create the chore type
    try:
        # Create a new ChoreType object with all the data
        chore_type = ChoreType(
            name=name,
            description=description,
            value=float(value),  # type: ignore[arg-type]  # Convert string to number (dollars)
            sunday_limit=sunday,
            monday_limit=monday,
            tuesday_limit=tuesday,
            wednesday_limit=wednesday,
            thursday_limit=thursday,
            friday_limit=friday,
            saturday_limit=saturday,
            # active defaults to True (chore is available)
        )

        # Add to database session and save
        db.session.add(chore_type)
        db.session.commit()

        flash(f'Chore type "{name}" created successfully!')
    except ValueError:
        # This happens if value can't be converted to a number
        flash("Invalid value amount")

    # Redirect back to the chore management page
    return redirect(url_for("manage_chore_types"))


# ----------------------------------------------------------------------------
# EDIT CHORE TYPE - Update an existing chore template
# ----------------------------------------------------------------------------
@app.route("/parent/edit_chore_type/<int:chore_type_id>", methods=["POST"])
@login_required
@parent_required
def edit_chore_type(chore_type_id):
    # <int:chore_type_id> is a URL parameter, e.g., /parent/edit_chore_type/5
    # Flask automatically converts it to an integer and passes it to this function

    # Get the chore type from the database
    chore_type = ChoreType.query.get_or_404(chore_type_id)

    # Update the chore type with new values from the form
    # .get('name', chore_type.name) means: use the new value if provided,
    # otherwise keep the old value (chore_type.name)
    chore_type.name = request.form.get("name", chore_type.name)
    chore_type.description = request.form.get("description", chore_type.description)

    # Try to update numeric fields
    try:
        # Update value (money amount)
        chore_type.value = float(request.form.get("value", chore_type.value))

        # Update all daily limits
        chore_type.sunday_limit = int(
            request.form.get("sunday", chore_type.sunday_limit)
        )
        chore_type.monday_limit = int(
            request.form.get("monday", chore_type.monday_limit)
        )
        chore_type.tuesday_limit = int(
            request.form.get("tuesday", chore_type.tuesday_limit)
        )
        chore_type.wednesday_limit = int(
            request.form.get("wednesday", chore_type.wednesday_limit)
        )
        chore_type.thursday_limit = int(
            request.form.get("thursday", chore_type.thursday_limit)
        )
        chore_type.friday_limit = int(
            request.form.get("friday", chore_type.friday_limit)
        )
        chore_type.saturday_limit = int(
            request.form.get("saturday", chore_type.saturday_limit)
        )

        # Save changes to database
        db.session.commit()

        flash(f'Chore type "{chore_type.name}" updated successfully!')
    except ValueError:
        # This happens if any numeric conversion fails
        flash("Invalid values provided")

    return redirect(url_for("manage_chore_types"))


# ----------------------------------------------------------------------------
# TOGGLE CHORE TYPE - Enable or disable a chore template
# ----------------------------------------------------------------------------
@app.route("/parent/toggle_chore_type/<int:chore_type_id>", methods=["POST"])
@login_required
@parent_required
def toggle_chore_type(chore_type_id):
    # This route activates or deactivates a chore type
    # Deactivated chores don't show up for children to submit

    # Get the chore type
    chore_type = ChoreType.query.get_or_404(chore_type_id)

    # Toggle the active status
    # not True becomes False, not False becomes True
    chore_type.active = not chore_type.active

    # Save the change
    db.session.commit()

    # Show a message telling the parent what happened
    status = "activated" if chore_type.active else "deactivated"
    flash(f'Chore type "{chore_type.name}" {status}')

    return redirect(url_for("manage_chore_types"))


# ----------------------------------------------------------------------------
# APPROVE SUBMISSION - Approve a child's chore submission
# ----------------------------------------------------------------------------
@app.route("/parent/approve_submission/<int:submission_id>", methods=["POST"])
@login_required
@parent_required
def approve_submission(submission_id):
    # This route approves a chore that the child submitted
    # Once approved, the money gets added to their balance

    # Get the submission from the database
    submission = ChoreSubmission.query.get_or_404(submission_id)

    # Update the submission status to approved
    submission.status = "approved"
    # Record when it was approved
    # datetime.utcnow() gets the current date and time in UTC
    submission.date_approved = datetime.utcnow()

    # ---- Create a transaction record ----
    # Transactions track all money movements (chores, fines, payments)
    # This transaction records the earnings from this chore
    transaction = Transaction(
        user_id=submission.user_id,  # Which child earned this
        type="chore",  # Type of transaction
        description=f"Approved: {submission.chore_type.name}",  # What chore was it
        amount=submission.chore_type.value,  # How much money
    )

    # Add the transaction and save everything
    db.session.add(transaction)
    db.session.commit()

    flash("Chore approved!")
    return redirect(url_for("parent_dashboard"))


# ----------------------------------------------------------------------------
# ADD FINE - Record a fine for the child
# ----------------------------------------------------------------------------
@app.route("/parent/add_fine", methods=["POST"])
@login_required
@parent_required
def add_fine():
    # Fines reduce the child's balance
    # They might be for breaking rules, losing things, etc.

    # Get the child user
    child = User.query.filter_by(role="child").first()

    if not child:
        flash("No child account found")
        return redirect(url_for("parent_dashboard"))

    # Get fine details from the form
    description = request.form.get("description")  # e.g., "Lost library book"
    amount = request.form.get("amount")  # e.g., "5.00"

    # Make sure both fields are filled
    if description and amount:
        try:
            # Create a transaction for the fine
            transaction = Transaction(
                user_id=child.id,
                type="fine",  # This is a fine (deducts from balance)
                description=description,
                amount=float(amount),  # Convert string to number
            )

            # Save to database
            db.session.add(transaction)
            db.session.commit()

            flash("Fine added successfully!")
        except ValueError:
            # This happens if amount isn't a valid number
            flash("Invalid amount")
    else:
        flash("Please fill all fields")

    return redirect(url_for("parent_dashboard"))


# ----------------------------------------------------------------------------
# ADD PAYMENT - Record when parent pays the child
# ----------------------------------------------------------------------------
@app.route("/parent/add_payment", methods=["POST"])
@login_required
@parent_required
def add_payment():
    # This route records when the parent pays the child actual money
    # Payments reduce the child's balance (because money is being settled)

    # Get the child user
    child = User.query.filter_by(role="child").first()

    if not child:
        flash("No child account found")
        return redirect(url_for("parent_dashboard"))

    # Get the payment amount from the form
    amount = request.form.get("amount")

    # Make sure an amount was provided
    if amount:
        try:
            # Create a transaction for the payment
            transaction = Transaction(
                user_id=child.id,
                type="payment",  # This is a payment (reduces balance)
                description="Payment made",  # Simple description
                amount=float(amount),  # Convert string to number
            )

            # Save to database
            db.session.add(transaction)
            db.session.commit()

            flash("Payment recorded!")
        except ValueError:
            # This happens if amount isn't a valid number
            flash("Invalid amount")
    else:
        flash("Please enter an amount")

    return redirect(url_for("parent_dashboard"))


# ============================================================================
# MAIN EXECUTION BLOCK
# ============================================================================
# This is Python's way of detecting if this file is being run directly
# (as opposed to being imported as a module by another file)
#
# if __name__ == "__main__": is a special check that is True only when
# you run this file directly (e.g., "python main.py"), not when you import it
if __name__ == "__main__":
    # ---- Create database tables ----
    # app.app_context() creates a special context that Flask needs
    # to work with the database outside of handling a web request
    # The "with" statement ensures the context is properly cleaned up
    with app.app_context():
        # db.create_all() looks at all the model classes we defined
        # (User, ChoreType, ChoreSubmission, Transaction) and creates
        # tables for them if they don't already exist
        # If the tables exist, it does nothing
        db.create_all()

    # ---- Start the Flask web server ----
    # app.run() starts the web server and begins listening for requests
    # debug=True enables:
    #   1. Auto-reload: The server restarts when you change code
    #   2. Detailed error pages: Shows helpful debug info when errors occur
    # WARNING: Never use debug=True in production! Only for development
    # By default, the server runs on http://127.0.0.1:5000/
    app.run(debug=True)
