from flask import render_template, Response, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, logout_user
from . import v1_bp
from .auth import auth_bp
from app.models.enums import SlotType
from app.models import StudentProfile, User
from app.models.catalog import Campus, Major, Course
from app.models.ontology import CourseAllocation, RequirementGroup, RequirementSlot
from app.models.student_profile import CourseConflictError
from app.core import onboarding_required
from app.core.extensions import db
import json
from sqlalchemy import select, delete

from app.services import recompute_for_user
from app.services.engines.recompute_course_allocations import extract_course_instances, preferred_term_by_course, recompute_course_allocations
from app.services.engines.build_eligible_slots_by_course import build_eligible_slots_by_course


v1_bp.register_blueprint(auth_bp, url_prefix="/auth")

# html = """
# <h1>Welcome {{ current_user.email }}</h1>

# <form method="POST" action="{{ url_for('v1.auth.logout_post') }}">
#   <button type="submit">Log out</button>
# </form>
# """


def safe_next_url(fallback_endpoint: str):
    """
    Basic safety: allow only relative paths so nobody can send users to evil.com
    """
    nxt = (request.form.get("next") or "").strip()
    if nxt.startswith("/"):
        return nxt
    return url_for(fallback_endpoint)

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
    
    try:
        recompute_for_user(current_user.id)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        # Don’t fail onboarding because allocations failed 
        flash("Profile saved, but we couldn't update your degree progress yet.", "warning")
    
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    
    return redirect(url_for("v1.dashboard"))


@v1_bp.post("/account/delete")
@login_required
def delete_account_post():
    next_url = safe_next_url("v1.onboarding_get")
    
    try:
        # user = current_user
        user = db.session.get(User, current_user.id)
        
        # important to log out before deleting the row to avoid stale session 
        logout_user()
        
        # should cascade
        db.session.delete(user)
        db.session.commit()
        
        flash("Your account has been deleted.", "success")
        return redirect(url_for("v1.home"))
    
    except Exception as e: 
        print(e)
        db.session.rollback()
        flash("Could not delete account. Please try again.", "error")
        return redirect(next_url)

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
    
    try:
        recompute_for_user(current_user.id)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Profile saved, but we couldn't update your degree progress yet.", "warning")
    
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    
    return redirect(url_for("v1.dashboard"))

@v1_bp.get("/dashboard")
@login_required
@onboarding_required
def dashboard():
    profile = current_user.student_profile 
    
    req_groups = RequirementGroup.query.filter_by(owner_id=profile.major_id).all()
    group_ids = [g.id for g in req_groups]
    
    
    slots = RequirementSlot.query.filter(RequirementSlot.requirement_group_id.in_(group_ids)).all()
    slots_by_id = {s.id: s for s in slots}
    
    total_slots = len(slots)
    
    allocs = CourseAllocation.query.filter_by(student_profile_id=profile.id).all()
    
    allocs_by_slot = {} 
    for a in allocs: 
        allocs_by_slot.setdefault(a.requirement_slot_id, []).append(a)
    
    satisfied = 0 
    
    for slot_id, slot in slots_by_id.items():
        slot_allocs = allocs_by_slot.get(slot_id, [])
        
        if not slot_allocs:
            continue 
        
        if slot.slot_type == SlotType.BUCKET: 
            course_ids = [a.course_id for a in slot_allocs]
            courses = Course.query.filter(Course.id.in_(course_ids)).all()
            credits = sum(int(c.credits or 0) for c in courses)
            if credits >= int(slot.min_credits_required or 0):
                satisfied += 1 
                
        else: 
            satisfied += 1 
            
    percentage_completed = int(round(((satisfied / total_slots) * 100))) if total_slots else 0 
    percentage_completed = max(0, min(100, percentage_completed))
            
            
    
    
    return render_template("dashboard/index.html", slots_satisfied=satisfied, slots_total=total_slots, percentage_completed=percentage_completed)


