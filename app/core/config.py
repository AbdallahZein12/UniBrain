import os 
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)


class Config: 
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"sqlite:///{INSTANCE_DIR / 'unibrain.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False 