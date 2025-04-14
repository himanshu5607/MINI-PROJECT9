from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.complaint import Complaint
from app.models.category import Category
import os
from werkzeug.utils import secure_filename





user_bp = Blueprint('user', __name__)

@user_bp.route('/about')
def about():
    return render_template('user/about.html')

@user_bp.route('/services')
def services():
    return render_template('user/services.html')

@user_bp.route('/contact')
def contact():
    return render_template('user/contact.html')

@user_bp.route('/faqs')
def faqs():
    return render_template('user/faqs.html')



ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

@user_bp.route('/dashboard')
@login_required
def dashboard():
    complaints = Complaint.query.filter_by(user_id=current_user.id).all()
    return render_template('user/dashboard.html', complaints=complaints)

@user_bp.route('/complaints')
@login_required
def view_complaints():
    complaints = Complaint.query.filter_by(user_id=current_user.id).all()
    return render_template('user/view_complaints.html', complaints=complaints)

@user_bp.route('/submit_complaint', methods=['GET', 'POST'])
@login_required
def submit_complaint():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        category_id = request.form.get('category')
        image = request.files.get('image')
        
        if not all([title, description, location, category_id]):
            flash('All required fields must be filled.', 'danger')
            return redirect(url_for('user.submit_complaint'))
        
        # Create new complaint
        complaint = Complaint(
            title=title,
            description=description,
            location=location,
            user_id=current_user.id,
            category_id=category_id
        )
        
        # Handle image upload
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join('app/statics/uploads', filename)
            image.save(image_path)
            complaint.image_url = filename
        
        try:
            db.session.add(complaint)
            db.session.commit()
            flash('Complaint submitted successfully!', 'success')
            return redirect(url_for('user.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your complaint. Please try again.', 'danger')
    
    categories = Category.query.all()
    return render_template('user/submit_complaint.html', categories=categories)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS