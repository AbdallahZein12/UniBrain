from app.core.extensions import db
from sqlalchemy.sql import func 


class Major(db.Model): 
    __tablename__ = "majors"
    
    """
    TBD...
    """