from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.complaint import Complaint
from app.models.category import Category
from app.models.user import User
import random
import string
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    complaints = Complaint.query.all()
    users = User.query.all()
    categories = Category.query.all()
    return render_template('admin/dashboard.html',
                         complaints=complaints,
                         users=users,
                         categories=categories,
                         now=datetime.now())

@admin_bp.route('/complaints')
@admin_required
def view_complaints():
    complaints = Complaint.query.all()
    return render_template('admin/complaints.html', complaints=complaints)

@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if name:
            category = Category(name=name, description=description)
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully.', 'success')
        return redirect(url_for('admin.manage_categories'))
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/category/<int:id>/delete', methods=['POST'])
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/category/<int:id>/edit', methods=['POST'])
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if name:
            category.name = name
            category.description = description
            db.session.commit()
            flash('Category updated successfully.', 'success')
        else:
            flash('Category name is required.', 'danger')
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/complaint/<int:id>/status', methods=['POST'])
@admin_required
def update_complaint_status(id):
    complaint = Complaint.query.get_or_404(id)
    status = request.form.get('status')
    
    if status in ['pending', 'in_progress', 'resolved']:
        complaint.status = status
        db.session.commit()
        flash(f'Complaint #{complaint.id} status updated to {status.replace("_", " ").title()}.', 'success')
    else:
        flash('Invalid status provided.', 'danger')
    
    return redirect(url_for('admin.view_complaints'))

@admin_bp.route('/complaint/<int:id>/delete', methods=['POST'])
@admin_required
def delete_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    db.session.delete(complaint)
    db.session.commit()
    flash(f'Complaint #{id} has been deleted.', 'success')
    return redirect(url_for('admin.view_complaints'))

@admin_bp.route('/user/<int:id>/delete', methods=['POST'])
@admin_required
def delete_user(id):
    if current_user.id == id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user = User.query.get_or_404(id)
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot delete the last admin user.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # Delete all complaints associated with the user
    Complaint.query.filter_by(user_id=id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'User and all associated complaints have been deleted.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(id):
    if current_user.id == id:
        flash('You cannot modify your own admin status.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user = User.query.get_or_404(id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    action = "granted" if user.is_admin else "revoked"
    flash(f'Admin privileges {action} for user {user.username}.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(id):
    if current_user.id == id:
        flash('Use the profile page to change your own password.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user = User.query.get_or_404(id)
    # Generate a random password
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    user.set_password(new_password)
    db.session.commit()
    
    flash(f'Password reset for {user.username}. New password: {new_password}', 'success')
    return redirect(url_for('admin.manage_users'))
