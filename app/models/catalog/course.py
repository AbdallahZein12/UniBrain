from app.core.extensions import db
from sqlalchemy.sql import func


class Course(db.Model):
    __tablename__ = "courses"
    
    id = db.Column(db.String(64), primary_key=True)
    
    title = db.Column(db.String(250), nullable=False, index=True)
    credits = db.Column(db.Integer(), nullable=False)
    
    department_id = db.Column(
        db.String(64), 
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False, 
        index=True 
    )
    
    # campus_id = db.Column(
    #     db.String(64), 
    #     db.ForeignKey("campuses.id", ondelete="RESTRICT"),
    #     nullable=False,
    #     index=True 
    # )
    
    # terms_offered = db.Column(db.JSON, nullable=False, default=list)
    
    prereq_rules = db.Column(db.JSON, nullable=False, default=list)
    prereq_notes = db.Column(db.Text, nullable=True)
    
    
    department = db.relationship("Department", back_populates="courses")
    offerings = db.relationship(
        "CourseOffering",
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    
    # campus = db.relationship("Campus", back_populates="courses")
   
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(), nullable=True) 