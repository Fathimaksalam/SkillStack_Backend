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
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "https://skillstack-frontend-3a8v.onrender.com"
    ]
)
    JWTManager(app)

    # Initialize DB
    init_database()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(skill_bp, url_prefix='/api/skills')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(session_bp, url_prefix='/api/sessions')

    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'SkillStack API is running',
            'version': '1.0.0'
        })

    return app



app = create_app()


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    print("🚀 Starting SkillStack Backend…")
    print(f"📊 Server running on port: {port}")
    app.run(host='0.0.0.0', port=port)
