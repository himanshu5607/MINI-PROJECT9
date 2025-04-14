from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.user import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if already logged in
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        remember = True if request.form.get('remember') else False

        print(f"Login attempt for email: {email}")  # Debug log

        # Input validation
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return redirect(url_for('auth.login'))

        # Find user by email
        user = User.query.filter_by(email=email).first()
        print(f"User found: {user is not None}")  # Debug log

        # Check if user exists
        if not user:
            flash('No account found with that email.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check password
        if not user.check_password(password):
            print("Password check failed")  # Debug log
            flash('Incorrect password.', 'danger')
            return redirect(url_for('auth.login'))

        print("Password check passed, logging in user")  # Debug log

        # Log in user and update last login time
        login_user(user, remember=remember)
        user.update_last_login()

        print(f"User logged in successfully: {user.username}")  # Debug log

        # Redirect to appropriate dashboard
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard' if current_user.is_admin else 'user.dashboard'))
    
    # Check if this is the first user (will be admin)
    is_first_user = User.query.count() == 0
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"Registration attempt for username: {username}, email: {email}")  # Debug log
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        # Validate username length
        if len(username) < 3 or len(username) > 64:
            flash('Username must be between 3 and 64 characters.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        # Validate email format
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        # Validate password length
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        try:
            # Create new user
            user = User(username=username, email=email, is_admin=is_first_user)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            print(f"User registered successfully: {username}")  # Debug log
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            print(f"Error during registration: {str(e)}")  # Debug log
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
    
    return render_template('auth/register.html', is_first_user=is_first_user)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
