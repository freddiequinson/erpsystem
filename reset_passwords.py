from app import create_app, db
from modules.auth.models import User
import bcrypt

def reset_passwords():
    app = create_app('default')
    with app.app_context():
        # Reset admin password
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f"Resetting password for user: {admin_user.username}")
            # Generate a proper bcrypt hash
            password = 'admin123'
            admin_user.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.session.commit()
            print(f"Password for {admin_user.username} has been reset to: {password}")
        else:
            print("Admin user not found")
        
        # Reset manager password
        manager_user = User.query.filter_by(username='manager').first()
        if manager_user:
            print(f"Resetting password for user: {manager_user.username}")
            # Generate a proper bcrypt hash
            password = 'manager123'
            manager_user.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.session.commit()
            print(f"Password for {manager_user.username} has been reset to: {password}")
        else:
            print("Manager user not found")

if __name__ == '__main__':
    reset_passwords()
