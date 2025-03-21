import os
import sys
from flask import Flask
from extensions import db

# Add the current directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the models that need tables created
from modules.pos.models import POSReturn, POSReturnLine, QualityCheck

# Create a minimal Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erp_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create the tables
with app.app_context():
    print("Creating returns management tables...")
    db.create_all()
    print("Tables created successfully!")
