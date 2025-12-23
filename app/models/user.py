from ..core.extensions import db

# from sqlalchemy.dialects.postgresql import UUID 
from sqlalchemy.sql import func
import uuid 

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin



class User(UserMixin ,db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255),unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # audit 
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    
    def get_id(self) -> str: 
        return self.id 
    
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password: str) -> bool: 
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self) -> str: 
        return f"<User id={self.id} email={self.email}>"