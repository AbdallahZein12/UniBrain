from app.core import db 
from sqlalchemy.sql import func 
from sqlalchemy import Enum
from app.models.enums import RequirementScope
from app.models.enums import RuleType
from app.models.catalog import Major, Campus


class RequirementGroup(db.Model):
    __tablename__ = "requirement_groups"
    
    id = db.Column(db.String(64), primary_key=True)
    
    name = db.Column(db.String(250), nullable=False)
    scope = db.Column(
        Enum(RequirementScope, name="requirement_scope"),
        nullable=False 
    )
    
    owner_id = db.Column(db.String(64), nullable=False)
    
    rule_type = db.Column(
        Enum(RuleType, name="rule_type"),
        nullable=False 
    )
    
    priority = db.Column(db.Integer, nullable=False, index=True, default=0)
    
    choose_n = db.Column(db.Integer, nullable=True)
    slots = db.relationship(
        "RequirementSlot",
        back_populates="group",
        cascade="all, delete-orphan", 
        passive_deletes=True, 
        order_by="RequirementSlot.position"
    )
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    @property 
    def owner_major(self): 
        if self.scope == RequirementScope.MAJOR: 
            return Major.query.get(self.owner_id)
        return None 
    
    @property 
    def owner_campus(self): 
        if self.scope == RequirementScope.GEN_ED:
            return Campus.query.get(self.owner_id)
        return None 
    
    @property 
    def owner(self):
        if self.scope == RequirementScope.MAJOR:
            return self.owner_major
        if self.scope == RequirementScope.GEN_ED:
            return self.owner_campus
        return None 