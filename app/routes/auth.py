from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.user import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.utils.otp import generate_otp
from flask import session
from flask_mail import Message
from app import mail

# Import necessary modules
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
    
    is_first_user = User.query.count() == 0
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"Registration attempt for username: {username}, email: {email}")
        
        # Input validations
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        if len(username) < 3 or len(username) > 64:
            flash('Username must be between 3 and 64 characters.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)

        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register.html', is_first_user=is_first_user)
        
        try:
            # Generate OTP
            otp = generate_otp()
            
            # Store registration details in session
            session['registration'] = {
                'username': username,
                'email': email,
                'password': password,
                'is_first_user': is_first_user,
                'otp': otp
            }
            
            # Send OTP via email
            '''msg = Message('Your OTP Code', recipients=[email])
            msg.body = f'Your OTP code is {otp}. Please enter this to complete your registration.'
            mail.send(msg)'''
            msg = Message('OTP Verification for Your Account', recipients=[email])
            msg.body = f"""
Hi {username},
Thank you for registering with Civicare.
Your One-Time Password (OTP) for completing your registration is: {otp}
        
This OTP is valid for 5 minutes.

If you did not initiate this request, please ignore this email.

Thanks,  
The Civicare Team
                """
            mail.send(msg)

            

            flash('An OTP has been sent to your email. Please check your inbox.', 'info')
            return redirect(url_for('auth.verify_otp'))
        
        except Exception as e:
            print(f"Error during sending OTP: {str(e)}")
            flash('An error occurred while sending OTP. Please try again.', 'danger')
    
    return render_template('auth/register.html', is_first_user=is_first_user)

@auth_bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    registration_info = session.get('registration')

    if not registration_info:
        flash('No registration process found. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()

        if entered_otp == registration_info['otp']:
            try:
                user = User(
                    username=registration_info['username'],
                    email=registration_info['email'],
                    is_admin=registration_info['is_first_user']
                )
                user.set_password(registration_info['password'])

                db.session.add(user)
                db.session.commit()

                session.pop('registration', None)  # Clear registration session
                flash('Registration successful! You can now login.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                print(f"Error creating user after OTP verification: {str(e)}")
                db.session.rollback()
                flash('An error occurred. Please try again.', 'danger')
                return redirect(url_for('auth.register'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('auth/register.html')



@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
