from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    result, status_code = AuthController.register_user(username, email, password)
    
    if status_code == 201:
        user_data = result['user']
        access_token = create_access_token(identity=str(user_data['id']))
        result['access_token'] = access_token
        result['user_id'] = user_data['id']
        result['username'] = user_data['username']
    
    return jsonify(result), status_code

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    result, status_code = AuthController.login_user(username, password)
    
    if status_code == 200:
        access_token = create_access_token(identity=str(result['user_id']))
        result['access_token'] = access_token
    
    return jsonify(result), status_code
