from flask import jsonify
from . import health_bp


@health_bp.get("")
def health():
    return jsonify(status="ok")
