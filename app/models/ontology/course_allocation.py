from app.core.extensions import db 
from sqlalchemy.sql import func 
import uuid
from sqlalchemy import UniqueConstraint


class CourseAllocation(db.Model): 
    __tablename__ = "course_allocations"
    
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    student_profile_id = db.Column(
        db.String(36), 
        db.ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    course_id = db.Column(
        db.String(64), 
        db.ForeignKey("courses.id"),
        nullable=False,
        index=True
    )
    
    requirement_slot_id = db.Column(
        db.String(64),
        db.ForeignKey("requirement_slots.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    term = db.Column(db.String(120), nullable=False)
    
    locked = db.Column(db.Boolean, nullable=False, default=False)
    
    
    # most_constrained, advisor_override, student_selected
    reason = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        
        # a course can only be used once per student
        UniqueConstraint(
            "student_profile_id",
            "course_id",
            name="uq_allocation_student_course"
        ),
        
        # a req slot can only be fulfilled once per student
        UniqueConstraint(
            "student_profile_id",
            "requirement_slot_id",
            "course_id",
            name="uq_allocation_student_slot"
        ),
    )
    
    
    student = db.relationship("StudentProfile", backref="course_allocations")
    course = db.relationship("Course")
    requirement_slot = db.relationship("RequirementSlot")