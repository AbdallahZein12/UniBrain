from flask import Flask 
from .core.config import Config
from .core.extensions import db, migrate
from dotenv import load_dotenv
from flask_login import LoginManager
from datetime import timedelta
import datetime

from app.models import InviteCode

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
    
    # init extensions 
    db.init_app(app)
    migrate.init_app(app,db)
    
    # import models so Alembic sees them 
    from . import models 
    
    #register blueprints 
    from .v1 import v1_bp 
    from .routes.health import bp as health_bp 
    
    app.register_blueprint(v1_bp, url_prefix="/v1")
    app.register_blueprint(health_bp)
    
    # CLI Commands 
    register_cli(app)
    
    # Login manager
    # login_manager = LoginManager()
    # login_manager.login_view = 'v1.auth.login'
    # login_manager.init_app(app)
    
    # @login_manager.user_loader  
    # def load_user(id): 
    #     return db.session.get(User, id)
    
    return app

def register_cli(app: Flask): 
    from .core.extensions import db 
    import click 
    
    @app.cli.command("seed")
    def seed():
        """Seed the db with initial data"""
        click.echo("Sending DB....")
        db.session.commit() 
        click.echo("Done!")
    
    @app.cli.command("make-invite")
    @click.option("--code", help="Your custom invite code")
    @click.option("--uses", default=3, show_default=True, help="Max uses for the invite code")
    @click.option("--days", default=14, show_default=True, help="Days until expiration (0 = no expiry!)")
    def make_invite(code, uses, days): 
        """Create a new invite code"""
        code_str = code 
        expires_at = None 
        if days and days > 0: 
            expires_at = datetime.utcnow() + timedelta(days=days)
        
        invite = InviteCode(code=code_str, max_uses=uses, used_count=0, is_active=True, expires_at=expires_at) 
        db.session.add(invite)
        db.session.commit() 
        
        click.echo(f"Invite code: {code_str}")
        if expires_at: 
            click.echo(f"Expires: {expires_at} (UTC)")
        click.echo(f"Max uses: {uses}")
        
        