import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from app.config import Config
from app.database import db, init_db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('FRONTEND_URL', 'http://localhost:3000'),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    db.init_app(app)

    with app.app_context():
        for folder in ('UPLOAD_FOLDER', 'AUDIO_FOLDER'):
            path = app.config.get(folder)
            if path:
                path = os.path.abspath(path)
                os.makedirs(path, exist_ok=True)
        from app import models
        init_db()

    from app.routes import pdf_routes, chunk_routes, audio_routes
    app.register_blueprint(pdf_routes.bp, url_prefix="/api")
    app.register_blueprint(chunk_routes.bp, url_prefix="/api")
    app.register_blueprint(audio_routes.bp, url_prefix="/api")

    frontend_build = app.config.get('FRONTEND_BUILD')
    if frontend_build and os.path.isdir(frontend_build):
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path):
            if path.startswith("api/"):
                return {"error": "Not found"}, 404
            full_path = os.path.join(frontend_build, path)
            if os.path.isfile(full_path):
                return send_from_directory(frontend_build, path)
            return send_from_directory(frontend_build, "index.html")

    return app
