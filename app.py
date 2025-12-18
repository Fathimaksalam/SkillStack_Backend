from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from utils.database import init_database

# Import routes
from routes.auth_routes import auth_bp
from routes.skill_routes import skill_bp
from routes.dashboard_routes import dashboard_bp
from routes.session_routes import session_bp

def create_app():
    app = Flask(__name__)

    # JWT settings
    app.config['JWT_SECRET_KEY'] = 'skillstack-secret-key-2024-change-in-production'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400  # 24 hours

   
    CORS(
        app,
        resources={r"/api/*": {
        "origins":["http://localhost:5174", "http://127.0.0.1:5174"] ,
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"]
    }},
        supports_credentials=True
    )

    # JWT setup
    jwt = JWTManager(app)

    # Initialize DB
    init_database()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(skill_bp, url_prefix='/api/skills')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(session_bp, url_prefix='/api/sessions')

    # Health check
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'SkillStack API is running',
            'version': '1.0.0'
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    print("🚀 Starting SkillStack Backend…")
    print("🌐 Allowed CORS Origin: http://localhost:5174")
    print("📊 Server: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