@v1_bp.get("/allocations")
@login_required
@onboarding_required
def allocations_get():
    profile = current_user.student_profile
    
    # flatten courses_by_term
    instances = extract_course_instances(profile.courses_by_term or {})
    term_by_course = preferred_term_by_course(instances=instances)
    taken_course_ids = sorted(term_by_course.keys())
    
    # load current allocs
    allocs = CourseAllocation.query.filter_by(student_profile_id=profile.id).all()
    alloc_by_course = {a.course_id: a for a in allocs}
    
    # load slots + groups (for labels)
    groups = RequirementGroup.query.filter_by(owner_id=profile.major_id).all()
    group_ids = [g.id for g in groups]
    slots = RequirementSlot.query.filter(RequirementSlot.requirement_group_id.in_(group_ids)).all()
    slots_by_id = {s.id: s for s in slots}
    
    # load course titles for display 
    courses = Course.query.filter(Course.id.in_(taken_course_ids)).all()
    courses_by_id = {c.id:c for c in courses}
    
    eligible_by_course = build_eligible_slots_by_course(
        taken_course_ids=taken_course_ids,
        slots_by_id=slots_by_id,
        include_bucket_slots= True
    )
    
    # build view 
    
    rows = [] 
    for cid in taken_course_ids: 
        c = courses_by_id.get(cid)
        alloc = alloc_by_course.get(cid)
        eligible_slots = [slots_by_id[sid] for sid in sorted(eligible_by_course.get(cid,[])) if sid in slots_by_id]
    
        
        completed = profile.flatten_courses()[0]
        in_prog = profile.flatten_courses()[1]
        
        rows.append({
            "course_id": cid,
            "status": "Completed" if cid in completed else ("In progress" if cid in in_prog else "Unknown"),
            "title": getattr(c, "title", cid),
            "credits": getattr(c, "credits", None),
            "term": term_by_course.get(cid, "UNKNOWN"),
            "allocation": None if not alloc else {
                "requirement_slot_id": alloc.requirement_slot_id,
                "label": getattr(slots_by_id.get(alloc.requirement_slot_id), "label", alloc.requirement_slot_id),
                "locked": alloc.locked,
                "reason": alloc.reason,
            },
            "eligible_slots": [{"id": s.id, "label": s.label} for s in eligible_slots],
            "has_overlap": len(eligible_slots) > 1,
        })
    
        
    return render_template("allocations/allocations.html", rows=rows)

