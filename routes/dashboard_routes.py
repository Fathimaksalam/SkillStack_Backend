from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.dashboard_controller import DashboardController

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def get_dashboard():
    user_id = int(get_jwt_identity())
    result = DashboardController.get_dashboard_data(user_id)
    return jsonify(result), 200
