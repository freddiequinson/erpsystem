import sqlite3
import bcrypt
import os
from datetime import datetime

# Database path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')

def create_sales_worker_user():
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the Sales Worker role exists
    cursor.execute("SELECT id FROM roles WHERE name = 'Sales Worker'")
    role = cursor.fetchone()
    
    if not role:
        # Create the Sales Worker role
        cursor.execute(
            "INSERT INTO roles (name, description) VALUES (?, ?)",
            ('Sales Worker', 'Sales staff with access limited to POS and returns management')
        )
        conn.commit()
        
        # Get the new role ID
        cursor.execute("SELECT id FROM roles WHERE name = 'Sales Worker'")
        role = cursor.fetchone()
        
        print("Sales Worker role created successfully!")
    
    role_id = role[0]
    
    # Check if the user already exists
    username = "salesuser"
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user:
        user_id = user[0]
        print(f"User '{username}' already exists.")
        
        # Check if user already has the Sales Worker role
        cursor.execute(
            "SELECT id FROM user_roles WHERE user_id = ? AND role_id = ?",
            (user_id, role_id)
        )
        user_role = cursor.fetchone()
        
        if not user_role:
            # Assign the Sales Worker role to the user
            cursor.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id)
            )
            conn.commit()
            print(f"Sales Worker role assigned to user '{username}'.")
    else:
        # Create a new user
        hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, "salesuser@example.com", hashed_password, "Sales", "User", 1, datetime.utcnow())
        )
        conn.commit()
        
        # Get the new user ID
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        user_id = user[0]
        
        # Assign the Sales Worker role to the user
        cursor.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
            (user_id, role_id)
        )
        conn.commit()
        
        print(f"Sales Worker user created successfully!")
    
    print(f"Login credentials: Username: {username}, Password: password123")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    create_sales_worker_user()
