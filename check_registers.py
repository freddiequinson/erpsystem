from app import create_app
from extensions import db
from modules.pos.models import POSCashRegister

app = create_app()
with app.app_context():
    registers = POSCashRegister.query.all()
    print('Cash Registers:', [(r.id, r.name) for r in registers])
