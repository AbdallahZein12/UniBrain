import click 
from app.core import db 
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta 
import secrets 
from app.models import InviteCode
from flask.cli import with_appcontext



@click.command("make-invite")
@click.option("--code", help="Your custom invite code")
@click.option("--uses", default=3, show_default=True, help="Max uses for the invite code")
@click.option("--days", default=14, show_default=True, help="Days until expiration (0 = no expiry!)")
@with_appcontext
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
    
    