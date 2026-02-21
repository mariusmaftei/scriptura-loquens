from functools import wraps
from flask import request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature


def create_auth_token(email):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps({"email": email}, salt="auth")


def verify_auth_token(token):
    if not token:
        return None
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        data = s.loads(token, salt="auth", max_age=7 * 24 * 3600)
        return data.get("email")
    except BadSignature:
        return None


def get_token_from_request():
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        email = verify_auth_token(token) if token else None
        admin_email = current_app.config.get("ADMIN_EMAIL")
        if not admin_email or email != admin_email:
            return jsonify({"error": "Unauthorized", "message": "Login required"}), 401
        return f(*args, **kwargs)

    return decorated
