from app.core import db
import uuid
from sqlalchemy.sql import func 
from sqlalchemy import event
import re 

LIU_KNOWN_COURSES: set[str] = set() # TODO: replace with LIU catalog set



class StudentProfile(db.Model):
    TERM_RE = re.compile(r"^(Spring|Summer|Fall|Winter)\s(20\d{2})$")
    MAX_COURSES_PER_TERM = 8
    
    
    __tablename__ = "student_profiles"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, 
        nullable=False, 
        index=True
    )
    
    full_name = db.Column(db.String(120), nullable=True)
    
    # ontology keys (strings)
    campus_id = db.Column(db.String(64), nullable=True, index=True)
    major_id = db.Column(db.String(64), nullable=True, index=True)
    
    expected_grad_year = db.Column(db.Integer, nullable=True)
    
    """
    Term-structured courses:

    {
      "completed": [
        {"term": "Fall 2024", "courses": ["AI102", "AI202"]},
        {"term": "Spring 2025", "courses": ["CS210"]}
      ],
      "in_progress": [
        {"term": "Fall 2025", "courses": ["CS340", "MATH205"]}
      ]
    }
    """
    
    courses_by_term = db.Column(db.JSON, nullable=False, default=dict)
    unknown_courses = db.Column(db.JSON, nullable=False, default=list)
    
    # completed_course_ids = db.Column(db.JSON, nullable=False, default=list)
    # in_progress_course_ids = db.Column(db.JSON, nullable=False, default=list)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(),nullable=True)
    
    user = db.relationship("User", back_populates="student_profile", uselist=False)
    

    # --------
    # HELPERS
    # --------
    
    @staticmethod
    def _norm_course(course: str) -> str | None: 
        if not course:
            return None 
        c = course.strip().upper() 
        return c or None 
    
    @staticmethod 
    def _norm_term(term: str) -> str: 
        return (term or "").strip().title()
    
    def normalize_courses_by_term(self) -> None: 
        """
        - Uppercase course codes 
        - Remove blanks/dupes 
        - Merge duplicate terms within the same bucket
        - do NOT resolve overlaps between completed and in_progress
        """
        
        data = self.courses_by_term or {} 
        completed_rows = data.get("completed") or [] 
        inprog_rows = data.get("in_progress") or [] 
        
        def merge_rows(rows):
            merged: dict[str, set[str]] = {} 
            for row in rows:
                term = self._norm_term((row or {}).get("term"))
                courses = (row or {}).get("courses") or [] 
                bucket = merged.setdefault(term, set())
    
                for c in courses: 
                    nc = self._norm_course(c)
                    if nc: 
                        bucket.add(nc)

            return [{"term": term, "courses": sorted(list(cset))} for term, cset in merged.items()]

        completed = merge_rows(completed_rows)
        in_progress = merge_rows(inprog_rows)
        
        self.courses_by_term = {"completed": completed, "in_progress": in_progress}
    
    
    def find_course_conflicts(self) -> set[str]:
        data = self.courses_by_term or {}
        
        completed = {
            self._norm_course(c)
            for row in (data.get("completed") or [])
            for c in (row.get("courses") or [])
        }
        
        inprog = {
            self._norm_course(c)
            for row in (data.get("in_progress") or [])
            for c in (row.get("courses") or [])
        }
        
        completed.discard(None)
        inprog.discard(None)
        
        return completed & inprog 
    
    def validate_courses_by_term(self, known_courses: set[str]) -> list[str]: 
        """
        Hard Validations:
        - Term format
        - Max courses per term 
        
        SOft: 
        - Unknown courses (captured for now but not rejected)
        
        Returns: 
        list[str] of unknown courses 
        """
        
        data = self.courses_by_term or {} 
        unknown: set[str] = set()
        
        for bucket_name in ("completed","in_progress"): 
            for row in (data.get(bucket_name) or []):
                term = self._norm_term(row.get("term"))
                
                if not self.TERM_RE.match(term):
                    raise ValueError(f"Invalid term format: '{term}'")
                
                courses = row.get("courses") or []
                
                normed = [] 
                
                for c in courses: 
                    nc = self._norm_course(c)
                    if not nc: 
                        continue 
                    
                    if nc not in known_courses:
                        unknown.add(nc)
                        
                    normed.append(nc)
                
                if len(set(normed)) > self.MAX_COURSES_PER_TERM:
                    raise ValueError(
                        f"Max {self.MAX_COURSES_PER_TERM} courses allowed in {term}"
                    )
                    
        self.unknown_courses = sorted(unknown)
        return self.unknown_courses
            
        
    
    def flatten_courses(self) -> tuple[list[str], list[str]]: 
        data = self.courses_by_term or {} 
        completed = sorted({
            self._norm_course(c)
            for row in (data.get("completed") or [])
            for c in (row.get("courses") or [])
            if self._norm_course(c)
        })
        inprog = sorted({
            self._norm_course(c)
            for row in (data.get("in_progress") or [])
            for c in (row.get("courses") or [])
            if self._norm_course(c)
        })
        return completed, inprog
        
    @property
    def onboarding_complete(self) -> bool: 
        return bool(self.campus_id and self.major_id and self.expected_grad_year)
        


class CourseConflictError(ValueError):
    """Raised when a course appears in both completed and in_progress."""
    pass 

# @event.listens_for(StudentProfile, "before_insert")
# def _student_profile_before_insert(mapper, connection, target: StudentProfile): 
#     target.normalize_courses_by_term()
#     conflicts = target.find_course_conflicts() 
#     if conflicts: 
#         raise CourseConflictError(
#             f"Courses cannot be both completed and in progress: {sorted(conflicts)}"
#         )
        
# @event.listens_for(StudentProfile, "before_update")
# def _student_profile_before_update(mapper, connection, target: StudentProfile):
#     target.normalize_courses_by_term()
#     conflicts = target.find_course_conflicts()
#     if conflicts: 
#         raise CourseConflictError(
#             f"Courses cannot be both completed and in progress: {sorted(conflicts)}"
#         )
        
        
        
@event.listens_for(StudentProfile, "before_insert")
@event.listens_for(StudentProfile, "before_update")
def _student_profile_validate(mapper, connection, target: StudentProfile):
    target.normalize_courses_by_term()
    
    # hard validation 
    target.validate_courses_by_term(LIU_KNOWN_COURSES)
    
    conflicts = target.find_course_conflicts()
    
    if conflicts: 
        raise CourseConflictError(
            f"Courses cannot be both completed and in progress: {sorted(conflicts)}"
        )