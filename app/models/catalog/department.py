from app.core.extensions import db 
from sqlalchemy.sql import func 


class Department(db.Model):
    __tablename__ = "departments"
    __table_args__ = (
    db.UniqueConstraint("campus_id", "name", name="uq_department_campus_name"),
    )
    
    
    id = db.Column(db.String(64), primary_key=True)
    
    name = db.Column(db.String(250), nullable=False)
    campus_id = db.Column(
        db.String(64),
        db.ForeignKey("campuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    campus = db.relationship("Campus", back_populates="departments")
    majors = db.relationship("Major", back_populates="department")
    courses = db.relationship("Course", back_populates="department")
    
    