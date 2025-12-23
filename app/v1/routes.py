from flask import render_template, Response
from flask_login import login_required, current_user
from . import v1_bp
from .auth import auth_bp

v1_bp.register_blueprint(auth_bp, url_prefix="/auth")

html = """
<h1>Welcome {{ current_user.email }}</h1>

<form method="POST" action="{{ url_for('v1.auth.logout_post') }}">
  <button type="submit">Log out</button>
</form>
"""

@v1_bp.get("/home")
def home():
    return render_template("home.html")

@v1_bp.get("/onboarding")
@login_required
def onboarding():
    return Response(f"""
        <h1>Welcome {current_user.email}</h1>
        <form method="POST" action="/v1/auth/logout">
            <button type="submit">Log out</button>
        </form>
    """, mimetype="text/html")

