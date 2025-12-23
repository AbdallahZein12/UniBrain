from datetime import datetime, timezone
import uuid 

from sqlalchemy.sql import func  
from ..core.extensions import db 



class InviteCode(db.Model): 
    
    __table_args__ = (
    db.CheckConstraint("max_uses >= 1", name="ck_invite_max_uses_gte_1"),
    db.CheckConstraint("used_count >= 0", name="ck_invite_used_count_gte_0"),
    )
    __tablename__ = "invite_codes" 
    
    id = db.Column(db.String(36), primary_key=True, default= lambda: str(uuid.uuid4()))
    
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    max_uses = db.Column(db.Integer, nullable=False, default=1)
    used_count = db.Column(db.Integer, nullable=False, default=0)
    
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None: 
            exp = exp.replace(tzinfo=timezone.utc)
        
        if now > exp:
            return True 
        
        return False
        

    @property
    def is_exhausted(self) -> bool:
        return self.used_count >= self.max_uses

    @property
    def status(self) -> str:
        """
        One of: valid, expired, exhausted, disabled
        """
        if not self.is_active:
            return "disabled"
        if self.is_exhausted:
            return "exhausted"
        if self.is_expired:
            return "expired"
        return "valid"
    
    
    def is_valid_now(self) -> bool: 
        return self.status == "valid"
    