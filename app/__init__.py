from flask import Flask 
from dotenv import load_dotenv

def create_app() -> Flask:
    """
    Initialize and configure the Flask application.
    Loads environment variables from a .env file, creates a Flask app instance,
    and registers the v1 API blueprint with the '/v1' URL prefix.
    Returns:
    Flask: The configured Flask application instance.
    """
    
    load_dotenv() 
    app = Flask(__name__)
    
    from .v1 import v1_bp 
    app.register_blueprint(v1_bp, url_prefix="/v1")
    
    return app