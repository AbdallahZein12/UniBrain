from app.core.extensions import db
from sqlalchemy.sql import func 


class Major(db.Model): 
    __tablename__ = "majors"
    __table_args__ = (
    db.UniqueConstraint("campus_id", "department_id", "name", "degree",
                      name="uq_major_campus_dept_name_degree"),
    )
    
    id = db.Column(db.String(64), primary_key=True)
    
    name = db.Column(db.String(250), nullable=False)
    degree = db.Column(db.String(120), nullable=False)
    
    department_id = db.Column(
        db.String(64), 
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True 
    )
    
    campus_id = db.Column(
        db.String(64), 
        db.ForeignKey("campuses.id",ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    total_credits_required = db.Column(db.Integer, nullable=False)
    # requirement_group_ids = 
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    students = db.relationship("StudentProfile", back_populates="major")
    department = db.relationship("Department", back_populates="majors")
    campus = db.relationship("Campus", back_populates="majors")
    
    
    
    
    