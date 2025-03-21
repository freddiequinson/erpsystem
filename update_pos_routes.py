"""
This script updates the POS routes.py file to ensure cash registers are pre-selected
based on the user's branch ID for manager and sales worker accounts.
"""
import os
import re
import shutil
from datetime import datetime

# Path to the routes.py file
routes_file = os.path.join('modules', 'pos', 'routes.py')

# Create a backup of the original file
backup_file = f"{routes_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
shutil.copy2(routes_file, backup_file)
print(f"Created backup at: {backup_file}")

# Read the current content of the file
with open(routes_file, 'r') as file:
    content = file.read()

# Define the pattern to find the new_session function
new_session_pattern = r'@pos\.route\(\'/sessions/new\', methods=\[\'GET\', \'POST\'\]\)\s*@login_required\s*def new_session\(\):'

# Find the new_session function
match = re.search(new_session_pattern, content)
if not match:
    print("Could not find the new_session function in the file.")
    exit(1)

# Find the section where we need to make changes
start_pattern = r'# Filter cash registers by branch for non-admin users'
end_pattern = r'if form\.validate_on_submit\(\):'

start_match = re.search(start_pattern, content)
end_match = re.search(end_pattern, content[match.end():])

if not start_match or not end_match:
    print("Could not find the section to update.")
    exit(1)

# Calculate the actual end position
end_pos = match.end() + end_match.start()

# Define the new code section
new_code = """    # Filter cash registers by branch for non-admin users
    if is_admin:
        # Admin sees all cash registers
        try:
            registers = POSCashRegister.query.all()
            form.cash_register_id.choices = [(r.id, r.name) for r in registers]
        except Exception as e:
            print(f"Error getting cash registers: {e}")
            form.cash_register_id.choices = []
    else:
        # Branch managers and sales workers only see their branch's cash registers
        try:
            # Determine branch ID based on user role and attributes
            branch_id = 1  # Default to Branch 1
            
            # Check if user has branch_id attribute
            if hasattr(current_user, 'branch_id') and current_user.branch_id:
                branch_id = current_user.branch_id
                print(f"Using branch_id from user attributes: {branch_id}")
            # If not, try to extract from username
            elif current_user.username:
                username = current_user.username.lower()
                if 'branch' in username:
                    try:
                        branch_id = int(username.replace('branch', '').strip())
                        print(f"Extracted branch_id from username (branch pattern): {branch_id}")
                    except ValueError:
                        pass
                elif 'manager' in username:
                    try:
                        branch_id = int(username.replace('manager', '').strip())
                        print(f"Extracted branch_id from username (manager pattern): {branch_id}")
                    except ValueError:
                        pass
            
            print(f"User: {current_user.username}, Branch ID: {branch_id}")
            
            # Get cash registers for this specific branch only
            registers = POSCashRegister.query.filter_by(branch_id=branch_id).all()
            
            if registers:
                # Set the choices for the dropdown
                form.cash_register_id.choices = [(r.id, r.name) for r in registers]
                
                # ALWAYS pre-select the first register for non-admin users
                # This is critical to ensure the cash register is selected
                form.cash_register_id.data = registers[0].id
                print(f"Pre-selected cash register ID: {registers[0].id} for branch {branch_id}")
            else:
                flash(f'No cash registers found for Branch {branch_id}. Please contact an administrator.', 'warning')
                form.cash_register_id.choices = []
        except Exception as e:
            print(f"Error filtering cash registers: {e}")
            form.cash_register_id.choices = []
    
"""

# Replace the old section with the new one
updated_content = content[:start_match.start()] + new_code + content[end_pos:]

# Write the updated content back to the file
with open(routes_file, 'w') as file:
    file.write(updated_content)

print(f"Successfully updated {routes_file}")
print("The changes include:")
print("1. Added logic to check if user has branch_id attribute")
print("2. Added logic to extract branch_id from username if attribute not available")
print("3. Improved pre-selection of cash registers based on user's branch")
print("4. Added more detailed logging for debugging")
