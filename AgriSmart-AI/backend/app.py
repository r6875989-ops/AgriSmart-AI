import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models.database import init_db
from routes.auth import auth_bp
from routes.disease import disease_bp
from routes.fertilizer import fertilizer_bp
from routes.price import price_bp
from routes.voice import voice_bp
from routes.dashboard import dashboard_bp

def create_app(*args, **kwargs):
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # CORS
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    
    # Ensure upload folder exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    init_db()
    
    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(disease_bp)
    app.register_blueprint(fertilizer_bp)
    app.register_blueprint(price_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(dashboard_bp)
    
    # Health check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'app': 'AgriSmart AI Backend',
            'version': '1.0.0'
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 5MB.'}), 413
    
    return app

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Create and run app
    app = create_app()
    print("\n🌾 AgriSmart AI Backend running on http://localhost:5005")
    print("📊 Health check: http://localhost:5005/api/health\n")
    port = int(os.environ.get('PORT' , 5005))
    app.run(
        host='0.0.0.0',
        port=port, 
        debug=False, 
        threaded=True, 
        use_reloader=False
    )
