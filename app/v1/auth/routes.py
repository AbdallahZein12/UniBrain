from flask import Blueprint, render_template

auth_bp = Blueprint("auth",
    __name__,
    template_folder="templates",
    static_folder="static"
)



@auth_bp.get("/login")
def login():
    return render_template("login.html")

@auth_bp.get("/signup")
def signup():
    return render_template("signup.html")
