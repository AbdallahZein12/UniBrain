from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError

from app.core.extensions import db
from app.models import User, InviteCode 


def auth_fail_redirect(source: str, default_endpoint: str):
    return (
        url_for("v1.home")
        if source == "modal"
        else url_for(default_endpoint)
)


auth_bp = Blueprint("auth",
    __name__,
    template_folder="templates",
    static_folder="static"
)


@auth_bp.get("/login")
def login_page():
    return render_template("login.html")


@auth_bp.post("/login")
def login_post(): 
    
    source = request.form.get("source", "page")
    if source not in ("modal", "page"):
        source = "page"
    
    email = request.form.get("email","").strip().lower()
    password = request.form.get("password", "")
    
    user = User.query.filter_by(email=email).first() 
    if not user or not user.check_password(password): 
        flash("Invalid email or password!", "error")
        return redirect(auth_fail_redirect(source, "v1.auth.login_page"))
    
    if not user.is_active:
        flash("Account is disabled!", "error")
        return redirect(auth_fail_redirect(source, "v1.auth.login_page"))
    
    login_user(user, remember=True)
    flash("Welcome back!", "success")
    return redirect(url_for("v1.home"))

@auth_bp.get("/signup")
def signup_page():
    return render_template("signup.html")

@auth_bp.post("/signup")
def signup_post(): 
    
    source = request.form.get("source", "page")
    if source not in ("modal", "page"):
        source = "page"
        
    email = request.form.get("email", "").strip().lower() 
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "") 
    invite_code_str = request.form.get("invite_code", "").strip().upper()
    
    if not invite_code_str:
        flash("Invite code is required for the beta!", "error")
        return redirect(auth_fail_redirect(source, "v1.auth.signup_page"))
    
    if not email or not password: 
        flash("Email and password are required!", "error")
        return redirect(auth_fail_redirect(source, "v1.auth.signup_page"))
    
    if password != confirm:
        flash("Passwords do not match!", "error")
        return redirect(auth_fail_redirect(source, "v1.auth.signup_page"))
    
    if len(password) < 7:
        flash("Password must be at least 7 characters!", category="error") 
        return redirect(auth_fail_redirect(source, "v1.auth.signup_page"))
    
    if User.query.filter_by(email=email).first(): 
        flash("Email already registered. Try logging in!", "error")
        return redirect(auth_fail_redirect(source, "v1.auth.login_page"))
    
    try: 
        with db.session.begin():
            code = (
                InviteCode.query
                .filter_by(code=invite_code_str)
                .with_for_update()
                .first() 
            )
            
            if not code or not code.is_valid_now():
                flash("Invite code is invalid or expired!", "error")
                return redirect(auth_fail_redirect(source, "v1.auth.signup_page"))
            
            # consume one use 
            code.used_count += 1 
            code.last_used_at = db.func.now()  
            
            # if it's exhausted, disable it 
            if code.used_count >= code.max_uses:
                code.is_active = False 
                
        
            user = User(email=email)
            user.set_password(password)
        
            db.session.add(user)
    
        login_user(user, remember=True)
        flash("Account created!", "success")
        return redirect(url_for("v1.home"))
    
    except Exception: 
        db.session.rollback() 
        flash("Something went wrong. Please try again.", "error")
        return redirect(auth_fail_redirect(source, "v1.auth.signup_page"))
    
    
@auth_bp.post("/logout")
@login_required
def logout_post():
    logout_user()
    return redirect(url_for("v1.home"))
