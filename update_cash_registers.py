import sqlite3
import os
from config import Config

# The database file path from the config
db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')

print(f"Using database file: {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Print all cash registers
print("\nCurrent cash registers in the database:")
cursor.execute("SELECT id, name, balance, branch_id FROM pos_cash_registers")
registers = cursor.fetchall()
if registers:
    for register in registers:
        print(f"ID: {register[0]}, Name: {register[1]}, Balance: {register[2]}, Branch ID: {register[3]}")
else:
    print("No cash registers found in the database.")

# Check if we need to create cash registers for branches
cursor.execute("SELECT id, name FROM branches")
branches = cursor.fetchall()
print("\nBranches in the database:")
for branch in branches:
    print(f"ID: {branch[0]}, Name: {branch[1]}")
    
    # Check if this branch has a cash register
    cursor.execute("SELECT COUNT(*) FROM pos_cash_registers WHERE branch_id = ?", (branch[0],))
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Create a cash register for this branch
        register_name = f"{branch[1]} POS Register"
        cursor.execute(
            "INSERT INTO pos_cash_registers (name, balance, branch_id) VALUES (?, ?, ?)",
            (register_name, 0.0, branch[0])
        )
        print(f"Created cash register '{register_name}' for branch ID {branch[0]}")

# Commit changes
conn.commit()

# Print updated cash registers
print("\nUpdated cash registers in the database:")
cursor.execute("SELECT id, name, balance, branch_id FROM pos_cash_registers")
registers = cursor.fetchall()
if registers:
    for register in registers:
        print(f"ID: {register[0]}, Name: {register[1]}, Balance: {register[2]}, Branch ID: {register[3]}")
else:
    print("No cash registers found in the database.")

# Close the connection
conn.close()

print("\nDatabase update completed successfully!")
