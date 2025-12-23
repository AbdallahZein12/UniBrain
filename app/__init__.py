from flask import Flask 
from .core import Config
from .core import db, migrate
from dotenv import load_dotenv
from flask_login import LoginManager
from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy.exc import IntegrityError


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
        code_str = (code or secrets.token_urlsafe(10)).upper()
        expires_at = None 
        
        if days and days > 0: 
            expires_at = datetime.now(timezone.utc) + timedelta(days=days)
        
        invite = InviteCode(code=code_str, max_uses=uses, used_count=0, is_active=True, expires_at=expires_at) 
        
        db.session.add(invite)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            click.echo("Invite code already exists or an invalid input was given. Try a different code.")
            return 
        
        click.echo(f"Invite code: {code_str}")
        if expires_at: 
            click.echo(f"Expires: {expires_at} (UTC)")
        click.echo(f"Max uses: {uses}")
        
        