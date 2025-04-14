from app import create_app, db
from app.models.user import User
from app.models.complaint import Complaint
from app.models.category import Category

app = create_app()

# Create database tables
def init_db():
    with app.app_context():
        # Check if we already have tables
        if not User.query.first():
            print("Initializing database...")
            db.create_all()
            
            print("Creating default admin and categories...")
            # Create default admin
            admin = User(
                username='admin',
                email='admin@mcgm.in',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create default categories
            categories = [
                Category(name='Roads', description='Issues related to roads and pavements'),
                Category(name='Water', description='Water supply and drainage issues'),
                Category(name='Electricity', description='Power supply and street lighting issues'),
                Category(name='Sanitation', description='Waste management and cleanliness issues'),
                Category(name='Others', description='Other civil issues')
            ]
            for category in categories:
                db.session.add(category)
            
            try:
                db.session.commit()
                print("Database initialized successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"Error initializing database: {e}")
                raise
        else:
            print("Database already exists, skipping initialization")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    init_db()  # Initialize with default data if needed
    app.run(debug=True)
