from app.core.extensions import db 
from sqlalchemy.sql import func



class Campus(db.Model):
    __tablename__ = "campuses"
    
    id = db.Column(db.String(64), primary_key=True)
    
    name = db.Column(db.String(250), nullable=False)
    address = db.Column(db.String(500), nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    students = db.relationship("StudentProfile", back_populates="campus")
    departments = db.relationship("Department", back_populates="campus")
    
    