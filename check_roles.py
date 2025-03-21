from app import create_app, db
from modules.auth.models import Role, User, UserRole

def check_roles():
    app = create_app('default')
    with app.app_context():
        # Check existing roles
        roles = Role.query.all()
        print('Available roles:')
        for role in roles:
            print(f'- {role.name}')
        
        # Check if Manager role exists
        manager_role = Role.query.filter_by(name='Manager').first()
        if not manager_role:
            print('Creating Manager role...')
            manager_role = Role(name='Manager', description='Access to manager dashboard and staff management')
            db.session.add(manager_role)
            db.session.commit()
            print('Manager role created successfully!')
        else:
            print('Manager role already exists.')
        
        # Check if Admin role exists
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            print('Creating Admin role...')
            admin_role = Role(name='Admin', description='Full system access')
            db.session.add(admin_role)
            db.session.commit()
            print('Admin role created successfully!')
        else:
            print('Admin role already exists.')
        
        # Check users with Manager role
        manager_users = User.query.join(UserRole).join(Role).filter(Role.name == 'Manager').all()
        print(f'\nUsers with Manager role: {len(manager_users)}')
        for user in manager_users:
            print(f'- {user.username}')
        
        # Check users with Admin role
        admin_users = User.query.join(UserRole).join(Role).filter(Role.name == 'Admin').all()
        print(f'\nUsers with Admin role: {len(admin_users)}')
        for user in admin_users:
            print(f'- {user.username}')
        
        # Check if there's at least one admin user
        if not admin_users:
            print('\nNo admin users found. Creating a default admin user...')
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(username='admin', email='admin@example.com')
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print('Default admin user created with username: admin, password: admin123')
            
            # Assign admin role to the admin user
            if admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
                db.session.commit()
                print('Admin role assigned to admin user.')

if __name__ == '__main__':
    check_roles()
