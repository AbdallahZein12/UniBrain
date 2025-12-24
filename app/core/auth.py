from functools import wraps 
from flask import abort, redirect, url_for, request
from flask_login import login_required, current_user 

def admin_required(view): 
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return view(*args, **kwargs)
    return wrapped

def onboarding_required(view): 
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs): 
        profile = getattr(current_user, "student_profile", None)
        
        # Onboarding not done 
        if profile is None:
            return redirect(url_for("v1.onboarding"))
        
        # Onboarding not full complete
        if not profile.onboarding_complete: 
            return redirect(url_for("v1.onboarding"))
        
        return view(*args, **kwargs)
    
    return wrapped