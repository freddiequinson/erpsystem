
from app import create_app, db

def create_tables():
    app = create_app('development')
    with app.app_context():
        db.create_all()
        print("All database tables created successfully!")

if __name__ == '__main__':
    create_tables()
