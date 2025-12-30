from app.core import db
import uuid
from sqlalchemy.sql import func 
from sqlalchemy import event, select, inspect
import re 
from app.models.catalog import Course
from difflib import get_close_matches

# LIU_KNOWN_COURSES: set[str] = set() # TODO: replace with LIU catalog set
COURSE_SPLIT_RE = re.compile(r"^([A-Z]{2,4})\s*[-]?\s*(\d{3})([A-Z]?)$")



def default_courses_by_term():
    return {"completed": [], "in_progress": []}



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
    campus_id = db.Column(
        db.String(64),
        db.ForeignKey("campuses.id", ondelete="SET NULL"),
        # unique=False, 
        nullable=True, 
        index=True 
    )
    
    major_id = db.Column(
        db.String(64),
        db.ForeignKey("majors.id", ondelete="SET NULL"),
        # unique=False,
        nullable=True, 
        index=True 
                         
    )
    
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
    
    
    
    courses_by_term = db.Column(db.JSON, nullable=False, default=default_courses_by_term)
    unknown_courses = db.Column(db.JSON, nullable=False, default=list)
    unknown_course_suggestions = db.Column(db.JSON, nullable=True)
    
    
    # completed_course_ids = db.Column(db.JSON, nullable=False, default=list)
    # in_progress_course_ids = db.Column(db.JSON, nullable=False, default=list)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(),nullable=True)
    
    user = db.relationship("User", back_populates="student_profile", uselist=False)
    campus = db.relationship("Campus", back_populates="students")
    major = db.relationship("Major", back_populates="students")

   
    # HELPERS
   
    @staticmethod
    def _parse_course_id(code: str) -> tuple[str, int, str] | None:
        """Parse canonical code like CS 201 or ENG 110C into ('CS', 201, '') or ('ENG', 110, 'C')"""
        if not code:
            return None 
        m = COURSE_SPLIT_RE.match(code.replace(" ",""))
        if not m: 
            return None 
        dept, num, suffix = m.group(1), int(m.group(2)), m.group(3) or ""
        return dept, num, suffix
    
    @staticmethod
    def suggest_close_courses(unknown_code: str, known_courses: set[str], limit: int = 5) -> list[str]:
        u = StudentProfile._norm_course(unknown_code)
        if not u or not known_courses:
            return []
        
        parsed = StudentProfile._parse_course_id(u)
        if not parsed: 
            # fallback fuzzy across all
            return get_close_matches(u, sorted(known_courses), n=limit, cutoff=0.78)
        
        dept, num, suffix = parsed
        
        same_dept = [k for k in known_courses if k.startswith(dept + " ")]
        if not same_dept: 
            return get_close_matches(u, sorted(known_courses), n=limit, cutoff=0.78)
        
        def score(k: str) -> tuple[int,int]:
            pk = StudentProfile._parse_course_id(k)
            if not pk: 
                return (10**9, 10**9)
            _, k_num, k_suf = pk
            return (abs(k_num - num), 0 if k_suf == suffix else 1)
        
        return sorted(same_dept, key=score)[:limit]
        
    @staticmethod
    def _norm_course(course: str) -> str | None: 
        if not course:
            return None 
        
        raw = course.strip().upper()
        
        raw = re.sub(r"\s+", " ", raw)
        
        compact = raw.replace(" ", "").replace("-", "")
        
        # "CS201" -> "CS 201", "CS-201" -> "CS 201"
        m = COURSE_SPLIT_RE.match(compact)
        if m:
            return f"{m.group(1)} {m.group(2)}{m.group(3)}"
         
        return raw or None 
    
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
    
    def find_term_conflicts(self) -> set[str]: 
        data = self.courses_by_term or {}
        
        completed = {
            self._norm_term(row.get("term"))
            for row in (data.get("completed") or [])
        }
        
        inprog = {
            self._norm_term(row.get("term"))
            for row in (data.get("in_progress") or [])
        }
        
        return completed & inprog 
    
    def validate_courses_by_term(self, known_courses: set[str]) -> list[str]: 
        suggestions: dict[str, list[str]] = {}
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
                    
                    if known_courses and nc not in known_courses:
                        unknown.add(nc)
                        suggestions[nc] = StudentProfile.suggest_close_courses(nc, known_courses=known_courses, limit=5)
                        
                        
                    normed.append(nc)
                
                if len(set(normed)) > self.MAX_COURSES_PER_TERM:
                    raise ValueError(
                        f"Max {self.MAX_COURSES_PER_TERM} courses allowed in {term}"
                    )
                    
        self.unknown_courses = sorted(unknown)
        self.unknown_course_suggestions = suggestions
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
        return bool(self.full_name and self.campus_id and self.major_id)
        


class CourseConflictError(ValueError):
    """Raised when a course appears in both completed and in_progress."""
    pass 

class TermConflictError(ValueError):
    """Raised when a term appears in both completed and in_progress"""
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
    
    state = inspect(target)
    
    
    # Only run course recognition when courses_by_term changed
    if state.persistent and not state.attrs.courses_by_term.history.has_changes():
        return
    
    known_courses = {
        target._norm_course(cid)
        # cid.strip().upper()
        for cid in connection.execute(select(Course.id)).scalars().all()
        if cid
    }
    
    known_courses.discard(None)
    
    # hard validation 
    target.validate_courses_by_term(known_courses=known_courses)
    
    # hard validation
    course_conflicts = target.find_course_conflicts()
    
    # hard validation 
    term_conflicts = target.find_term_conflicts()
    
    if course_conflicts: 
        raise CourseConflictError(
            f"Courses cannot be both completed and in progress: {sorted(course_conflicts)}"
        )
    
    if term_conflicts:
        raise TermConflictError(
            f"Terms cannot be both completed and in progress: {sorted(term_conflicts)}"   
        )