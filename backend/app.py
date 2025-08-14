from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Blueprints
from backend.routes.auth import auth_bp
from backend.routes.recipes import recipes_bp

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

def create_app():
    app = Flask(__name__)
    CORS(app) # Enable CORS for all routes

    app.config['SECRET_KEY'] = SECRET_KEY if SECRET_KEY else 'supersecretkey' # Güvenli bir anahtar kullanın!

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(recipes_bp, url_prefix='/api/recipes')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

# Render ve Gunicorn için WSGI callable olarak doğrudan uygulamayı atayın
application = create_app()

