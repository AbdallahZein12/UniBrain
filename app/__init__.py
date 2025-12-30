from flask import Flask 
from .core import Config
from app.core.cli import seed_command, make_invite
from .core import db, migrate, limiter, csrf
from dotenv import load_dotenv
from flask_login import LoginManager
from sqlalchemy import event
from sqlalchemy.engine import Engine 
import sqlite3
from werkzeug.middleware.proxy_fix import ProxyFix
import os 


def create_app() -> Flask:
    """
    Initialize and configure the Flask application.
    Loads environment variables from a .env file, creates a Flask app instance,
    and registers the v1 API blueprint with the '/v1' URL prefix.
    Returns:
    Flask: The configured Flask application instance.
    """

    load_dotenv() 
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    
    if os.getenv("FLASK_ENV") != "dev":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
    
    # init extensions 
    db.init_app(app)
    migrate.init_app(app,db)
    limiter.init_app(app)
    csrf.init_app(app)
    
    # import models so Alembic sees them 
    from . import models 
    from app.models import catalog
    from .models import User
    
    #register blueprints 
    from .v1 import v1_bp 
    from .health import health_bp 
    from .admin import admin_bp
    
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(v1_bp, url_prefix="/v1")
    app.register_blueprint(health_bp)
    
    # CLI Commands 
    register_cli(app)
    
    # Login manager
    login_manager = LoginManager()
    login_manager.login_view = 'v1.auth.login_page'
    login_manager.init_app(app)
    
    @login_manager.user_loader  
    def load_user(user_id): 
        return User.query.get(user_id)
    
    return app


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record): 
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close() 
        

def register_cli(app: Flask): 
    app.cli.add_command(seed_command)
    app.cli.add_command(make_invite)
    
