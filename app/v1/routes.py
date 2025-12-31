from flask import render_template, Response, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import v1_bp
from .auth import auth_bp
from app.models import StudentProfile
from app.models.catalog import Campus, Major, Course
from app.models.student_profile import CourseConflictError
from app.core import onboarding_required
from app.core.extensions import db
import json
from sqlalchemy import select

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


@v1_bp.post("/onboarding/validate-courses")
@login_required
def onboarding_validate_courses():
    payload = request.get_json(silent=True) or {}
    courses_by_term = payload.get("courses_by_term") or {"completed": [], "in_progress": []}
    
    # load known courses
    known_raw = db.session.execute(select(Course.id)).scalars().all()
    known_courses = {StudentProfile._norm_course(x) for x in known_raw}
    known_courses.discard(None)
    
    # DO NOT COMMITTTT!
    tmp = StudentProfile(user_id=current_user.id)
    tmp.courses_by_term = courses_by_term
    
    try: 
        tmp.normalize_courses_by_term()
        tmp.validate_courses_by_term(known_courses)
        
        return jsonify({
            "ok": True, 
            "unknown_courses": tmp.unknown_courses or [],
            "suggestions": getattr(tmp, "unknown_course_suggestions",{}) or {},  
        }), 200 
    except ValueError as e: 
        # term format, max courses etc 
        return jsonify({"ok": False, "error": str(e)}), 400

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
    profile = current_user.student_profile
    if profile and profile.onboarding_complete:
        return redirect(url_for("v1.dashboard"))
    
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
    
    if expected_grad_year_raw:
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
    
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    
    return redirect(url_for("v1.dashboard"))

@v1_bp.get("/profile/edit")
@login_required
@onboarding_required
def profile_edit_get(): 
    profile = current_user.student_profile
    campuses = Campus.query.order_by(Campus.name).all()
    majors = Major.query.order_by(Major.name).all()
    return render_template("onboarding/onboarding.html", campuses=campuses, majors=majors, profile=profile, edit_mode=True)

@v1_bp.post("/profile/edit")
@login_required
@onboarding_required
def profile_edit_post(): 
    profile = current_user.student_profile
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
    
    if expected_grad_year_raw:
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
        return redirect(url_for("v1.profile_edit_get", next=next_url) if next_url else url_for("v1.profile_edit_get"))
     
     # profile creation 
     
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    # if profile is None: 
    #     profile = StudentProfile(user_id=current_user.id)
    #     db.session.add(profile)
    
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
        return redirect(url_for("v1.profile_edit_get", next=next_url) if next_url else url_for("v1.profile_edit_get"))
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("v1.profile_edit_get", next=next_url) if next_url else url_for("v1.profile_edit_get"))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Something went wrong saving your profile. Please try again", "error")
        return redirect(url_for("v1.profile_edit_get", next=next_url) if next_url else url_for("v1.profile_edit_get"))
    
    flash("Profile saved!", "success")
    
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    
    return redirect(url_for("v1.dashboard"))

@v1_bp.get("/dashboard")
@login_required
@onboarding_required
def dashboard():
    return render_template("dashboard/index.html")
