from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from functools import wraps
from sqlalchemy import func
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import ClassVar

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # type: ignore

# Database Models
class User(UserMixin, db.Model):  # type: ignore[name-defined]
    __tablename__ = 'user'
    id: int = db.Column(db.Integer, primary_key=True)  # type: ignore
    username: str = db.Column(db.String(80), unique=True, nullable=False)  # type: ignore
    password_hash: str = db.Column(db.String(255), nullable=False)  # type: ignore
    role: str = db.Column(db.String(20), nullable=False)  # type: ignore
    chore_submissions = db.relationship('ChoreSubmission', backref='user', lazy=True)  # type: ignore
    
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class ChoreType(db.Model):  # type: ignore[name-defined]
    """Template for chores that can be submitted - defined by parent"""
    __tablename__ = 'chore_type'
    id: int = db.Column(db.Integer, primary_key=True)  # type: ignore
    name: str = db.Column(db.String(100), nullable=False)  # type: ignore
    description: str = db.Column(db.String(500), nullable=False)  # type: ignore
    value: float = db.Column(db.Float, nullable=False)  # type: ignore
    # Daily limits for each day of week (0 = unlimited)
    sunday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    monday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    tuesday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    wednesday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    thursday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    friday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    saturday_limit: int = db.Column(db.Integer, nullable=False, default=1)  # type: ignore
    active: bool = db.Column(db.Boolean, nullable=False, default=True)  # type: ignore
    date_created: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # type: ignore
    submissions = db.relationship('ChoreSubmission', backref='chore_type', lazy=True)  # type: ignore
    
    def __init__(self, **kwargs) -> None:  # type: ignore
        super().__init__(**kwargs)
    
    def get_limit_for_day(self, day_of_week: int) -> int:
        """Get limit for a specific day (0=Sunday, 6=Saturday)"""
        limits = [self.sunday_limit, self.monday_limit, self.tuesday_limit, 
                 self.wednesday_limit, self.thursday_limit, self.friday_limit, self.saturday_limit]
        return limits[day_of_week]
    
    def get_day_abbreviations(self) -> str:
        """Return string like 'SMTWThFS' based on which days have limits > 0"""
        days = ['S', 'M', 'T', 'W', 'Th', 'F', 'S']
        limits = [self.sunday_limit, self.monday_limit, self.tuesday_limit,
                 self.wednesday_limit, self.thursday_limit, self.friday_limit, self.saturday_limit]
        return ''.join(day for day, limit in zip(days, limits) if limit > 0)

class ChoreSubmission(db.Model):  # type: ignore[name-defined]
    """Instance of a chore completed by child - awaiting approval"""
    __tablename__ = 'chore_submission'
    id: int = db.Column(db.Integer, primary_key=True)  # type: ignore
    user_id: int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # type: ignore
    chore_type_id: int = db.Column(db.Integer, db.ForeignKey('chore_type.id'), nullable=False)  # type: ignore
    status: str = db.Column(db.String(20), nullable=False, default='pending')  # type: ignore
    date_submitted: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # type: ignore
    date_approved: Optional[datetime] = db.Column(db.DateTime)  # type: ignore
    notes: Optional[str] = db.Column(db.String(500))  # type: ignore
    # Relationships populated by backrefs (not actual columns, no type annotation needed)
    
    def __init__(self, **kwargs) -> None:  # type: ignore
        super().__init__(**kwargs)

