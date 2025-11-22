from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.skill_controller import SkillController

skill_bp = Blueprint('skills', __name__)

@skill_bp.route('', methods=['POST'])
@jwt_required()
def create_skill():
    user_id = get_jwt_identity()
    data = request.get_json()
    result, status = SkillController.create_skill(user_id, data)
    return jsonify(result), status

@skill_bp.route('', methods=['GET'])
@jwt_required()
def get_skills():
    user_id = get_jwt_identity()
    result, status = SkillController.get_user_skills(user_id)
    return jsonify(result), status

@skill_bp.route('/<int:skill_id>', methods=['GET'])
@jwt_required()
def get_skill_detail(skill_id):
    user_id = get_jwt_identity()
    result, status = SkillController.get_skill_detail(user_id, skill_id)
    return jsonify(result), status

@skill_bp.route('/subtopics/<int:subtopic_id>/status', methods=['PUT'])
@jwt_required()
def update_subtopic_status(subtopic_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    result, code = SkillController.update_subtopic_status(user_id, subtopic_id, data.get("status"))
    return jsonify(result), code

@skill_bp.route('/learning-sessions', methods=['POST'])
@jwt_required()
def add_learning_session():
    user_id = get_jwt_identity()
    data = request.get_json()
    result, status = SkillController.add_learning_session(user_id, data)
    return jsonify(result), status

@skill_bp.route('/<int:skill_id>/review', methods=['POST'])
@jwt_required()
def submit_final_review(skill_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    result, status = SkillController.submit_final_review(user_id, skill_id, data.get("rating"), data.get("notes"))
    return jsonify(result), status

@skill_bp.route('/<int:skill_id>', methods=['DELETE'])
@jwt_required()
def delete_skill(skill_id):
    user_id = get_jwt_identity()
    result, status = SkillController.delete_skill(user_id, skill_id)
    return jsonify(result), status
