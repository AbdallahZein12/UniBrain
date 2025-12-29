from flask import render_template, Response, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import v1_bp
from .auth import auth_bp
from app.models import StudentProfile
from app.models.catalog import Campus, Major
from app.models.student_profile import CourseConflictError
from app.core import onboarding_required
from app.core.extensions import db
import json

v1_bp.register_blueprint(auth_bp, url_prefix="/auth")

# html = """
# <h1>Welcome {{ current_user.email }}</h1>

# <form method="POST" action="{{ url_for('v1.auth.logout_post') }}">
#   <button type="submit">Log out</button>
# </form>
# """

@v1_bp.get("/home")
def home():
    return render_template("home.html")

@v1_bp.get("/onboarding")
@login_required
def onboarding():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if profile and profile.onboarding_complete: 
        return redirect(url_for("v1.dashboard"))
    campuses = Campus.query.order_by(Campus.name).all()
    majors = Major.query.order_by(Major.name).all()
    return render_template("onboarding/onboarding.html", campuses=campuses, majors=majors, profile=profile)


@v1_bp.post("/onboarding")
@login_required
def onboarding_post():
    
    next_url = request.args.get("next") or request.form.get("next") or ""
    
    full_name = (request.form.get("full_name") or "").strip()
    campus_id = (request.form.get("campus_id") or "").strip()
    major_id = (request.form.get("major_id") or "").strip()
    expected_grad_year_raw = (request.form.get("expected_grad_year") or "").strip()
    
    courses_json_raw = request.form.get("courses_by_term_json") or ""
    
    errors = []
    
    if not full_name:
        errors.append("Name is required!")
        
    if not campus_id:
        errors.append("Campus is required!")
        
    if not major_id:
        errors.append("Major is required!")

    expected_grad_year = None 
    
    if expected_grad_year:
        try: 
            expected_grad_year = int(expected_grad_year_raw)
        except ValueError:
            errors.append("Expected graduation year must be a number.")
        
    courses_by_term = {"completed":[], "in_progress":[]}
    if courses_json_raw.strip():
        try: 
            courses_by_term = json.loads(courses_json_raw)  
            if not isinstance(courses_by_term, dict): 
                errors.append("Courses payload format is invalid.")
        except json.JSONDecodeError:
            errors.append("Could not read courses payload (invalid JSON).")
            
    if errors:
        for e in errors:
            flash(e,"error")
        return redirect(url_for("v1.onboarding", next=next_url) if next_url else url_for("v1.onboarding"))
     
     # profile creation 
     
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if profile is None: 
        profile = StudentProfile(user_id=current_user.id)
        db.session.add(profile)
    
    profile.full_name = full_name
    profile.campus_id = campus_id
    profile.major_id = major_id
    profile.expected_grad_year = expected_grad_year
    profile.courses_by_term = courses_by_term # triggers StudentProfile event listner for validation
               
    try:
        db.session.commit()
    except CourseConflictError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("v1.onboarding", next=next_url) if next_url else url_for("v1.onboarding"))
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("v1.onboarding", next=next_url) if next_url else url_for("v1.onboarding"))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Something went wrong saving your profile. Please try again", "error")
        return redirect(url_for("v1.onboarding", next=next_url) if next_url else url_for("v1.onboarding"))
    
    flash("Profile saved!", "success")
    
    if next_url.startswith("/"):
        return redirect(next_url)
    
    return redirect(url_for("v1.dashboard"))

    

@v1_bp.get("/dashboard")
@login_required
@onboarding_required
def dashboard():
    return Response(f"""
        <h1>Welcome {current_user.email}</h1>
        <form method="POST" action="/v1/auth/logout">
            <button type="submit">Log out</button>
        </form>
    """, mimetype="text/html")
