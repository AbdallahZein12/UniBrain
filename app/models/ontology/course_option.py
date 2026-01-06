from app.core import db
from sqlalchemy.sql import func 
from sqlalchemy import CheckConstraint
import uuid

class CourseOption(db.Model): 
    __tablename__ = "course_options"
    
    # id = db.Column(db.String(64), primary_key=True)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    requirement_slot_id = db.Column(
        db.String(64), 
        db.ForeignKey("requirement_slots.id", ondelete="CASCADE"),
        nullable=True,
        index=True 
    )
    
    bundle_id = db.Column(
        db.String(64), 
        db.ForeignKey("course_bundles.id", ondelete="CASCADE"),
        nullable=True, 
        index=True 
    )
    
    course_id = db.Column(
        db.String(64),
        db.ForeignKey("courses.id"),
        nullable=False 
    )
    
    note = db.Column(
        db.String(250), 
        nullable=True
    )
    
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    __table_args__ = (
        CheckConstraint(
            "(requirement_slot_id IS NOT NULL AND bundle_id IS NULL) OR "
            "(requirement_slot_id IS NULL AND bundle_id IS NOT NULL)",
            name="ck_course_option_parent_xor"
        ),
    )
    # backref automatically creates course_options in RequirementSlot
    # slot = db.relationship(
    #     "RequirementSlot",
    #     backref=db.backref("course_options", cascade="all, delete-orphan")
    # )
    
    slot = db.relationship("RequirementSlot", backref="course_options", passive_deletes=True)
    bundle = db.relationship("CourseBundle", backref="course_options", passive_deletes=True)
    
    @property 
    def parent(self): 
        return self.bundle or self.slot