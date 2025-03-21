"""
API endpoints for the POS module
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from modules.pos.models import POSCashRegister

pos_api = Blueprint('pos_api', __name__, url_prefix='/api')

@pos_api.route('/branches/<int:branch_id>/cash_registers', methods=['GET'])
@login_required
def get_branch_cash_registers(branch_id):
    """
    Get all cash registers for a specific branch
    
    Admin users can access any branch's registers
    Non-admin users can only access their assigned branch's registers
    """
    # Check if user is admin
    is_admin = current_user.has_role('admin')
    
    # Non-admin users can only access their assigned branch
    if not is_admin and current_user.branch_id != branch_id:
        return jsonify({
            'success': False,
            'message': 'You do not have permission to access this branch',
            'registers': []
        }), 403
    
    try:
        # Get all cash registers for the branch
        registers = POSCashRegister.query.filter_by(branch_id=branch_id).all()
        
        # Format the registers for the response
        registers_data = [
            {
                'id': register.id,
                'name': register.name,
                'balance': register.balance
            }
            for register in registers
        ]
        
        return jsonify({
            'success': True,
            'branch_id': branch_id,
            'registers': registers_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching cash registers: {str(e)}',
            'registers': []
        }), 500
