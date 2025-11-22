from models.user import User
from utils.helpers import hash_password, check_password

class AuthController:
    @staticmethod
    def register_user(username, email, password):
        """Register a new user"""
        # Check if user already exists
        if User.find_by_username(username):
            return {'error': 'Username already exists'}, 400
        
        if User.find_by_email(email):
            return {'error': 'Email already exists'}, 400
        
        # Validate password length
        if len(password) < 6:
            return {'error': 'Password must be at least 6 characters'}, 400
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password)
        )
        
        if user.save():
            return {
                'message': 'User registered successfully',
                'user': user.to_dict()
            }, 201
        else:
            return {'error': 'Registration failed'}, 500
    
    @staticmethod
    def login_user(username, password):
        """Login user and return user data"""
        user = User.find_by_username(username)
        
        if user and check_password(password, user.password_hash):
            return {
                'user_id': user.id,
                'username': user.username,
                'message': 'Login successful'
            }, 200
        else:
            return {'error': 'Invalid username or password'}, 401