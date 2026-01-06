from app.core import db 
from sqlalchemy.sql import func 


class CourseBundle(db.Model): 
    __tablename__ = "course_bundles"
    
    id = db.Column(db.String(64), primary_key=True)
    
    requirement_slot_id = db.Column(
        db.String(64), 
        db.ForeignKey("requirement_slots.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    label = db.Column(db.String(120), nullable=False)
    note = db.Column(db.String(250), nullable=True)
    must_be_same_term = db.Column(db.Boolean, nullable=False, default=False)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # slot = db.relationship("RequirementSlot", backref=db.backref("course_bundles",cascade="all, delete-orphan"), passive_deletes=True)
    slot = db.relationship(
    "RequirementSlot",
    backref=db.backref("course_bundles", cascade="all, delete-orphan"),
    passive_deletes=True
    )

    __table_args__ = (
    db.UniqueConstraint("requirement_slot_id", "label", name="uq_bundle_label_per_slot"),
    )
