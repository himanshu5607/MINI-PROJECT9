from flask import Blueprint, render_template
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return render_template('admin/dashboard.html')
        return render_template('user/dashboard.html')
    return render_template('index.html')
