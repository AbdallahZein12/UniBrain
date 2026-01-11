from app.core.extensions import db
from app.models import StudentProfile
from .engines import recompute_course_allocations  

def recompute_for_user(user_id: str) -> None:
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return
    recompute_course_allocations(profile.id, session=db.session)
