from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.skill_controller import SkillController

session_bp = Blueprint('sessions', __name__)

@session_bp.route('', methods=['POST'])
@jwt_required()
def add_session():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or "skill_id" not in data or "duration_minutes" not in data:
        return jsonify({"error": "Invalid request"}), 400

    result, status = SkillController.add_learning_session(user_id, data)
    return jsonify(result), status
