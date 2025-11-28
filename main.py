from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'parent' or 'child'
    chores = db.relationship('Chore', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Chore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending' or 'approved'
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_approved = db.Column(db.DateTime)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'chore', 'fine', 'payment'
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

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
    chores = Chore.query.filter_by(user_id=current_user.id).order_by(Chore.date_created.desc()).all()
    pending_earnings = sum(chore.amount for chore in chores if chore.status == 'pending')
    approved_earnings = sum(chore.amount for chore in chores if chore.status == 'approved')
    
    # Get fines
    fines = Transaction.query.filter_by(user_id=current_user.id, type='fine').all()
    total_fines = sum(fine.amount for fine in fines)
    
    # Get payments received
    payments = Transaction.query.filter_by(user_id=current_user.id, type='payment').all()
    total_payments = sum(payment.amount for payment in payments)
    
    balance = approved_earnings - total_fines - total_payments
    
    return render_template('child_dashboard.html', 
                         chores=chores, 
                         pending_earnings=pending_earnings,
                         approved_earnings=approved_earnings,
                         total_fines=total_fines,
                         balance=balance)

@app.route('/child/add_chore', methods=['POST'])
@login_required
@child_required
def add_chore():
    description = request.form.get('description')
    amount = request.form.get('amount')
    
    if description and amount:
        try:
            chore = Chore(user_id=current_user.id, description=description, amount=float(amount))
            db.session.add(chore)
            db.session.commit()
            flash('Chore added successfully!')
        except ValueError:
            flash('Invalid amount')
    else:
        flash('Please fill all fields')
    
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
    
    # Get pending chores
    pending_chores = Chore.query.filter_by(user_id=child.id, status='pending').order_by(Chore.date_created.desc()).all()
    approved_chores = Chore.query.filter_by(user_id=child.id, status='approved').order_by(Chore.date_approved.desc()).all()
    
    # Calculate balances
    approved_earnings = sum(chore.amount for chore in approved_chores)
    
    # Get fines
    fines = Transaction.query.filter_by(user_id=child.id, type='fine').all()
    total_fines = sum(fine.amount for fine in fines)
    
    # Get payments
    payments = Transaction.query.filter_by(user_id=child.id, type='payment').all()
    total_payments = sum(payment.amount for payment in payments)
    
    # Get all transactions for history
    transactions = Transaction.query.filter_by(user_id=child.id).order_by(Transaction.date.desc()).all()
    
    current_balance = approved_earnings - total_fines - total_payments
    
    return render_template('parent_dashboard.html',
                         child=child,
                         pending_chores=pending_chores,
                         approved_chores=approved_chores,
                         transactions=transactions,
                         current_balance=current_balance,
                         total_payments=total_payments)

@app.route('/parent/approve_chore/<int:chore_id>', methods=['POST'])
@login_required
@parent_required
def approve_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    chore.status = 'approved'
    chore.date_approved = datetime.utcnow()
    
    # Create transaction record
    transaction = Transaction(
        user_id=chore.user_id,
        type='chore',
        description=f'Approved: {chore.description}',
        amount=chore.amount
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
