from flask import Blueprint

reports_bp = Blueprint('reports', __name__)

# Import routes at the end to avoid circular imports
from . import routes