class Transaction(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'transaction'
    id: int = db.Column(db.Integer, primary_key=True)  # type: ignore
    user_id: int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # type: ignore
    type: str = db.Column(db.String(20), nullable=False)  # type: ignore
    description: str = db.Column(db.String(200), nullable=False)  # type: ignore
    amount: float = db.Column(db.Float, nullable=False)  # type: ignore
    date: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # type: ignore
    
    def __init__(self, **kwargs) -> None:  # type: ignore
        super().__init__(**kwargs)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Decorators for role-based access control
def parent_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'parent':
            flash('Access denied. Parent account required.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def child_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'child':
            flash('Access denied. Child account required.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'parent':
            return redirect(url_for('parent_dashboard'))
        else:
            return redirect(url_for('child_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Child Routes
@app.route('/child/dashboard')
@login_required
@child_required
def child_dashboard():
    # Get all active chore types
    chore_types = ChoreType.query.filter_by(active=True).order_by(ChoreType.name).all()
    
    # Get all submissions for this child
    submissions = ChoreSubmission.query.filter_by(user_id=current_user.id).order_by(ChoreSubmission.date_submitted.desc()).all()  # type: ignore[attr-defined]
    
    # Calculate earnings
    pending_earnings = sum(sub.chore_type.value for sub in submissions if sub.status == 'pending')
    approved_earnings = sum(sub.chore_type.value for sub in submissions if sub.status == 'approved')
    
    # Get fines
    fines = Transaction.query.filter_by(user_id=current_user.id, type='fine').all()
    total_fines = sum(fine.amount for fine in fines)
    
    # Get payments received
    payments = Transaction.query.filter_by(user_id=current_user.id, type='payment').all()
    total_payments = sum(payment.amount for payment in payments)
    
    balance = approved_earnings - total_fines - total_payments
    
    # Get today's date for checking limits
    today = date.today()
    today_weekday = today.weekday()  # 0=Monday in Python
    # Convert to 0=Sunday for our database
    db_weekday = (today_weekday + 1) % 7
    
    # For each chore type, check how many times submitted today
    chore_availability = {}
    for chore_type in chore_types:
        today_submissions = ChoreSubmission.query.filter(
            ChoreSubmission.user_id == current_user.id,
            ChoreSubmission.chore_type_id == chore_type.id,
            func.date(ChoreSubmission.date_submitted) == today
        ).count()
        
        limit = chore_type.get_limit_for_day(db_weekday)
        can_submit = limit == 0 or today_submissions < limit  # 0 = unlimited
        remaining = None if limit == 0 else max(0, limit - today_submissions)
        
        chore_availability[chore_type.id] = {
            'can_submit': can_submit,
            'today_count': today_submissions,
            'limit': limit,
            'remaining': remaining
        }
    
    return render_template('child_dashboard.html', 
                         chore_types=chore_types,
                         submissions=submissions,
                         pending_earnings=pending_earnings,
                         approved_earnings=approved_earnings,
                         total_fines=total_fines,
                         balance=balance,
                         chore_availability=chore_availability)

@app.route('/child/submit_chore', methods=['POST'])
@login_required
@child_required
def submit_chore():
    chore_type_id = request.form.get('chore_type_id')
    notes = request.form.get('notes', '')
    
    if not chore_type_id:
        flash('Please select a chore')
        return redirect(url_for('child_dashboard'))
    
    chore_type = ChoreType.query.get_or_404(chore_type_id)
    
    if not chore_type.active:
        flash('This chore is no longer available')
        return redirect(url_for('child_dashboard'))
    
    # Check daily limit
    today = date.today()
    today_weekday = today.weekday()
    db_weekday = (today_weekday + 1) % 7
    
    limit = chore_type.get_limit_for_day(db_weekday)
    
    if limit > 0:  # 0 means unlimited
        today_submissions = ChoreSubmission.query.filter(
            ChoreSubmission.user_id == current_user.id,
            ChoreSubmission.chore_type_id == chore_type.id,
            func.date(ChoreSubmission.date_submitted) == today
        ).count()
        
        if today_submissions >= limit:
            flash(f'You have already submitted the maximum number of "{chore_type.name}" chores for today.')
            return redirect(url_for('child_dashboard'))
    
    # Create submission
    submission = ChoreSubmission(
        user_id=current_user.id,
        chore_type_id=chore_type.id,
        notes=notes
    )
    db.session.add(submission)
    db.session.commit()
    
    flash(f'Chore "{chore_type.name}" submitted! Waiting for parent approval.')
    return redirect(url_for('child_dashboard'))

# Parent Routes
@app.route('/parent/dashboard')
@login_required
@parent_required
def parent_dashboard():
    # Get child user (assuming only one child for simplicity)
    child = User.query.filter_by(role='child').first()
    
    if not child:
        flash('No child account found')
        return render_template('parent_dashboard.html', child=None)
    
    # Get pending submissions
    pending_submissions = ChoreSubmission.query.filter_by(
        user_id=child.id, 
        status='pending'
    ).order_by(ChoreSubmission.date_submitted.desc()).all()  # type: ignore[attr-defined]
    
    # Get approved submissions
    approved_submissions = ChoreSubmission.query.filter_by(
        user_id=child.id,
        status='approved'
    ).order_by(ChoreSubmission.date_approved.desc()).limit(20).all()  # type: ignore[attr-defined]
    
    # Calculate balances
    all_approved = ChoreSubmission.query.filter_by(user_id=child.id, status='approved').all()
    approved_earnings = sum(sub.chore_type.value for sub in all_approved)
    
    # Get fines
    fines = Transaction.query.filter_by(user_id=child.id, type='fine').all()
    total_fines = sum(fine.amount for fine in fines)
    
    # Get payments
    payments = Transaction.query.filter_by(user_id=child.id, type='payment').all()
    total_payments = sum(payment.amount for payment in payments)
    
    # Get all transactions for history
    transactions = Transaction.query.filter_by(user_id=child.id).order_by(Transaction.date.desc()).all()  # type: ignore[attr-defined]
    
    current_balance = approved_earnings - total_fines - total_payments
    
    # Get all chore types for management
    chore_types = ChoreType.query.order_by(ChoreType.name).all()
    
    return render_template('parent_dashboard.html',
                         child=child,
                         pending_submissions=pending_submissions,
                         approved_submissions=approved_submissions,
                         transactions=transactions,
                         current_balance=current_balance,
                         total_payments=total_payments,
                         chore_types=chore_types)

@app.route('/parent/chore_types')
@login_required
@parent_required
def manage_chore_types():
    chore_types = ChoreType.query.order_by(ChoreType.name).all()
    return render_template('manage_chore_types.html', chore_types=chore_types)

@app.route('/parent/add_chore_type', methods=['POST'])
@login_required
@parent_required
def add_chore_type():
    name = request.form.get('name')
    description = request.form.get('description')
    value = request.form.get('value')
    
    # Get day limits
    sunday = int(request.form.get('sunday', '0'))
    monday = int(request.form.get('monday', '0'))
    tuesday = int(request.form.get('tuesday', '0'))
    wednesday = int(request.form.get('wednesday', '0'))
    thursday = int(request.form.get('thursday', '0'))
    friday = int(request.form.get('friday', '0'))
    saturday = int(request.form.get('saturday', '0'))
    
    if not all([name, description, value]):
        flash('Please fill all required fields')
        return redirect(url_for('manage_chore_types'))
    
    try:
        chore_type = ChoreType(
            name=name,
            description=description,
            value=float(value),  # type: ignore[arg-type]  # Already checked value is not None above
            sunday_limit=sunday,
            monday_limit=monday,
            tuesday_limit=tuesday,
            wednesday_limit=wednesday,
            thursday_limit=thursday,
            friday_limit=friday,
            saturday_limit=saturday
        )
        db.session.add(chore_type)
        db.session.commit()
        flash(f'Chore type "{name}" created successfully!')
    except ValueError:
        flash('Invalid value amount')
    
    return redirect(url_for('manage_chore_types'))

@app.route('/parent/edit_chore_type/<int:chore_type_id>', methods=['POST'])
@login_required
@parent_required
def edit_chore_type(chore_type_id):
    chore_type = ChoreType.query.get_or_404(chore_type_id)
    
    chore_type.name = request.form.get('name', chore_type.name)
    chore_type.description = request.form.get('description', chore_type.description)
    
    try:
        chore_type.value = float(request.form.get('value', chore_type.value))
        chore_type.sunday_limit = int(request.form.get('sunday', chore_type.sunday_limit))
        chore_type.monday_limit = int(request.form.get('monday', chore_type.monday_limit))
        chore_type.tuesday_limit = int(request.form.get('tuesday', chore_type.tuesday_limit))
        chore_type.wednesday_limit = int(request.form.get('wednesday', chore_type.wednesday_limit))
        chore_type.thursday_limit = int(request.form.get('thursday', chore_type.thursday_limit))
        chore_type.friday_limit = int(request.form.get('friday', chore_type.friday_limit))
        chore_type.saturday_limit = int(request.form.get('saturday', chore_type.saturday_limit))
        
        db.session.commit()
        flash(f'Chore type "{chore_type.name}" updated successfully!')
    except ValueError:
        flash('Invalid values provided')
    
    return redirect(url_for('manage_chore_types'))

@app.route('/parent/toggle_chore_type/<int:chore_type_id>', methods=['POST'])
@login_required
@parent_required
def toggle_chore_type(chore_type_id):
    chore_type = ChoreType.query.get_or_404(chore_type_id)
    chore_type.active = not chore_type.active
    db.session.commit()
    
    status = 'activated' if chore_type.active else 'deactivated'
    flash(f'Chore type "{chore_type.name}" {status}')
    return redirect(url_for('manage_chore_types'))

@app.route('/parent/approve_submission/<int:submission_id>', methods=['POST'])
@login_required
@parent_required
def approve_submission(submission_id):
    submission = ChoreSubmission.query.get_or_404(submission_id)
    submission.status = 'approved'
    submission.date_approved = datetime.utcnow()
    
    # Create transaction record
    transaction = Transaction(
        user_id=submission.user_id,
        type='chore',
        description=f'Approved: {submission.chore_type.name}',
        amount=submission.chore_type.value
    )
    db.session.add(transaction)
    db.session.commit()
    
    flash('Chore approved!')
    return redirect(url_for('parent_dashboard'))

@app.route('/parent/add_fine', methods=['POST'])
@login_required
@parent_required
def add_fine():
    child = User.query.filter_by(role='child').first()
    
    if not child:
        flash('No child account found')
        return redirect(url_for('parent_dashboard'))
    
    description = request.form.get('description')
    amount = request.form.get('amount')
    
    if description and amount:
        try:
            transaction = Transaction(
                user_id=child.id,
                type='fine',
                description=description,
                amount=float(amount)
            )
            db.session.add(transaction)
            db.session.commit()
            flash('Fine added successfully!')
        except ValueError:
            flash('Invalid amount')
    else:
        flash('Please fill all fields')
    
    return redirect(url_for('parent_dashboard'))

@app.route('/parent/add_payment', methods=['POST'])
@login_required
@parent_required
def add_payment():
    child = User.query.filter_by(role='child').first()
    
    if not child:
        flash('No child account found')
        return redirect(url_for('parent_dashboard'))
    
    amount = request.form.get('amount')
    
    if amount:
        try:
            transaction = Transaction(
                user_id=child.id,
                type='payment',
                description='Payment made',
                amount=float(amount)
            )
            db.session.add(transaction)
            db.session.commit()
            flash('Payment recorded!')
        except ValueError:
            flash('Invalid amount')
    else:
        flash('Please enter an amount')
    
    return redirect(url_for('parent_dashboard'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
