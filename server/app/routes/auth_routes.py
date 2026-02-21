from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    admin_email = current_app.config.get("ADMIN_EMAIL") or ""
    admin_password = current_app.config.get("ADMIN_PASSWORD") or ""

    if not admin_email or not admin_password:
        return jsonify({"error": "Auth not configured"}), 500

    if email != admin_email.lower() or password != admin_password:
        return jsonify({"error": "Invalid email or password"}), 401

    from app.auth import create_auth_token

    token = create_auth_token(email)
    return jsonify({"token": token, "email": email})
