import os
from app import create_app
from extensions import db
from modules.pos.models import POSCashRegister
from modules.auth.models import Branch

def create_cash_register():
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        # Check if Branch 1 exists
        branch = Branch.query.filter_by(id=1).first()
        if not branch:
            print("Branch 1 does not exist. Please create it first.")
            return
        
        # Create a new cash register for Branch 1
        cash_register = POSCashRegister(
            name="Branch 1 POS Register",
            balance=0.0,
            branch_id=1
        )
        
        db.session.add(cash_register)
        db.session.commit()
        
        print(f"Cash register '{cash_register.name}' created successfully for Branch 1!")
        
        # List all cash registers for Branch 1
        registers = POSCashRegister.query.filter_by(branch_id=1).all()
        print(f"\nAll cash registers for Branch 1:")
        for reg in registers:
            print(f"ID: {reg.id}, Name: {reg.name}, Branch ID: {reg.branch_id}")

if __name__ == "__main__":
    create_cash_register()
