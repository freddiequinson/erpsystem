import sqlite3
import os
from config import Config

# The database file path from the config
db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')

print(f"Using database file: {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("\nTables in the database:")
for table in tables:
    print(table[0])

# Check if branch table exists
branch_table_name = None
for table in tables:
    if 'branch' in table[0].lower():
        branch_table_name = table[0]
        break

if branch_table_name:
    print(f"\nFound branch table: {branch_table_name}")
    
    # Get branch table schema
    cursor.execute(f"PRAGMA table_info({branch_table_name})")
    columns = cursor.fetchall()
    print(f"\nColumns in {branch_table_name} table:")
    for column in columns:
        print(f"{column[1]} ({column[2]})")
    
    # List all branches
    cursor.execute(f"SELECT * FROM {branch_table_name}")
    branches = cursor.fetchall()
    print(f"\nBranches in the database:")
    for branch in branches:
        print(f"Branch: {branch}")
else:
    print("\nNo branch table found in the database.")

# Check cash registers table
print("\nCash registers in the database:")
cursor.execute("SELECT * FROM pos_cash_registers")
registers = cursor.fetchall()
for register in registers:
    print(f"Register: {register}")

# Close the connection
conn.close()
