from flask import Blueprint, render_template


v1_bp = Blueprint("v1",
    __name__,
    template_folder="templates",
    static_folder="static"
)


from auth import auth_bp
v1_bp.register_blueprint(auth_bp, url_prefix="/auth")


@v1_bp.get("/home")
def home():
    return render_template("home.html")