@v1_bp.post("/allocations/override")
@login_required
@onboarding_required
def allocations_override_post():
    profile = current_user.student_profile
    
    request_form = request.form
    cid = (request_form.get("course_id") or "").strip().upper()
    req_slot_id = (request_form.get("requirement_slot_id") or "").strip()
    
    if not cid or not req_slot_id: 
        flash("Missing course or requirement selection.", "error")
    
    # ensure course is actually in the student's courses_by_term    
    instances = extract_course_instances(profile.courses_by_term or {})
    term_by_course = preferred_term_by_course(instances)
    
    if cid not in term_by_course:
        flash("That course is not in your profile!", "error")
        return redirect(url_for("v1.allocations_get"))
    
    term = term_by_course[cid]
    
    # ensure req_slot_id is in the student's curr (owned by major)
    group_ids = db.session.execute(
        select(RequirementGroup.id).where(RequirementGroup.owner_id == profile.major_id)
        
    ).scalars().all()
    
    slot = db.session.execute(
        select(RequirementSlot).where(
            RequirementSlot.id == req_slot_id,
            RequirementSlot.requirement_group_id.in_(group_ids)
        )
    ).scalars().first()
    
    if not slot: 
        flash("That requirement is not part of your curriculum!", "error")
        return redirect(url_for("v1.allocations_get"))
    
    # ensure course is eligible for that slot 
    # build curriculum slots map once 
    
    curr_slots = db.session.execute(
        select(RequirementSlot).where(RequirementSlot.requirement_group_id.in_(group_ids))
    ).scalars().all()
    slots_by_id = {s.id: s for s in curr_slots}
    
    eligible_by_course = build_eligible_slots_by_course(
        taken_course_ids=[cid], 
        slots_by_id=slots_by_id, 
        session=db.session, 
        include_bucket_slots=True 
    )
    
    if req_slot_id not in (eligible_by_course.get(cid) or set()):
        flash("That course can't satisfy the selected requirement!", "error")
        return redirect(url_for("v1.allocations_get"))
    
    # upsert alloc for this course:
    existing = CourseAllocation.query.filter_by(
        student_profile_id=profile.id, 
        course_id=cid
    ).first() 
    
    if existing: 
        existing.requirement_slot_id = req_slot_id 
        existing.term = term 
        existing.locked = True 
        existing.reason = "student_selected"
    else: 
        db.session.add(
            CourseAllocation(
                student_profile_id=profile.id, 
                course_id=cid, 
                requirement_slot_id=req_slot_id, 
                term=term, 
                locked=True, 
                reason="student_selected"
            )
        )
    
    try:
        db.session.commit() 
    except Exception as e: 
        print(e)
        db.session.rollback()
        flash("Could not save your override. Please try again", "error")
        return redirect(url_for("v1.allocations.get"))
    
    # recompute 
    try: 
        recompute_course_allocations(profile.id, session=db.session)
        db.session.commit() 
    except Exception as e: 
        print(e)
        db.session.rollback() 
        flash("Override saved, but we couldn't refresh your other allocations yet", "warning")
        return redirect(url_for("v1.allocations_get"))
    
    flash("Allocation updated", "success")
    return redirect(url_for("v1.allocations_get"))
    
    
@v1_bp.post("/allocations/reset")
@login_required
@onboarding_required
def allocations_reset_post():
    profile = current_user.student_profile

    cid = (request.form.get("course_id") or "").strip().upper()
    if not cid:
        flash("Missing course id.", "error")
        return redirect(url_for("v1.allocations_get"))

    # Ensure the course is actually in the student's profile (so nobody can submit random ids)
    instances = extract_course_instances(profile.courses_by_term or {})
    term_by_course = preferred_term_by_course(instances)
    if cid not in term_by_course:
        flash("That course is not in your profile.", "error")
        return redirect(url_for("v1.allocations_get"))

    alloc = CourseAllocation.query.filter_by(
        student_profile_id=profile.id,
        course_id=cid
    ).first()

    if not alloc:
        flash("Nothing to reset for that course.", "warning")
        return redirect(url_for("v1.allocations_get"))

    try:
        # delete and let solver re-create it
        db.session.delete(alloc)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Could not reset that allocation.", "error")
        return redirect(url_for("v1.allocations_get"))

    # Recompute around it
    try:
        recompute_course_allocations(profile.id, session=db.session)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Reset saved, but we couldn't refresh the plan yet.", "warning")
        return redirect(url_for("v1.allocations_get"))

    flash("Reset to recommended.", "success")
    return redirect(url_for("v1.allocations_get"))

@v1_bp.post("/allocations/reset_all")
@login_required
@onboarding_required
def allocations_reset_all_post():
    profile = current_user.student_profile

    try:
        # Delete ALL allocations for this student (locked + unlocked)
        db.session.execute(
            delete(CourseAllocation).where(
                CourseAllocation.student_profile_id == profile.id
            )
        )
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Could not reset allocations. Please try again.", "error")
        return redirect(url_for("v1.allocations_get"))

    # Recompute fresh recommended allocations
    try:
        recompute_course_allocations(profile.id, session=db.session)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Allocations cleared, but we couldn't recompute recommendations yet.", "warning")
        return redirect(url_for("v1.allocations_get"))

    flash("All allocations reset to recommended.", "success")
    return redirect(url_for("v1.allocations_get"))