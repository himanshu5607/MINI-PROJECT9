from app import db
from datetime import datetime

class Complaint(db.Model):
    __tablename__ = 'complaint'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    def __init__(self, title, description, location, user_id, category_id, status='pending'):
        self.title = title
        self.description = description
        self.location = location
        self.user_id = user_id
        self.category_id = category_id
        self.status = status

    def __repr__(self):
        return f'<Complaint {self.title}>'
    
    def update_status(self, new_status):
        valid_statuses = ['pending', 'in_progress', 'resolved']
        if new_status in valid_statuses:
            self.status = new_status
            self.updated_at = datetime.utcnow()
            return True
        return False
