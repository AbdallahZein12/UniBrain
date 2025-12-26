from app.core.extensions import db 
from sqlalchemy.sql import func 

class CourseOffering(db.Model):
    __tablename__ = "course_offerings"
    
    course_id = db.Column(
        db.String(64),
        db.ForeignKey("courses.id",ondelete="CASCADE"),
        primary_key=True
    )
    
    campus_id = db.Column(
        db.String(64), 
        db.ForeignKey("campuses.id", ondelete="RESTRICT"),
        primary_key=True
    )
    
    terms_offered = db.Column(db.JSON, nullable=False, default=list)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(),nullable=True)
    
    course = db.relationship("Course", back_populates="offerings")
    campus = db.relationship("Campus", back_populates="course_offerings")