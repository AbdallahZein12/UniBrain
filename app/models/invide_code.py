from datetime import datetime 
import uuid 

from sqlalchemy.sql import func  
from ..core.extensions import db 


class InviteCode(db.Model): 
    __tablename__ = "invite_codes" 
    
    id = db.Column(db.String(36), primary_key=True, default= lambda: str(uuid.uuid4()))
    
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    max_uses = db.Column(db.Integer, nullable=False, default=1)
    used_count = db.Column(db.Integer, nullable=False, default=0)
    
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    created_at = db.Column(db.Datetime(timezone=True), server_default=func.now(), nullable=False)
    
    def is_valid_now(self) -> bool: 
        if not self.is_active: 
            return False 
        if self.expires_at and datetime.utcnow() > self.expires_at.replace(tzinfo=None):
            return False 
        if self.used_count >= self.max_uses: 
            return False 
        return True 
    