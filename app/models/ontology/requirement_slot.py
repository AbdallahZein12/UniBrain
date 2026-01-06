from app.core import db 
from sqlalchemy.sql import func 
from sqlalchemy import Enum
from app.models.enums import SlotType

class RequirementSlot(db.Model):
    __tablename__ = "requirement_slots"
    
    id = db.Column(db.String(64), primary_key=True)
    
    requirement_group_id = db.Column(
        db.String(64), 
        db.ForeignKey("requirement_groups.id", ondelete="CASCADE"),
        nullable=False, 
        index=True
    )
    
    label = db.Column(db.String(250), nullable=False)
    min_credits_required = db.Column(db.Integer, nullable=True)
    
    slot_type = db.Column(
        Enum(SlotType, name="slot_type"),
        nullable = False,
        default=SlotType.COURSE
    )
    
    slot_rule = db.Column(db.JSON, nullable=False, default=dict)
    # course_options = db.Column(db.JSON, default=list, nullable=False)
    # bundles = db.Column(db.JSON, default=list, nullable=False)
    
    position = db.Column(db.Integer, nullable=True)
    
    group = db.relationship(
        "RequirementGroup",
        back_populates="slots"
    )
    
    
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True, onupdate=func.now())
    