from app.core.extensions import db 
from sqlalchemy.sql import func 
from app.models.enums import Term

class CourseOffering(db.Model):
    __tablename__ = "course_offerings"
    __table_args__ = (
    db.UniqueConstraint("course_id", "campus_id", name="uq_offering_course_campus"),
    )
    
    id = db.Column(db.String(64), primary_key=True)
    
    course_id = db.Column(
        db.String(64),
        db.ForeignKey("courses.id",ondelete="CASCADE"),
        nullable=False,
        index=True
        # primary_key=True
    )
    
    campus_id = db.Column(
        db.String(64), 
        db.ForeignKey("campuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
        # primary_key=True
    )
    
    terms_offered = db.Column(db.JSON, nullable=False, default=list)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(),nullable=True)
    
    course = db.relationship("Course", back_populates="offerings")
    campus = db.relationship("Campus", back_populates="course_offerings")
    
    @property 
    def offered_terms(self) -> set[Term]:
        return {Term(t) for t in self.terms_offered or []}
    
    def offers_term(self, term: Term) -> bool: 
        return term in self.offered_terms