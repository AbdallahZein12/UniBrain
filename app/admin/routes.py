from flask import render_template, request, flash, redirect, url_for
from app.core import admin_required
from app.models import InviteCode
import string 
import secrets 
from datetime import datetime, timezone, timedelta
from app.core import db
from sqlalchemy.sql import func 
from sqlalchemy.exc import IntegrityError

from . import admin_bp



def _generate_human_code() -> str: 
    alphabet = string.ascii_uppercase + string.digits 
    return "-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3))

@admin_bp.get("/invites")
@admin_required
def invites_page():
    invites = InviteCode.query.order_by(InviteCode.created_at.desc()).all()
    return render_template("admin/invites.html", invites=invites)

@admin_bp.post("/invites")
@admin_required
def create_invite():
    code_raw = (request.form.get("code") or "").strip().upper()
    uses_raw = (request.form.get("uses") or "3").strip()
    days_raw = (request.form.get("days") or "14").strip()
    
    try:
        uses = int(uses_raw)
        days = int(days_raw)
    except ValueError:
        flash("Uses and days must be valid integers!", "error")
        return redirect(url_for("admin.invites_page"))
    
    if uses < 1: 
        flash("Max uses must be at least 1!", "error")
        return redirect(url_for("admin.invites_page"))
    
    if days < 0: 
        flash("Days must be 0 or greater!", "error")
        return redirect(url_for("admin.invites_page"))
    
    code_str = code_raw or _generate_human_code()
    
    expires_at = None 
    if days > 0: 
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)
        
    invite = InviteCode(
        code=code_str, 
        max_uses=uses, 
        used_count=0, 
        is_active=True,  
        expires_at=expires_at, 
        last_used_at=None,
    )
    

    db.session.add(invite)
    try:
        db.session.commit() 
    except IntegrityError: 
        db.session.rollback() 
        flash("That invite code already exists! Try a different code.", "error")
        return redirect(url_for("admin.invites_page"))
    
    
    flash(f"Invite created: {code_str}", "success")
    return redirect(url_for("admin.invites_page"))

@admin_bp.post(f"/invites/<invite_id>/toggle")
@admin_required
def toggle_invite(invite_id: str): 
    invite = InviteCode.query.get(invite_id)
    if not invite:
        flash("Invite not found!", "error")
        return redirect(url_for("admin.invites_page"))
    
    invite.is_active = not invite.is_active
    db.session.commit() 
    
    flash(
        f"Invite {'enabled' if invite.is_active else 'disabled'}: {invite.code}",
        "success"
    )
    
    return redirect(url_for("admin.invites_page"))