from flask import Blueprint, render_template


v1_bp = Blueprint("v1",
    __name__,
    template_folder="templates",
    static_folder="static"
)

@v1_bp.get("/home")
def home():
    return render_template("home.html")
